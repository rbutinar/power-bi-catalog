"""
Database module for Power BI Semantic Analyzer.
Provides functionality for storing and querying Power BI metadata.
"""
from .schema import create_schema
from .json_importer import import_from_directory
from .query_api import PBIMetadataAPI
from .rest_datasources import extend_schema_for_rest_datasources, import_rest_datasources

# Apply the REST API datasources extension to the import_from_directory function
from .rest_datasources import update_import_from_directory
import_from_directory = update_import_from_directory(import_from_directory)

__all__ = ['create_schema', 'import_from_directory', 'PBIMetadataAPI', 
           'extend_schema_for_rest_datasources', 'import_rest_datasources']
