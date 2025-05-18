"""
Power BI Tenant Analyzer
------------------------
This script scans a Power BI tenant using service principal authentication to:
1. List all workspaces (admin/groups endpoint)
2. List all datasets in each workspace
3. Extract detailed metadata for each dataset using XMLA/pyadomd

Authentication is done entirely with service principal (app registration).
"""
import os
import sys
import json
import time
import requests
import argparse
import traceback
from datetime import datetime
from pathlib import Path

# Set PATH environment variables for DLL loading (must be before pyadomd import)
os.environ["PATH"] += os.pathsep + os.path.abspath("lib")
adomd_dir = r"C:\Program Files\Microsoft.NET\ADOMD.NET\160"
os.environ["PATH"] += os.pathsep + adomd_dir
sys.path.append(adomd_dir)

from dotenv import load_dotenv
from pyadomd import Pyadomd

# Import database module (optional, only used if --db flag is provided)
try:
    from database import create_schema, import_from_directory
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configuration
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["SECRET_VALUE"]
TENANT_ID = os.environ["TENANT_ID"]
OUTPUT_DIR = "tenant_analysis_service_principal"

# Create output directory if it doesn't exist
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Logging setup
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_access_token():
    """Get an access token using client credentials flow"""
    log("Authenticating using service principal...")
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }
    
    r = requests.post(token_url, data=token_data)
    r.raise_for_status()
    token = r.json()["access_token"]
    log(f"Access token obtained (truncated): {token[:8]}...{token[-8:]}")
    return token

def get_workspaces(token):
    """Get all workspaces using the admin/groups endpoint"""
    log("Fetching all workspaces...")
    api_url = "https://api.powerbi.com/v1.0/myorg/admin/groups?$top=5000"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(api_url, headers=headers)
        resp.raise_for_status()
        workspaces = resp.json().get("value", [])
        log(f"Found {len(workspaces)} workspaces")
        return workspaces
    except Exception as e:
        log(f"Error fetching workspaces: {str(e)}")
        return []

def get_datasets_in_workspace(token, workspace_id):
    """Get all datasets in a workspace"""
    api_url = f"https://api.powerbi.com/v1.0/myorg/admin/groups/{workspace_id}/datasets"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        resp = requests.get(api_url, headers=headers)
        resp.raise_for_status()
        datasets = resp.json().get("value", [])
        return datasets
    except Exception as e:
        log(f"Error fetching datasets for workspace {workspace_id}: {str(e)}")
        return []

