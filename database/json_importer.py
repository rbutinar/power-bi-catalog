"""
Import Power BI metadata from JSON files into SQLite database.
This module converts the JSON output from pbi_tenant_analyzer.py into a structured SQLite database.
"""
import json
import os
import sqlite3
import uuid
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class JsonToSqliteImporter:
    """Class to import Power BI metadata from JSON files into SQLite database."""
    
    def __init__(self, db_path):
        """
        Initialize the importer.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def __enter__(self):
        """Context manager entry point."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        if self.conn:
            self.conn.commit()
            self.conn.close()
    
    def import_tenant_analysis(self, json_dir, tenant_id=None):
        """
        Import tenant analysis data from JSON files.
        
        Args:
            json_dir (str): Directory containing JSON files
            tenant_id (str, optional): Tenant ID for this analysis
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Record this analysis run
            self.cursor.execute(
                "INSERT INTO analysis_runs (source_directory, tenant_id) VALUES (?, ?)",
                (json_dir, tenant_id)
            )
            run_id = self.cursor.lastrowid
            
            # Load tenant summary file
            tenant_summary_path = os.path.join(json_dir, 'tenant_summary.json')
            if not os.path.exists(tenant_summary_path):
                logger.error(f"Tenant summary file not found: {tenant_summary_path}")
                return False
                
            with open(tenant_summary_path, 'r', encoding='utf-8') as f:
                tenant_data = json.load(f)
            
            # Check if tenant_data is a dictionary with 'workspaces' key (new format)
            # or a list of workspaces (old format)
            if isinstance(tenant_data, dict) and 'workspaces' in tenant_data:
                workspaces = tenant_data.get('workspaces', [])
            else:
                # Assume it's a list of workspaces
                workspaces = tenant_data if isinstance(tenant_data, list) else []
            
            # Process workspaces
            workspaces_count = 0
            datasets_count = 0
            
            for workspace in workspaces:
                # Insert workspace
                self.cursor.execute(
                    "INSERT OR REPLACE INTO workspaces (id, name, type, is_on_dedicated_capacity) VALUES (?, ?, ?, ?)",
                    (
                        workspace['id'], 
                        workspace['name'], 
                        workspace.get('type', 'Unknown'),
                        1 if workspace.get('is_on_dedicated_capacity', False) else 0
                    )
                )
                workspaces_count += 1
                
                # Process datasets in workspace
                for dataset in workspace.get('datasets', []):
                    # Insert dataset
                    self.cursor.execute(
                        "INSERT OR REPLACE INTO datasets (id, name, workspace_id) VALUES (?, ?, ?)",
                        (dataset['id'], dataset['name'], workspace['id'])
                    )
                    datasets_count += 1
                    
                    # Look for detailed metadata file for this dataset
                    metadata_file = f"{workspace['name'].replace(' ', '_')}_{dataset['name'].replace(' ', '_')}_metadata.json"
                    metadata_path = os.path.join(json_dir, metadata_file)
                    
                    if os.path.exists(metadata_path):
                        self._process_dataset_metadata(metadata_path, dataset['id'])
            
            # Get counts for tables, columns, measures, and relationships
            self.cursor.execute("SELECT COUNT(*) FROM tables")
            tables_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM columns")
            columns_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM measures")
            measures_count = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM relationships")
            relationships_count = self.cursor.fetchone()[0]
            
            # Update the analysis run with all counts
            self.cursor.execute(
                """UPDATE analysis_runs SET 
                   workspaces_count = ?, 
                   datasets_count = ?,
                   tables_count = ?,
                   columns_count = ?,
                   measures_count = ?,
                   relationships_count = ?,
                   timestamp = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (workspaces_count, datasets_count, tables_count, columns_count, 
                 measures_count, relationships_count, run_id)
            )
            
            logger.info(f"Imported {workspaces_count} workspaces and {datasets_count} datasets from {json_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing tenant analysis: {str(e)}")
            # Mark the run as failed
            if run_id:
                self.cursor.execute(
                    "UPDATE analysis_runs SET success = 0 WHERE id = ?",
                    (run_id,)
                )
            return False
    
    def _process_dataset_metadata(self, metadata_path, dataset_id):
        """
        Process detailed metadata for a dataset.
        
        Args:
            metadata_path (str): Path to the metadata JSON file
            dataset_id (str): Dataset ID
        """
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
            # Skip if there was an error extracting metadata
            if 'error' in metadata:
                logger.warning(f"Skipping dataset {dataset_id} due to extraction error")
                return
                
            # Process tables
            for table in metadata.get('tables', []):
                table_id = str(table.get('id', uuid.uuid4()))
                
                # Insert table
                self.cursor.execute(
                    "INSERT OR REPLACE INTO tables (id, name, dataset_id, row_count) VALUES (?, ?, ?, ?)",
                    (
                        table_id,
                        table.get('name') or 'Unknown',  # Handle None values
                        dataset_id,
                        table.get('row_count', 0)
                    )
                )
                
                # Process columns
                for column in table.get('columns', []):
                    column_id = str(column.get('id', uuid.uuid4()))
                    
                    # Insert column
                    self.cursor.execute(
                        """
                        INSERT OR REPLACE INTO columns 
                        (id, name, table_id, data_type, description, is_hidden, data_category, sort_by_column_id, is_key) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            column_id,
                            column.get('name') or 'Unknown',  # Handle None values
                            table_id,
                            column.get('data_type'),
                            column.get('description'),
                            1 if column.get('is_hidden', False) else 0,
                            column.get('data_category'),
                            column.get('sort_by_column_id'),
                            1 if column.get('is_key', False) else 0
                        )
                    )
            
            # Process measures
            for measure in metadata.get('measures', []):
                measure_id = str(measure.get('id', uuid.uuid4()))
                
                # Find table_id if available
                table_id = measure.get('table_id')  # Direct table_id reference
                
                # If table_id is not directly available, try with table_name
                if table_id is None and 'table_name' in measure:
                    self.cursor.execute(
                        "SELECT id FROM tables WHERE name = ? AND dataset_id = ?",
                        (measure['table_name'], dataset_id)
                    )
                    result = self.cursor.fetchone()
                    if result:
                        table_id = result[0]
                
                # Insert measure
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO measures 
                    (id, name, dataset_id, table_id, expression, description, is_hidden) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        measure_id,
                        measure.get('name') or 'Unknown',  # Handle None values
                        dataset_id,
                        table_id,
                        measure.get('expression'),
                        measure.get('description'),
                        1 if measure.get('is_hidden', False) else 0
                    )
                )
            
            # Process relationships
            for relationship in metadata.get('relationships', []):
                relationship_id = str(relationship.get('id', uuid.uuid4()))
                
                # Handle different relationship formats
                from_table = relationship.get('from_table')
                from_column = relationship.get('from_column')
                to_table = relationship.get('to_table')
                to_column = relationship.get('to_column')
                
                # If using table_id and column_id format instead
                if from_table is None and 'from_table_id' in relationship:
                    from_table = relationship.get('from_table_id')
                if from_column is None and 'from_column_id' in relationship:
                    from_column = relationship.get('from_column_id')
                if to_table is None and 'to_table_id' in relationship:
                    to_table = relationship.get('to_table_id')
                if to_column is None and 'to_column_id' in relationship:
                    to_column = relationship.get('to_column_id')
                
                # Insert relationship
                self.cursor.execute(
                    """
                    INSERT OR REPLACE INTO relationships 
                    (id, dataset_id, from_table, from_column, to_table, to_column, cross_filtering_behavior, is_active) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        relationship_id,
                        dataset_id,
                        str(from_table) if from_table is not None else 'Unknown',
                        str(from_column) if from_column is not None else 'Unknown',
                        str(to_table) if to_table is not None else 'Unknown',
                        str(to_column) if to_column is not None else 'Unknown',
                        relationship.get('cross_filtering_behavior'),
                        1 if relationship.get('is_active', True) else 0
                    )
                )
                
        except Exception as e:
            logger.error(f"Error processing dataset metadata {metadata_path}: {str(e)}")

