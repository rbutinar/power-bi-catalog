"""
Power BI Database Analyzer
-------------------------
Command-line tool to analyze Power BI metadata stored in SQLite database.
This tool can import JSON metadata from tenant analysis and query the resulting database.
"""
import os
import sys
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime

from database import create_schema, import_from_directory, PBIMetadataAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log(message):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def setup_database(db_path):
    """Create the database schema if it doesn't exist."""
    if not os.path.exists(db_path):
        log(f"Creating new database at {db_path}")
        create_schema(db_path)
        return True
    return False

def import_data(db_path, json_dir, tenant_id=None):
    """Import data from JSON files into the database."""
    log(f"Importing data from {json_dir} into {db_path}")
    
    # Ensure the database schema exists
    setup_database(db_path)
    
    # Import the data
    success = import_from_directory(db_path, json_dir, tenant_id)
    
    if success:
        log(f"Successfully imported Power BI metadata from {json_dir}")
    else:
        log(f"Failed to import Power BI metadata from {json_dir}")
        return False
    
    return True

def show_stats(db_path):
    """Show database statistics."""
    api = PBIMetadataAPI(db_path)
    stats = api.get_database_stats()
    
    print("\n=== Database Statistics ===")
    print(f"Workspaces: {stats['workspace_count']}")
    print(f"Datasets: {stats['dataset_count']}")
    print(f"Tables: {stats['table_count']}")
    print(f"Columns: {stats['column_count']}")
    print(f"Measures: {stats['measure_count']}")
    print(f"Relationships: {stats['relationship_count']}")
    print(f"Data Sources: {stats.get('data_source_count', 0)}")
    print(f"Last Analysis: {stats['last_analysis']}")
    print("==========================\n")

def show_largest_datasets(db_path, limit=10):
    """Show the largest datasets in the database."""
    api = PBIMetadataAPI(db_path)
    datasets = api.get_largest_datasets(limit)
    
    print(f"\n=== Top {len(datasets)} Largest Datasets ===")
    for i, ds in enumerate(datasets, 1):
        print(f"{i}. {ds['name']} ({ds['workspace_name']})")
        print(f"   Tables: {ds['table_count']}, Columns: {ds['column_count']}, Measures: {ds['measure_count']}")
        if 'total_rows' in ds and ds['total_rows']:
            print(f"   Total Rows: {ds['total_rows']:,}")
        print()
    print("==========================\n")

def show_complex_measures(db_path, limit=10):
    """Show the most complex measures in the database."""
    api = PBIMetadataAPI(db_path)
    measures = api.get_complex_measures(limit)
    
    print(f"\n=== Top {len(measures)} Most Complex Measures ===")
    for i, m in enumerate(measures, 1):
        print(f"{i}. {m['name']} ({m['dataset_name']} / {m['workspace_name']})")
        print(f"   Length: {m['expression_length']} characters")
        if len(m['expression']) > 100:
            print(f"   Expression: {m['expression'][:100]}...")
        else:
            print(f"   Expression: {m['expression']}")
        print()
    print("==========================\n")

def search_metadata(db_path, search_term, limit=10):
    """Search for metadata matching the search term."""
    api = PBIMetadataAPI(db_path)
    
    print(f"\n=== Search Results for '{search_term}' ===")
    
    # Search datasets
    datasets = api.search_datasets(search_term, limit)
    if datasets:
        print("\nDatasets:")
        for i, ds in enumerate(datasets, 1):
            print(f"{i}. {ds['name']} ({ds['workspace_name']})")
    
    # Search tables
    tables = api.search_tables(search_term, limit)
    if tables:
        print("\nTables:")
        for i, t in enumerate(tables, 1):
            print(f"{i}. {t['name']} in {t['dataset_name']} ({t['workspace_name']})")
    
    # Search columns
    columns = api.search_columns(search_term, limit)
    if columns:
        print("\nColumns:")
        for i, c in enumerate(columns, 1):
            print(f"{i}. {c['name']} ({c['data_type']}) in {c['table_name']}.{c['dataset_name']} ({c['workspace_name']})")
    
    # Search measures
    measures = api.search_measures(search_term, limit)
    if measures:
        print("\nMeasures:")
        for i, m in enumerate(measures, 1):
            print(f"{i}. {m['name']} in {m['dataset_name']} ({m['workspace_name']})")
    
    # Search data sources
    data_sources = api.search_data_sources(search_term, limit)
    if data_sources:
        print("\nData Sources:")
        for i, ds in enumerate(data_sources, 1):
            print(f"{i}. {ds.get('name', 'Unnamed Source')} in {ds['dataset_name']} ({ds['workspace_name']})")
            if ds.get('connection_string'):
                # Mask sensitive information in connection string
                conn_str = ds['connection_string']
                if 'password=' in conn_str.lower():
                    conn_str = re.sub(r'password=.*?;', 'password=***;', conn_str, flags=re.IGNORECASE)
                print(f"   Connection: {conn_str}")
    
    if not (datasets or tables or columns or measures or data_sources):
        print("No results found.")
    
    print("==========================\n")

