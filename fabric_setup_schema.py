import os
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SQL_SERVER = os.getenv("SQL_SERVER_ENDPOINT")
SQL_PORT = os.getenv("SQL_SERVER_PORT", "1433")
SQL_DATABASE = os.getenv("SQL_DATABASE_NAME")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("SECRET_VALUE")
TENANT_ID = os.getenv("TENANT_ID")

# Connection string for Azure AD Service Principal authentication
conn_str = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server={SQL_SERVER},{SQL_PORT};"
    f"Database={SQL_DATABASE};"
    "Authentication=ActiveDirectoryServicePrincipal;"
    f"UID={CLIENT_ID};"
    f"PWD={CLIENT_SECRET};"
    f"Authority Id={TENANT_ID};"
    "Encrypt=yes;TrustServerCertificate=no;"
)

def create_schema_and_tables():
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        # Create schemas
        cursor.execute("IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'scan') EXEC('CREATE SCHEMA scan')")
        cursor.execute("IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo') EXEC('CREATE SCHEMA dbo')")
        # Create scan tables (raw metadata)
        cursor.execute('''
        IF OBJECT_ID('scan.datasets', 'U') IS NULL
        CREATE TABLE scan.datasets (
            id INT IDENTITY PRIMARY KEY,
            workspace_id NVARCHAR(100),
            dataset_id NVARCHAR(100),
            name NVARCHAR(255),
            created_at DATETIME,
            modified_at DATETIME
        )''')
        cursor.execute('''
        IF OBJECT_ID('scan.tables', 'U') IS NULL
        CREATE TABLE scan.tables (
            id INT IDENTITY PRIMARY KEY,
            dataset_id NVARCHAR(100),
            table_name NVARCHAR(255),
            column_count INT,
            measure_count INT
        )''')
        cursor.execute('''
        IF OBJECT_ID('scan.columns', 'U') IS NULL
        CREATE TABLE scan.columns (
            id INT IDENTITY PRIMARY KEY,
            table_id INT,
            column_name NVARCHAR(255),
            data_type NVARCHAR(100)
        )''')
        # Create enrichment tables (dbo schema, with versioning)
        cursor.execute('''
        IF OBJECT_ID('dbo.datasets', 'U') IS NULL
        CREATE TABLE dbo.datasets (
            id INT IDENTITY PRIMARY KEY,
            workspace_id NVARCHAR(100),
            dataset_id NVARCHAR(100),
            name NVARCHAR(255),
            description NVARCHAR(1000),
            owner NVARCHAR(255),
            version INT DEFAULT 1,
            valid_from DATETIME DEFAULT GETDATE(),
            valid_to DATETIME NULL,
            is_current BIT DEFAULT 1,
            modified_by NVARCHAR(255),
            modified_at DATETIME DEFAULT GETDATE()
        )''')
        cursor.execute('''
        IF OBJECT_ID('dbo.columns', 'U') IS NULL
        CREATE TABLE dbo.columns (
            id INT IDENTITY PRIMARY KEY,
            dataset_id NVARCHAR(100),
            table_name NVARCHAR(255),
            column_name NVARCHAR(255),
            data_type NVARCHAR(100),
            description NVARCHAR(1000),
            version INT DEFAULT 1,
            valid_from DATETIME DEFAULT GETDATE(),
            valid_to DATETIME NULL,
            is_current BIT DEFAULT 1,
            modified_by NVARCHAR(255),
            modified_at DATETIME DEFAULT GETDATE()
        )''')
        cursor.execute('''
        IF OBJECT_ID('dbo.measures', 'U') IS NULL
        CREATE TABLE dbo.measures (
            id INT IDENTITY PRIMARY KEY,
            dataset_id NVARCHAR(100),
            table_name NVARCHAR(255),
            measure_name NVARCHAR(255),
            expression NVARCHAR(MAX),
            description NVARCHAR(1000),
            version INT DEFAULT 1,
            valid_from DATETIME DEFAULT GETDATE(),
            valid_to DATETIME NULL,
            is_current BIT DEFAULT 1,
            modified_by NVARCHAR(255),
            modified_at DATETIME DEFAULT GETDATE()
        )''')
        conn.commit()
        print("Schemas and tables created successfully in Fabric Warehouse.")

if __name__ == "__main__":
    create_schema_and_tables()