def extract_dataset_metadata(workspace_name, dataset_name):
    """Extract detailed metadata for a dataset using XMLA/pyadomd"""
    log(f"Extracting metadata for dataset '{dataset_name}' in workspace '{workspace_name}'...")
    
    # Connection string for service principal authentication
    endpoint = f"powerbi://api.powerbi.com/v1.0/myorg/{workspace_name}"
    connection_str = (
        f"Provider=MSOLAP;Data Source={endpoint};"
        f"Initial Catalog={dataset_name};"
        f"User ID=app:{CLIENT_ID}@{TENANT_ID};"
        f"Password={CLIENT_SECRET};"
        f"Integrated Security=ClaimsToken;"
    )
    
    # Initialize dataset metadata structure
    dataset_metadata = {
        "dataset_name": dataset_name,
        "workspace_name": workspace_name,
        "extraction_date": datetime.now().isoformat(),
        "tables": [],
        "measures": [],
        "relationships": [],
        "data_sources": []
    }
    
    try:
        with Pyadomd(connection_str) as conn:
            # Get tables
            with conn.cursor().execute("SELECT * FROM $SYSTEM.TMSCHEMA_TABLES") as cur:
                columns = [col[0] for col in cur.description]
                rows = cur.fetchall()
                
                for row in rows:
                    table_data = dict(zip(columns, row))
                    dataset_metadata["tables"].append({
                        "id": table_data.get("ID"),
                        "name": table_data.get("Name"),
                        "description": table_data.get("Description"),
                        "is_hidden": table_data.get("IsHidden"),
                        "data_category": table_data.get("DataCategory"),
                        "columns": []  # Will be populated later
                    })
    
            # Get columns for each table
            with conn.cursor().execute("SELECT * FROM $SYSTEM.TMSCHEMA_COLUMNS") as cur:
                columns = [col[0] for col in cur.description]
                rows = cur.fetchall()
                
                # Create a mapping of table IDs to their position in the tables array
                table_id_to_index = {table["id"]: i for i, table in enumerate(dataset_metadata["tables"])}
                
                for row in rows:
                    column_data = dict(zip(columns, row))
                    table_id = column_data.get("TableID")
                    
                    if table_id in table_id_to_index:
                        dataset_metadata["tables"][table_id_to_index[table_id]]["columns"].append({
                            "id": column_data.get("ID"),
                            "name": column_data.get("Name"),
                            "description": column_data.get("Description"),
                            "data_type": column_data.get("DataType"),
                            "is_hidden": column_data.get("IsHidden"),
                            "data_category": column_data.get("DataCategory"),
                            "sort_by_column_id": column_data.get("SortByColumnID"),
                            "is_key": column_data.get("IsKey")
                        })
    
            # Get measures
            with conn.cursor().execute("SELECT * FROM $SYSTEM.TMSCHEMA_MEASURES") as cur:
                columns = [col[0] for col in cur.description]
                rows = cur.fetchall()
                
                for row in rows:
                    measure_data = dict(zip(columns, row))
                    dataset_metadata["measures"].append({
                        "id": measure_data.get("ID"),
                        "name": measure_data.get("Name"),
                        "description": measure_data.get("Description"),
                        "expression": measure_data.get("Expression"),
                        "table_id": measure_data.get("TableID"),
                        "display_folder": measure_data.get("DisplayFolder"),
                        "format_string": measure_data.get("FormatString"),
                        "is_hidden": measure_data.get("IsHidden")
                    })
    
            # Get relationships
            with conn.cursor().execute("SELECT * FROM $SYSTEM.TMSCHEMA_RELATIONSHIPS") as cur:
                columns = [col[0] for col in cur.description]
                rows = cur.fetchall()
                
                for row in rows:
                    relationship_data = dict(zip(columns, row))
                    dataset_metadata["relationships"].append({
                        "id": relationship_data.get("ID"),
                        "from_table_id": relationship_data.get("FromTableID"),
                        "from_column_id": relationship_data.get("FromColumnID"),
                        "to_table_id": relationship_data.get("ToTableID"),
                        "to_column_id": relationship_data.get("ToColumnID"),
                        "is_active": relationship_data.get("IsActive"),
                        "cross_filtering_behavior": relationship_data.get("CrossFilteringBehavior"),
                        "cardinality": relationship_data.get("Cardinality")
                    })
    
            # Get data sources
            try:
                with conn.cursor().execute("SELECT * FROM $SYSTEM.TMSCHEMA_DATA_SOURCES") as cur:
                    columns = [col[0] for col in cur.description]
                    rows = cur.fetchall()
                    
                    for row in rows:
                        source_data = dict(zip(columns, row))
                        dataset_metadata["data_sources"].append({
                            "id": source_data.get("ID"),
                            "name": source_data.get("Name"),
                            "connection_string": source_data.get("ConnectionString"),
                            "type": source_data.get("Type"),
                            "impersonation_mode": source_data.get("ImpersonationMode")
                        })
            except Exception as e:
                log(f"Warning: Could not retrieve data sources: {str(e)}")
                dataset_metadata["data_sources"] = [{"error": "Could not retrieve data sources"}]
    
        log(f"Metadata extracted: {len(dataset_metadata['tables'])} tables, {sum(len(t['columns']) for t in dataset_metadata['tables'])} columns, {len(dataset_metadata['measures'])} measures")
        return dataset_metadata
        
    except Exception as e:
        log(f"Error extracting metadata for dataset '{dataset_name}': {str(e)}")
        return {
            "dataset_name": dataset_name,
            "workspace_name": workspace_name,
            "error": str(e),
            "error_details": traceback.format_exc()
        }