def show_dataset_details(db_path, dataset_id):
    """Show detailed information about a dataset."""
    api = PBIMetadataAPI(db_path)
    dataset = api.get_dataset_details(dataset_id)
    
    if not dataset:
        print(f"Dataset not found: {dataset_id}")
        return
    
    print(f"\n=== Dataset: {dataset['name']} ===")
    print(f"Workspace: {dataset['workspace_name']}")
    print(f"Dedicated Capacity: {'Yes' if dataset.get('is_on_dedicated_capacity') else 'No'}")
    print(f"Tables: {len(dataset['tables'])}")
    print(f"Measures: {len(dataset['measures'])}")
    print(f"Data Sources: {len(dataset.get('data_sources', []))}")
    print(f"Relationships: {len(dataset['relationships'])}")
    
    # Show tables
    if dataset['tables']:
        print("\nTables:")
        for i, table in enumerate(dataset['tables'], 1):
            print(f"{i}. {table['name']} ({len(table['columns'])} columns, {table['row_count']:,} rows)")
    
    # Show measures (limited to 10)
    if dataset['measures']:
        print("\nMeasures (top 10):")
        for i, measure in enumerate(dataset['measures'][:10], 1):
            print(f"{i}. {measure['name']}")
            if measure.get('expression'):
                if len(measure['expression']) > 100:
                    print(f"   {measure['expression'][:100]}...")
                else:
                    print(f"   {measure['expression']}")
    
    # Show relationships (limited to 10)
    if dataset['relationships']:
        print("\nRelationships (top 10):")
        for i, rel in enumerate(dataset['relationships'][:10], 1):
            print(f"{i}. {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")
            if rel.get('cross_filtering_behavior'):
                print(f"   Cross-filtering: {rel['cross_filtering_behavior']}")
    
    # Show data sources
    if dataset.get('data_sources'):
        print("\nData Sources:")
        for i, src in enumerate(dataset['data_sources'], 1):
            print(f"{i}. {src.get('name', 'Unnamed Source')} ({src.get('type', 'Unknown Type')})")
            if src.get('connection_string'):
                # Mask sensitive information in connection string
                conn_str = src['connection_string']
                if 'password=' in conn_str.lower():
                    conn_str = re.sub(r'password=.*?;', 'password=***;', conn_str, flags=re.IGNORECASE)
                print(f"   Connection: {conn_str}")
    
    print("==========================\n")

def show_data_sources(db_path, dataset_id=None, limit=20):
    """Show data sources in the database."""
    api = PBIMetadataAPI(db_path)
    
    if dataset_id:
        data_sources = api.get_data_sources(dataset_id, limit)
        print(f"\n=== Data Sources for Dataset {dataset_id} ===")
    else:
        data_sources = api.get_data_sources(limit=limit)
        print(f"\n=== Top {len(data_sources)} Data Sources ===")
    
    if not data_sources:
        print("No data sources found.")
    else:
        for i, src in enumerate(data_sources, 1):
            print(f"{i}. {src.get('name', 'Unnamed Source')} ({src.get('type', 'Unknown Type')})")
            print(f"   Dataset: {src.get('dataset_name')} / Workspace: {src.get('workspace_name')}")
            if src.get('connection_string'):
                # Mask sensitive information in connection string
                conn_str = src['connection_string']
                if 'password=' in conn_str.lower():
                    conn_str = re.sub(r'password=.*?;', 'password=***;', conn_str, flags=re.IGNORECASE)
                print(f"   Connection: {conn_str}")
            print()
    
    print("==========================\n")