def import_from_directory(db_path, json_dir, tenant_id=None):
    """
    Import Power BI metadata from a directory of JSON files.
    
    Args:
        db_path (str): Path to the SQLite database file
        json_dir (str): Directory containing JSON files
        tenant_id (str, optional): Tenant ID for this analysis
        
    Returns:
        bool: True if successful, False otherwise
    """
    with JsonToSqliteImporter(db_path) as importer:
        return importer.import_tenant_analysis(json_dir, tenant_id)

if __name__ == "__main__":
    # For testing/direct execution
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Import Power BI metadata from JSON to SQLite')
    parser.add_argument('--db_path', default='pbi_metadata.db', help='Path to SQLite database')
    parser.add_argument('--json_dir', required=True, help='Directory containing JSON files')
    parser.add_argument('--tenant_id', help='Tenant ID for this analysis')
    
    args = parser.parse_args()
    
    # Ensure the database schema exists
    from schema import create_schema
    create_schema(args.db_path)
    
    # Import the data
    success = import_from_directory(args.db_path, args.json_dir, args.tenant_id)
    
    if success:
        print(f"Successfully imported Power BI metadata from {args.json_dir} to {args.db_path}")
    else:
        print(f"Failed to import Power BI metadata from {args.json_dir}")
        exit(1)
