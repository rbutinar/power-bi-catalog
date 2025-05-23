"""
Import REST API datasource information from JSON files into SQLite database.
This module extends the database schema and provides import functionality for REST API datasources.
"""
import json
import os
import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def extend_schema_for_rest_datasources(db_path):
    """
    Extend the SQLite database schema to include REST API datasources.
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # REST API Datasources table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rest_datasources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_id TEXT NOT NULL,
        workspace_id TEXT NOT NULL,
        datasource_type TEXT,
        server TEXT,
        database_name TEXT,
        connection_details TEXT,  -- JSON field for any additional connection details
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id),
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    ''')
    
    # Create index for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rest_datasources_dataset ON rest_datasources(dataset_id)')
    
    conn.commit()
    conn.close()
    
    logger.info(f"REST API datasources schema extended in {db_path}")
    return True

def import_rest_datasources(db_path, datasources_file):
    """
    Import REST API datasource information from JSON file into SQLite database.
    
    Args:
        db_path (str): Path to the SQLite database file
        datasources_file (str): Path to the datasources JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Read datasources JSON file
        with open(datasources_file, 'r', encoding='utf-8') as f:
            datasources_data = json.load(f)
        
        # Process each datasource entry
        imported_count = 0
        for entry in datasources_data:
            workspace_id = entry.get('workspace_id')
            dataset_id = entry.get('dataset_id')
            datasource = entry.get('datasource', {})
            
            # Skip error entries
            if 'error' in datasource:
                continue
                
            # Extract datasource details
            datasource_type = datasource.get('datasourceType')
            connection_details = datasource.get('connectionDetails', {})
            server = connection_details.get('server')
            database_name = connection_details.get('database')
            
            # Store any additional connection details as JSON
            other_details = json.dumps({k: v for k, v in connection_details.items() 
                                      if k not in ['server', 'database']})
            
            # Insert into database
            cursor.execute('''
                INSERT INTO rest_datasources 
                (dataset_id, workspace_id, datasource_type, server, database_name, connection_details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (dataset_id, workspace_id, datasource_type, server, database_name, other_details))
            
            imported_count += 1
        
        conn.commit()
        conn.close()
        
        logger.info(f"Imported {imported_count} REST API datasources from {datasources_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error importing REST API datasources: {str(e)}")
        return False

def update_import_from_directory(original_import_func):
    """
    Decorator to extend the original import_from_directory function with REST API datasource import.
    
    Args:
        original_import_func: The original import_from_directory function
        
    Returns:
        function: The decorated function
    """
    def wrapper(db_path, directory, tenant_id=None):
        # Call the original function
        result = original_import_func(db_path, directory, tenant_id)
        
        # Extend schema for REST API datasources
        extend_schema_for_rest_datasources(db_path)
        
        # Import REST API datasources if the file exists
        datasources_file = os.path.join(directory, "datasources_info.json")
        if os.path.exists(datasources_file):
            try:
                import_rest_datasources(db_path, datasources_file)
                logger.info(f"Imported REST API datasource information from {datasources_file}")
            except Exception as e:
                logger.error(f"Error importing REST API datasource information: {str(e)}")
        
        return result
    
    return wrapper
