"""
Query API for Power BI metadata database.
This module provides a clean API for querying the Power BI metadata database.
"""
import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class PBIMetadataAPI:
    """API for querying Power BI metadata from SQLite database."""
    
    def __init__(self, db_path: str):
        """
        Initialize the API.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        
        # Ensure the database exists
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found at {db_path}")
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dictionaries.
        
        Args:
            query (str): SQL query to execute
            params (tuple): Parameters for the query
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def get_analysis_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent analysis runs.
        
        Args:
            limit (int): Maximum number of runs to return
            
        Returns:
            List[Dict[str, Any]]: Analysis runs
        """
        query = """
        SELECT id, run_date, source_directory, tenant_id, 
               workspaces_count, datasets_count, success
        FROM analysis_runs
        ORDER BY run_date DESC
        LIMIT ?
        """
        return self._execute_query(query, (limit,))
    
    def get_workspaces(self, limit: int = 100, dedicated_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get workspaces.
        
        Args:
            limit (int): Maximum number of workspaces to return
            dedicated_only (bool): Only return workspaces on dedicated capacity
            
        Returns:
            List[Dict[str, Any]]: Workspaces
        """
        query = """
        SELECT w.id, w.name, w.type, w.is_on_dedicated_capacity,
               COUNT(DISTINCT d.id) as dataset_count
        FROM workspaces w
        LEFT JOIN datasets d ON w.id = d.workspace_id
        """
        
        if dedicated_only:
            query += " WHERE w.is_on_dedicated_capacity = 1"
            
        query += """
        GROUP BY w.id
        ORDER BY dataset_count DESC
        LIMIT ?
        """
        
        return self._execute_query(query, (limit,))
    
    def get_datasets(self, workspace_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get datasets.
        
        Args:
            workspace_id (str, optional): Filter by workspace ID
            limit (int): Maximum number of datasets to return
            
        Returns:
            List[Dict[str, Any]]: Datasets
        """
        if workspace_id:
            query = """
            SELECT d.id, d.name, d.workspace_id, w.name as workspace_name,
                   COUNT(DISTINCT t.id) as table_count,
                   COUNT(DISTINCT m.id) as measure_count
            FROM datasets d
            JOIN workspaces w ON d.workspace_id = w.id
            LEFT JOIN tables t ON d.id = t.dataset_id
            LEFT JOIN measures m ON d.id = m.dataset_id
            WHERE d.workspace_id = ?
            GROUP BY d.id
            ORDER BY table_count DESC
            LIMIT ?
            """
            return self._execute_query(query, (workspace_id, limit))
        else:
            query = """
            SELECT d.id, d.name, d.workspace_id, w.name as workspace_name,
                   COUNT(DISTINCT t.id) as table_count,
                   COUNT(DISTINCT m.id) as measure_count
            FROM datasets d
            JOIN workspaces w ON d.workspace_id = w.id
            LEFT JOIN tables t ON d.id = t.dataset_id
            LEFT JOIN measures m ON d.id = m.dataset_id
            GROUP BY d.id
            ORDER BY table_count DESC
            LIMIT ?
            """
            return self._execute_query(query, (limit,))
    
    def get_dataset_details(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a dataset.
        
        Args:
            dataset_id (str): Dataset ID
            
        Returns:
            Dict[str, Any]: Dataset details
        """
        # Get basic dataset info
        query = """
        SELECT d.id, d.name, d.workspace_id, w.name as workspace_name,
               w.is_on_dedicated_capacity
        FROM datasets d
        JOIN workspaces w ON d.workspace_id = w.id
        WHERE d.id = ?
        """
        dataset_info = self._execute_query(query, (dataset_id,))
        
        if not dataset_info:
            return {}
            
        result = dataset_info[0]
        
        # Get tables
        query = """
        SELECT id, name, row_count
        FROM tables
        WHERE dataset_id = ?
        """
        result['tables'] = self._execute_query(query, (dataset_id,))
        
        # Get measures
        query = """
        SELECT id, name, table_id, expression, is_hidden
        FROM measures
        WHERE dataset_id = ?
        """
        result['measures'] = self._execute_query(query, (dataset_id,))
        
        # Get relationships
        query = """
        SELECT id, from_table, from_column, to_table, to_column, 
               cross_filtering_behavior, is_active
        FROM relationships
        WHERE dataset_id = ?
        """
        result['relationships'] = self._execute_query(query, (dataset_id,))
        
        # Get data sources
        query = """
        SELECT id, name, connection_string, type, impersonation_mode
        FROM data_sources
        WHERE dataset_id = ?
        """
        result['data_sources'] = self._execute_query(query, (dataset_id,))
        
        # For each table, get its columns
        for table in result['tables']:
            query = """
            SELECT id, name, data_type, is_hidden, data_category, is_key
            FROM columns
            WHERE table_id = ?
            """
            table['columns'] = self._execute_query(query, (table['id'],))
        
        return result
    
    def get_largest_datasets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get datasets with the most tables/columns.
        
        Args:
            limit (int): Maximum number of datasets to return
            
        Returns:
            List[Dict[str, Any]]: Largest datasets
        """
        query = """
        SELECT d.id, d.name, w.name as workspace_name,
               COUNT(DISTINCT t.id) as table_count,
               COUNT(DISTINCT c.id) as column_count,
               COUNT(DISTINCT m.id) as measure_count,
               SUM(t.row_count) as total_rows
        FROM datasets d
        JOIN workspaces w ON d.workspace_id = w.id
        LEFT JOIN tables t ON d.id = t.dataset_id
        LEFT JOIN columns c ON t.id = c.table_id
        LEFT JOIN measures m ON d.id = m.dataset_id
        GROUP BY d.id
        ORDER BY (table_count + column_count) DESC
        LIMIT ?
        """
        return self._execute_query(query, (limit,))
    
    def get_complex_measures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most complex measures based on expression length.
        
        Args:
            limit (int): Maximum number of measures to return
            
        Returns:
            List[Dict[str, Any]]: Complex measures
        """
        query = """
        SELECT m.id, m.name, d.name as dataset_name, w.name as workspace_name,
               LENGTH(m.expression) as expression_length, m.expression
        FROM measures m
        JOIN datasets d ON m.dataset_id = d.id
        JOIN workspaces w ON d.workspace_id = w.id
        WHERE m.expression IS NOT NULL
        ORDER BY expression_length DESC
        LIMIT ?
        """
        return self._execute_query(query, (limit,))
    
    def search_datasets(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for datasets by name.
        
        Args:
            search_term (str): Search term
            limit (int): Maximum number of datasets to return
            
        Returns:
            List[Dict[str, Any]]: Matching datasets
        """
        query = """
        SELECT d.id, d.name, w.name as workspace_name
        FROM datasets d
        JOIN workspaces w ON d.workspace_id = w.id
        WHERE d.name LIKE ?
        ORDER BY d.name
        LIMIT ?
        """
        return self._execute_query(query, (f"%{search_term}%", limit))
    
    def search_tables(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for tables by name.
        
        Args:
            search_term (str): Search term
            limit (int): Maximum number of tables to return
            
        Returns:
            List[Dict[str, Any]]: Matching tables
        """
        query = """
        SELECT t.id, t.name, d.name as dataset_name, w.name as workspace_name
        FROM tables t
        JOIN datasets d ON t.dataset_id = d.id
        JOIN workspaces w ON d.workspace_id = w.id
        WHERE t.name LIKE ?
        ORDER BY t.name
        LIMIT ?
        """
        return self._execute_query(query, (f"%{search_term}%", limit))
    
    def search_columns(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for columns by name.
        
        Args:
            search_term (str): Search term
            limit (int): Maximum number of columns to return
            
        Returns:
            List[Dict[str, Any]]: Matching columns
        """
        query = """
        SELECT c.id, c.name, c.data_type, t.name as table_name, 
               d.name as dataset_name, w.name as workspace_name
        FROM columns c
        JOIN tables t ON c.table_id = t.id
        JOIN datasets d ON t.dataset_id = d.id
        JOIN workspaces w ON d.workspace_id = w.id
        WHERE c.name LIKE ?
        ORDER BY c.name
        LIMIT ?
        """
        return self._execute_query(query, (f"%{search_term}%", limit))
    
    def search_measures(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for measures by name or expression.
        
        Args:
            search_term (str): Search term
            limit (int): Maximum number of measures to return
            
        Returns:
            List[Dict[str, Any]]: Matching measures
        """
        query = """
        SELECT m.id, m.name, m.expression, d.name as dataset_name, w.name as workspace_name
        FROM measures m
        JOIN datasets d ON m.dataset_id = d.id
        JOIN workspaces w ON d.workspace_id = w.id
        WHERE m.name LIKE ? OR m.expression LIKE ?
        ORDER BY m.name
        LIMIT ?
        """
        search_pattern = f"%{search_term}%"
        return self._execute_query(query, (search_pattern, search_pattern, limit))
        
    def search_data_sources(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for data sources by name or connection string.
        
        Args:
            search_term (str): Search term
            limit (int): Maximum number of data sources to return
            
        Returns:
            List[Dict[str, Any]]: Matching data sources
        """
        query = """
        SELECT ds.id, ds.name, ds.connection_string, ds.type, 
               d.name as dataset_name, w.name as workspace_name
        FROM data_sources ds
        JOIN datasets d ON ds.dataset_id = d.id
        JOIN workspaces w ON d.workspace_id = w.id
        WHERE ds.name LIKE ? OR ds.connection_string LIKE ?
        ORDER BY ds.name
        LIMIT ?
        """
        search_pattern = f"%{search_term}%"
        return self._execute_query(query, (search_pattern, search_pattern, limit))
        
    def get_data_sources(self, dataset_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get data sources.
        
        Args:
            dataset_id (str, optional): Filter by dataset ID
            limit (int): Maximum number of data sources to return
            
        Returns:
            List[Dict[str, Any]]: Data sources
        """
        if dataset_id:
            query = """
            SELECT ds.id, ds.name, ds.connection_string, ds.type, ds.impersonation_mode,
                   d.name as dataset_name, w.name as workspace_name
            FROM data_sources ds
            JOIN datasets d ON ds.dataset_id = d.id
            JOIN workspaces w ON d.workspace_id = w.id
            WHERE ds.dataset_id = ?
            ORDER BY ds.name
            LIMIT ?
            """
            return self._execute_query(query, (dataset_id, limit))
        else:
            query = """
            SELECT ds.id, ds.name, ds.connection_string, ds.type, ds.impersonation_mode,
                   d.name as dataset_name, w.name as workspace_name
            FROM data_sources ds
            JOIN datasets d ON ds.dataset_id = d.id
            JOIN workspaces w ON d.workspace_id = w.id
            ORDER BY ds.name
            LIMIT ?
            """
            return self._execute_query(query, (limit,))
    
    def execute_custom_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a custom SQL query.
        
        Args:
            query (str): SQL query to execute
            params (tuple): Parameters for the query
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        return self._execute_query(query, params)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get overall database statistics.
        
        Returns:
            Dict[str, Any]: Database statistics
        """
        # Get counts for each entity type
        workspace_count = self._get_count("workspaces")
        dataset_count = self._get_count("datasets")
        table_count = self._get_count("tables")
        column_count = self._get_count("columns")
        measure_count = self._get_count("measures")
        relationship_count = self._get_count("relationships")
        data_source_count = self._get_count("data_sources")
        
        # Get last analysis run
        query = """
        SELECT run_date FROM analysis_runs 
        ORDER BY run_date DESC LIMIT 1
        """
        result = self._execute_query(query)
        last_analysis = result[0]['run_date'] if result else None
        
        return {
            "workspace_count": workspace_count,
            "dataset_count": dataset_count,
            "table_count": table_count,
            "column_count": column_count,
            "measure_count": measure_count,
            "relationship_count": relationship_count,
            "data_source_count": data_source_count,
            "last_analysis": last_analysis
        }
    
    def _get_count(self, table_name: str) -> int:
        """
        Get the count of rows in a table.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            int: Row count
        """
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self._execute_query(query)
        return result[0]['count'] if result else 0
    
    def export_dataset_to_json(self, dataset_id: str, output_path: Optional[str] = None) -> Union[Dict[str, Any], str]:
        """
        Export a dataset's metadata to JSON.
        
        Args:
            dataset_id (str): Dataset ID
            output_path (str, optional): Path to save the JSON file
            
        Returns:
            Union[Dict[str, Any], str]: Dataset metadata as dict or path to saved file
        """
        dataset = self.get_dataset_details(dataset_id)
        
        if not dataset:
            return {}
            
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2)
            return output_path
        else:
            return dataset

if __name__ == "__main__":
    # For testing/direct execution
    import argparse
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='Query Power BI metadata from SQLite database')
    parser.add_argument('--db_path', default='pbi_metadata.db', help='Path to SQLite database')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--largest', type=int, help='Show N largest datasets')
    parser.add_argument('--complex_measures', type=int, help='Show N most complex measures')
    parser.add_argument('--dataset', help='Show details for a specific dataset ID')
    parser.add_argument('--search', help='Search term for datasets, tables, columns, and measures')
    
    args = parser.parse_args()
    
    api = PBIMetadataAPI(args.db_path)
    
    if args.stats:
        stats = api.get_database_stats()
        print("\nDatabase Statistics:")
        print(f"Workspaces: {stats['workspace_count']}")
        print(f"Datasets: {stats['dataset_count']}")
        print(f"Tables: {stats['table_count']}")
        print(f"Columns: {stats['column_count']}")
        print(f"Measures: {stats['measure_count']}")
        print(f"Relationships: {stats['relationship_count']}")
        print(f"Data Sources: {stats['data_source_count']}")
        print(f"Last Analysis: {stats['last_analysis']}")
    
    if args.largest:
        datasets = api.get_largest_datasets(args.largest)
        print(f"\nTop {len(datasets)} Largest Datasets:")
        for ds in datasets:
            print(f"{ds['name']} ({ds['workspace_name']}): {ds['table_count']} tables, {ds['column_count']} columns, {ds['measure_count']} measures")
    
    if args.complex_measures:
        measures = api.get_complex_measures(args.complex_measures)
        print(f"\nTop {len(measures)} Most Complex Measures:")
        for m in measures:
            print(f"{m['name']} ({m['dataset_name']}): {m['expression_length']} chars")
    
    if args.dataset:
        dataset = api.get_dataset_details(args.dataset)
        if dataset:
            print(f"\nDataset: {dataset['name']} ({dataset['workspace_name']})")
            print(f"Tables: {len(dataset['tables'])}")
            print(f"Measures: {len(dataset['measures'])}")
            print(f"Relationships: {len(dataset['relationships'])}")
        else:
            print(f"Dataset not found: {args.dataset}")
    
    if args.search:
        print(f"\nSearch results for '{args.search}':")
        
        datasets = api.search_datasets(args.search)
        if datasets:
            print("\nDatasets:")
            for ds in datasets:
                print(f"- {ds['name']} ({ds['workspace_name']})")
        
        tables = api.search_tables(args.search)
        if tables:
            print("\nTables:")
            for t in tables:
                print(f"- {t['name']} in {t['dataset_name']} ({t['workspace_name']})")
        
        columns = api.search_columns(args.search)
        if columns:
            print("\nColumns:")
            for c in columns:
                print(f"- {c['name']} ({c['data_type']}) in {c['table_name']}.{c['dataset_name']} ({c['workspace_name']})")
        
        measures = api.search_measures(args.search)
        if measures:
            print("\nMeasures:")
            for m in measures:
                print(f"- {m['name']} in {m['dataset_name']} ({m['workspace_name']})")