def analyze_tenant(use_sqlite=False, db_path=None, workspace_filter=None, workspace_id_filter=None, dataset_filter=None, dataset_id_filter=None):
    """Main function to analyze the entire tenant"""
    start_time = time.time()
    log("Starting Power BI tenant analysis...")
    
    # Get access token
    token = get_access_token()
    
    # Get all workspaces
    workspaces = get_workspaces(token)
    
    # Initialize tenant summary
    tenant_summary = {
        "analysis_date": datetime.now().isoformat(),
        "tenant_id": TENANT_ID,
        "workspaces_count": len(workspaces),
        "workspaces": []
    }
    
    # Process each workspace
    for workspace in workspaces:
        workspace_id = workspace.get("id")
        workspace_name = workspace.get("name")
        workspace_type = workspace.get("type")
        is_on_dedicated_capacity = workspace.get("isOnDedicatedCapacity", False)
        
        # Apply workspace filters if specified
        if workspace_filter and workspace_filter.lower() not in workspace_name.lower():
            log(f"Skipping workspace (name filter): {workspace_name}")
            continue
            
        if workspace_id_filter and workspace_id_filter != workspace_id:
            log(f"Skipping workspace (ID filter): {workspace_name}")
            continue
        # Already extracted these values above for filtering
        
        log(f"Processing workspace: {workspace_name} (ID: {workspace_id}, Type: {workspace_type})")
        
        # Skip personal workspaces if needed (they often don't support XMLA)
        if workspace_type == "PersonalGroup" and not is_on_dedicated_capacity:
            log(f"Skipping personal workspace not on dedicated capacity: {workspace_name}")
            continue
        
        # Get datasets in the workspace
        datasets = get_datasets_in_workspace(token, workspace_id)
        log(f"Found {len(datasets)} datasets in workspace {workspace_name}")
        
        workspace_summary = {
            "id": workspace_id,
            "name": workspace_name,
            "type": workspace_type,
            "is_on_dedicated_capacity": is_on_dedicated_capacity,
            "datasets_count": len(datasets),
            "datasets": []
        }
        
        # Process each dataset
        for dataset in datasets:
            dataset_id = dataset.get("id")
            dataset_name = dataset.get("name")
            
            # Apply dataset filters if specified
            if dataset_filter and dataset_filter.lower() not in dataset_name.lower():
                log(f"Skipping dataset (name filter): {dataset_name}")
                continue
                
            if dataset_id_filter and dataset_id_filter != dataset_id:
                log(f"Skipping dataset (ID filter): {dataset_name}")
                continue
                
            log(f"Processing dataset: {dataset_name} (ID: {dataset_id})")
            
            # Extract metadata if the dataset is on a dedicated capacity
            dataset_info = {
                "id": dataset_id,
                "name": dataset_name,
                "configured_by": dataset.get("configuredBy")
            }
            
            if is_on_dedicated_capacity:
                try:
                    # Extract detailed metadata
                    metadata = extract_dataset_metadata(workspace_name, dataset_name)
                    
                    # Save dataset metadata to file
                    safe_name = f"{workspace_name}_{dataset_name}".replace(" ", "_").replace("/", "_")
                    dataset_file = os.path.join(OUTPUT_DIR, f"{safe_name}_metadata.json")
                    with open(dataset_file, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    
                    # Add summary to dataset info
                    dataset_info["metadata_extracted"] = True
                    dataset_info["tables_count"] = len(metadata.get("tables", []))
                    dataset_info["measures_count"] = len(metadata.get("measures", []))
                    dataset_info["metadata_file"] = dataset_file
                except Exception as e:
                    log(f"Error processing dataset {dataset_name}: {str(e)}")
                    dataset_info["metadata_extracted"] = False
                    dataset_info["error"] = str(e)
            else:
                dataset_info["metadata_extracted"] = False
                dataset_info["reason"] = "Workspace not on dedicated capacity"
            
            workspace_summary["datasets"].append(dataset_info)
        
        tenant_summary["workspaces"].append(workspace_summary)
    
    # Save tenant summary
    summary_file = os.path.join(OUTPUT_DIR, "tenant_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(tenant_summary, f, indent=2, ensure_ascii=False)
    
    # Calculate statistics
    total_datasets = sum(len(w.get("datasets", [])) for w in tenant_summary["workspaces"])
    datasets_with_metadata = sum(
        sum(1 for d in w.get("datasets", []) if d.get("metadata_extracted", False))
        for w in tenant_summary["workspaces"]
    )
    
    elapsed_time = time.time() - start_time
    log(f"Analysis complete in {elapsed_time:.2f} seconds")
    log(f"Summary: {len(workspaces)} workspaces, {total_datasets} datasets, {datasets_with_metadata} datasets with extracted metadata")
    log(f"Results saved to {OUTPUT_DIR}")
    
    # Save to SQLite database if requested
    if use_sqlite and DATABASE_AVAILABLE:
        if db_path is None:
            # Store database in project root by default
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbi_metadata.db")
        
        log(f"Saving metadata to SQLite database: {db_path}")
        try:
            # Create schema if needed
            create_schema(db_path)
            
            # Import JSON data
            import_success = import_from_directory(db_path, OUTPUT_DIR, tenant_id=TENANT_ID)
            
            if import_success:
                log("Successfully imported metadata to SQLite database")
            else:
                log("Failed to import metadata to SQLite database")
        except Exception as e:
            log(f"Error saving to SQLite database: {str(e)}")
    elif use_sqlite and not DATABASE_AVAILABLE:
        log("SQLite database integration requested but database module not available")
        log("Please ensure the database module is installed")
    
    return tenant_summary

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Power BI Tenant Analyzer')
    parser.add_argument('--sqlite', action='store_true', help='Save results to SQLite database')
    parser.add_argument('--db-path', help='Path to SQLite database file')
    parser.add_argument('--workspace', help='Filter analysis to workspaces containing this name (case-insensitive)')
    parser.add_argument('--workspace-id', help='Filter analysis to a specific workspace ID')
    parser.add_argument('--dataset', help='Filter analysis to datasets containing this name (case-insensitive)')
    parser.add_argument('--dataset-id', help='Filter analysis to a specific dataset ID')
    args = parser.parse_args()
    
    # Run the analysis
    analyze_tenant(
        use_sqlite=args.sqlite, 
        db_path=args.db_path,
        workspace_filter=args.workspace,
        workspace_id_filter=args.workspace_id,
        dataset_filter=args.dataset,
        dataset_id_filter=args.dataset_id
    )
