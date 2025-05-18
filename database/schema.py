"""
SQLite schema definition for Power BI metadata database.
This module creates the necessary tables to store Power BI metadata.
"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def create_schema(db_path):
    """
    Create the SQLite database schema for Power BI metadata.
    
    Args:
        db_path (str): Path to the SQLite database file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Workspaces table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS workspaces (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        is_on_dedicated_capacity BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Datasets table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS datasets (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        workspace_id TEXT NOT NULL,
        created_date TEXT,
        modified_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
    )
    ''')
    
    # Tables table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tables (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dataset_id TEXT NOT NULL,
        row_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
    )
    ''')
    
    # Columns table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS columns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        table_id TEXT NOT NULL,
        data_type TEXT,
        description TEXT,
        is_hidden BOOLEAN DEFAULT 0,
        data_category TEXT,
        sort_by_column_id TEXT,
        is_key BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (table_id) REFERENCES tables(id)
    )
    ''')
    
    # Measures table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS measures (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dataset_id TEXT NOT NULL,
        table_id TEXT,
        expression TEXT,
        description TEXT,
        is_hidden BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id),
        FOREIGN KEY (table_id) REFERENCES tables(id)
    )
    ''')
    
    # Relationships table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS relationships (
        id TEXT PRIMARY KEY,
        dataset_id TEXT NOT NULL,
        from_table TEXT NOT NULL,
        from_column TEXT NOT NULL,
        to_table TEXT NOT NULL,
        to_column TEXT NOT NULL,
        cross_filtering_behavior TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
    )
    ''')
    
    # Analysis runs table to track when analyses were performed
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analysis_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source_directory TEXT NOT NULL,
        tenant_id TEXT,
        workspaces_count INTEGER DEFAULT 0,
        datasets_count INTEGER DEFAULT 0,
        tables_count INTEGER DEFAULT 0,
        columns_count INTEGER DEFAULT 0,
        measures_count INTEGER DEFAULT 0,
        relationships_count INTEGER DEFAULT 0,
        success BOOLEAN DEFAULT 1,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_datasets_workspace ON datasets(workspace_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tables_dataset ON tables(dataset_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_columns_table ON columns(table_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_measures_dataset ON measures(dataset_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationships_dataset ON relationships(dataset_id)')
    
    conn.commit()
    conn.close()
    
    logger.info(f"Database schema created at {db_path}")
    return True

if __name__ == "__main__":
    # For testing/direct execution
    import argparse
    
    parser = argparse.ArgumentParser(description='Create SQLite schema for Power BI metadata')
    parser.add_argument('--db_path', default='pbi_metadata.db', help='Path to SQLite database')
    
    args = parser.parse_args()
    create_schema(args.db_path)
    print(f"Schema created successfully at {args.db_path}")