def export_dataset(db_path, dataset_id, output_path):
    """Export dataset to JSON file."""
    api = PBIMetadataAPI(db_path)
    
    if output_path:
        result = api.export_dataset_to_json(dataset_id, output_path)
        if isinstance(result, str):
            log(f"Dataset exported to {result}")
        else:
            log("Failed to export dataset")
    else:
        # Print to stdout
        result = api.export_dataset_to_json(dataset_id)
        if isinstance(result, dict):
            print(json.dumps(result, indent=2))
        else:
            log("Failed to export dataset")

def find_database():
    """Find the SQLite database file in common locations."""
    # List of common locations to check
    possible_locations = [
        # Current directory
        "pbi_metadata.db",
        # Project root directory
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbi_metadata.db"),
        # Output directories
        os.path.join("tenant_analysis_service_principal", "pbi_metadata.db"),
        os.path.join("tenant_analysis_user_auth", "pbi_metadata.db"),
        os.path.join("tenant_analysis", "pbi_metadata.db")
    ]
    
    # Check each location
    for location in possible_locations:
        if os.path.exists(location):
            log(f"Found database at {location}")
            return location
    
    # Default to project root if not found
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "pbi_metadata.db")

def main():
    """Main entry point for the command-line tool."""
    parser = argparse.ArgumentParser(description='Power BI Database Analyzer')
    
    # Database path
    parser.add_argument('--db', help='Path to SQLite database')
    
    # Command groups
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import data from JSON files')
    import_parser.add_argument('--json_dir', required=True, help='Directory containing JSON files')
    import_parser.add_argument('--tenant_id', help='Tenant ID for this analysis')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show database statistics')
    
    # Largest datasets command
    largest_parser = subparsers.add_parser('largest', help='Show largest datasets by table count')
    largest_parser.add_argument('--limit', type=int, default=10, help='Number of datasets to show')
    
    # Complex measures command
    complex_parser = subparsers.add_parser('complex', help='Show most complex measures')
    complex_parser.add_argument('--limit', type=int, default=10, help='Number of measures to show')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search metadata')
    search_parser.add_argument('--term', required=True, help='Search term')
    search_parser.add_argument('--limit', type=int, default=10, help='Number of results to show')
    
    # Dataset details command
    dataset_parser = subparsers.add_parser('dataset', help='Show dataset details')
    dataset_parser.add_argument('--id', required=True, help='Dataset ID')
    
    # Data sources command
    sources_parser = subparsers.add_parser('sources', help='Show data sources')
    sources_parser.add_argument('--dataset-id', help='Filter by dataset ID')
    sources_parser.add_argument('--limit', type=int, default=20, help='Number of sources to show')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export dataset to JSON')
    export_parser.add_argument('--id', required=True, help='Dataset ID')
    export_parser.add_argument('--output', help='Output file path')
    
    args = parser.parse_args()
    
    # Find the database if not specified
    if args.db is None:
        args.db = find_database()
    
    # Default to stats if no command is provided
    if not args.command:
        show_stats(args.db)
        return
    
    # Execute the appropriate command
    if args.command == 'import':
        import_data(args.db, args.json_dir, args.tenant_id)
    elif args.command == 'stats':
        show_stats(args.db)
    elif args.command == 'largest':
        show_largest_datasets(args.db, args.limit)
    elif args.command == 'complex':
        show_complex_measures(args.db, args.limit)
    elif args.command == 'search':
        search_metadata(args.db, args.term, args.limit)
    elif args.command == 'dataset':
        show_dataset_details(args.db, args.id)
    elif args.command == 'sources':
        show_data_sources(args.db, args.dataset_id, args.limit)
    elif args.command == 'export':
        export_dataset(args.db, args.id, args.output)

if __name__ == "__main__":
    main()
