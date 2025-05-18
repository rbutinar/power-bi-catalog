import os
import sys
import json
from datetime import datetime

# Set PATH environment variables for DLL loading
os.environ["PATH"] += os.pathsep + os.path.abspath("lib")
adomd_dir = r"C:\Program Files\Microsoft.NET\ADOMD.NET\160"
os.environ["PATH"] += os.pathsep + adomd_dir
sys.path.append(adomd_dir)

import traceback
from dotenv import load_dotenv
from pyadomd import Pyadomd

load_dotenv()

# Configuration
WORKSPACE_NAME = os.getenv("WORKSPACE_NAME")
DATASET_NAME = os.getenv("DATASET_NAME")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("SECRET_VALUE")
TENANT_ID = os.getenv("TENANT_ID")

if not all([WORKSPACE_NAME, DATASET_NAME, CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
    raise Exception("Missing required environment variables. Check your .env file.")

# Remove quotes if present
if WORKSPACE_NAME.startswith('"') and WORKSPACE_NAME.endswith('"'):
    WORKSPACE_NAME = WORKSPACE_NAME[1:-1]
if DATASET_NAME.startswith('"') and DATASET_NAME.endswith('"'):
    DATASET_NAME = DATASET_NAME[1:-1]

print(f"Extracting metadata for dataset '{DATASET_NAME}' in workspace '{WORKSPACE_NAME}'...")

# Connection string for service principal authentication
endpoint = f"powerbi://api.powerbi.com/v1.0/myorg/{WORKSPACE_NAME}"
connection_str = (
    f"Provider=MSOLAP;Data Source={endpoint};"
    f"Initial Catalog={DATASET_NAME};"
    f"User ID=app:{CLIENT_ID}@{TENANT_ID};"
    f"Password={CLIENT_SECRET};"
    f"Integrated Security=ClaimsToken;"
)

# Initialize dataset metadata structure
dataset_metadata = {
    "dataset_name": DATASET_NAME,
    "workspace_name": WORKSPACE_NAME,
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
            print(f"Found {len(rows)} tables")
            
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
            print(f"Found {len(rows)} columns")
            
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
            print(f"Found {len(rows)} measures")
            
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
            print(f"Found {len(rows)} relationships")
            
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
                print(f"Found {len(rows)} data sources")
                
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
            print(f"Warning: Could not retrieve data sources: {str(e)}")
            dataset_metadata["data_sources"] = [{"error": "Could not retrieve data sources"}]

    # Save the metadata to a JSON file
    output_file = f"{DATASET_NAME}_metadata.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(dataset_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"Metadata successfully extracted and saved to {output_file}")
    print(f"Summary: {len(dataset_metadata['tables'])} tables, {sum(len(t['columns']) for t in dataset_metadata['tables'])} columns, {len(dataset_metadata['measures'])} measures")

except Exception as e:
    print("Error extracting metadata:")
    traceback.print_exc()
