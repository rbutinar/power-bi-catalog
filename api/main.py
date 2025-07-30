"""
FastAPI backend for Power BI Catalog
"""
import os
import sqlite3
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Power BI Catalog API",
    description="A data catalog and internal marketplace for Power BI and data assets",
    version="1.0.0"
)

# Add CORS middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TenantConfig(BaseModel):
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None

class TenantConfigResponse(BaseModel):
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    has_client_secret: bool = False
    is_configured: bool = False

# Data models for Power BI entities
class Workspace(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    is_on_dedicated_capacity: Optional[bool] = None
    datasets_count: Optional[int] = 0

class Dataset(BaseModel):
    id: str
    name: str
    workspace_id: str
    workspace_name: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None
    tables_count: Optional[int] = 0
    measures_count: Optional[int] = 0

class Table(BaseModel):
    id: str
    name: str
    dataset_id: str
    dataset_name: Optional[str] = None
    row_count: Optional[int] = None
    columns_count: Optional[int] = 0

class Column(BaseModel):
    id: str
    name: str
    table_id: str
    table_name: Optional[str] = None
    data_type: Optional[str] = None
    description: Optional[str] = None
    is_hidden: Optional[bool] = None
    is_key: Optional[bool] = None

class Measure(BaseModel):
    id: str
    name: str
    dataset_id: str
    table_id: Optional[str] = None
    expression: Optional[str] = None
    description: Optional[str] = None
    is_hidden: Optional[bool] = None

class AnalysisStats(BaseModel):
    latest_run_date: Optional[str] = None
    total_workspaces: int = 0
    total_datasets: int = 0
    total_tables: int = 0
    total_columns: int = 0
    total_measures: int = 0
    total_relationships: int = 0
    workspaces_on_dedicated: int = 0

# Database connection helper
def get_db_connection():
    db_path = "pbi_metadata.db"
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found. Please run a Power BI scan first.")
    return sqlite3.connect(db_path)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Power BI Catalog API", "status": "running"}

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "API is working", "endpoint": "test"}

@app.get("/api/datasets/test-id/details")
async def test_dataset_details():
    """Test dataset details endpoint with hardcoded ID"""
    return {"message": "Dataset details endpoint is working", "test": True}

@app.get("/api/config", response_model=TenantConfigResponse)
async def get_config():
    """
    Get tenant configuration from environment variables.
    Returns configuration without exposing the client secret.
    """
    tenant_id = os.getenv("TENANT_ID")
    client_id = os.getenv("CLIENT_ID") 
    client_secret = os.getenv("SECRET_VALUE")
    
    # Check if configuration is complete
    is_configured = all([tenant_id, client_id, client_secret])
    
    return TenantConfigResponse(
        tenant_id=tenant_id,
        client_id=client_id,
        has_client_secret=bool(client_secret),
        is_configured=is_configured
    )

@app.post("/api/config")
async def update_config(config: TenantConfig):
    """
    Update tenant configuration.
    Note: This endpoint validates but doesn't persist to .env file
    """
    if not config.tenant_id or not config.client_id or not config.client_secret:
        raise HTTPException(
            status_code=400, 
            detail="All configuration fields are required"
        )
    
    # In a real implementation, you might want to validate the credentials
    # by making a test API call to Power BI
    
    return {
        "message": "Configuration validated successfully",
        "is_configured": True
    }

# Legacy endpoints redirected to new implementations
@app.get("/api/workspaces")
async def get_workspaces_legacy():
    """Legacy workspaces endpoint"""
    workspaces = await get_workspaces_new()
    return {"workspaces": workspaces, "message": "Data loaded from SQLite"}

@app.get("/api/datasets") 
async def get_datasets_legacy():
    """Legacy datasets endpoint"""
    datasets = await get_datasets_new()
    return {"datasets": datasets, "message": "Data loaded from SQLite"}

@app.get("/api/stats", response_model=AnalysisStats)
async def get_analysis_stats():
    """Get overall analysis statistics from the latest scan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get latest analysis run stats
        cursor.execute("""
            SELECT run_date, workspaces_count, datasets_count, tables_count, 
                   columns_count, measures_count, relationships_count
            FROM analysis_runs 
            ORDER BY run_date DESC 
            LIMIT 1
        """)
        latest_run = cursor.fetchone()
        
        # Get workspaces on dedicated capacity count
        cursor.execute("SELECT COUNT(*) FROM workspaces WHERE is_on_dedicated_capacity = 1")
        dedicated_count = cursor.fetchone()[0]
        
        if latest_run:
            return AnalysisStats(
                latest_run_date=latest_run[0],
                total_workspaces=latest_run[1] or 0,
                total_datasets=latest_run[2] or 0,
                total_tables=latest_run[3] or 0,
                total_columns=latest_run[4] or 0,
                total_measures=latest_run[5] or 0,
                total_relationships=latest_run[6] or 0,
                workspaces_on_dedicated=dedicated_count
            )
        else:
            return AnalysisStats()
    finally:
        conn.close()

@app.get("/api/workspaces/list", response_model=List[Workspace])
async def get_workspaces_new(limit: int = Query(100, ge=1, le=1000)):
    """Get all workspaces with dataset counts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT w.id, w.name, w.type, w.is_on_dedicated_capacity,
                   COUNT(d.id) as datasets_count
            FROM workspaces w
            LEFT JOIN datasets d ON w.id = d.workspace_id
            GROUP BY w.id, w.name, w.type, w.is_on_dedicated_capacity
            ORDER BY datasets_count DESC, w.name
            LIMIT ?
        """, (limit,))
        
        workspaces = []
        for row in cursor.fetchall():
            workspaces.append(Workspace(
                id=row[0],
                name=row[1],
                type=row[2],
                is_on_dedicated_capacity=bool(row[3]) if row[3] is not None else None,
                datasets_count=row[4]
            ))
        
        return workspaces
    finally:
        conn.close()

@app.get("/api/datasets/list", response_model=List[Dataset])
async def get_datasets_new(
    workspace_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get datasets with workspace info and counts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        base_query = """
            SELECT d.id, d.name, d.workspace_id, w.name as workspace_name,
                   d.created_date, d.modified_date,
                   COUNT(DISTINCT t.id) as tables_count,
                   COUNT(DISTINCT m.id) as measures_count
            FROM datasets d
            JOIN workspaces w ON d.workspace_id = w.id
            LEFT JOIN tables t ON d.id = t.dataset_id
            LEFT JOIN measures m ON d.id = m.dataset_id
        """
        
        if workspace_id:
            cursor.execute(f"""
                {base_query}
                WHERE d.workspace_id = ?
                GROUP BY d.id, d.name, d.workspace_id, w.name, d.created_date, d.modified_date
                ORDER BY d.name
                LIMIT ?
            """, (workspace_id, limit))
        else:
            cursor.execute(f"""
                {base_query}
                GROUP BY d.id, d.name, d.workspace_id, w.name, d.created_date, d.modified_date
                ORDER BY tables_count DESC, d.name
                LIMIT ?
            """, (limit,))
        
        datasets = []
        for row in cursor.fetchall():
            datasets.append(Dataset(
                id=row[0],
                name=row[1],
                workspace_id=row[2],
                workspace_name=row[3],
                created_date=row[4],
                modified_date=row[5],
                tables_count=row[6],
                measures_count=row[7]
            ))
        
        return datasets
    finally:
        conn.close()

@app.get("/api/datasets/{dataset_id}/details")
async def get_dataset_details(dataset_id: str):
    """Get comprehensive details for a specific dataset"""
    print(f"DEBUG: Dataset details requested for ID: {dataset_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get dataset basic info
        cursor.execute("""
            SELECT d.id, d.name, d.workspace_id, w.name as workspace_name,
                   d.created_date, d.modified_date, w.is_on_dedicated_capacity
            FROM datasets d
            JOIN workspaces w ON d.workspace_id = w.id
            WHERE d.id = ?
        """, (dataset_id,))
        
        dataset_row = cursor.fetchone()
        if not dataset_row:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Get tables with column counts
        cursor.execute("""
            SELECT t.id, t.name, t.row_count, COUNT(c.id) as columns_count
            FROM tables t
            LEFT JOIN columns c ON t.id = c.table_id
            WHERE t.dataset_id = ?
            GROUP BY t.id, t.name, t.row_count
            ORDER BY t.name
        """, (dataset_id,))
        
        tables = []
        for row in cursor.fetchall():
            tables.append({
                "id": row[0],
                "name": row[1],
                "row_count": row[2],
                "columns_count": row[3]
            })
        
        # Get measures
        cursor.execute("""
            SELECT id, name, expression, description, is_hidden
            FROM measures
            WHERE dataset_id = ?
            ORDER BY name
        """, (dataset_id,))
        
        measures = []
        for row in cursor.fetchall():
            measures.append({
                "id": row[0],
                "name": row[1],
                "expression": row[2],
                "description": row[3],
                "is_hidden": bool(row[4])
            })
        
        # Get relationships
        cursor.execute("""
            SELECT id, from_table, from_column, to_table, to_column, 
                   cross_filtering_behavior, is_active
            FROM relationships
            WHERE dataset_id = ?
            ORDER BY from_table, to_table
        """, (dataset_id,))
        
        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                "id": row[0],
                "from_table": row[1],
                "from_column": row[2],
                "to_table": row[3],
                "to_column": row[4],
                "cross_filtering_behavior": row[5],
                "is_active": bool(row[6]) if row[6] is not None else None
            })
        
        return {
            "id": dataset_row[0],
            "name": dataset_row[1],
            "workspace_id": dataset_row[2],
            "workspace_name": dataset_row[3],
            "created_date": dataset_row[4],
            "modified_date": dataset_row[5],
            "is_on_dedicated_capacity": bool(dataset_row[6]) if dataset_row[6] is not None else None,
            "tables": tables,
            "measures": measures,
            "relationships": relationships,
            "summary": {
                "total_tables": len(tables),
                "total_measures": len(measures),
                "total_relationships": len(relationships),
                "total_columns": sum(t["columns_count"] for t in tables),
                "total_rows": sum(t["row_count"] or 0 for t in tables)
            }
        }
    finally:
        conn.close()

@app.get("/api/datasets/{dataset_id}/tables", response_model=List[Table])
async def get_dataset_tables(dataset_id: str):
    """Get all tables for a specific dataset"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT t.id, t.name, t.dataset_id, d.name as dataset_name, 
                   t.row_count, COUNT(c.id) as columns_count
            FROM tables t
            JOIN datasets d ON t.dataset_id = d.id
            LEFT JOIN columns c ON t.id = c.table_id
            WHERE t.dataset_id = ?
            GROUP BY t.id, t.name, t.dataset_id, d.name, t.row_count
            ORDER BY t.name
        """, (dataset_id,))
        
        tables = []
        for row in cursor.fetchall():
            tables.append(Table(
                id=row[0],
                name=row[1],
                dataset_id=row[2],
                dataset_name=row[3],
                row_count=row[4],
                columns_count=row[5]
            ))
        
        return tables
    finally:
        conn.close()

@app.get("/api/tables/{table_id}/columns")
async def get_table_columns(table_id: str):
    """Get all columns for a specific table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT c.id, c.name, c.data_type, c.description, c.is_hidden, 
                   c.data_category, c.is_key, t.name as table_name
            FROM columns c
            JOIN tables t ON c.table_id = t.id
            WHERE c.table_id = ?
            ORDER BY c.name
        """, (table_id,))
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                "id": row[0],
                "name": row[1],
                "data_type": row[2],
                "description": row[3],
                "is_hidden": bool(row[4]) if row[4] is not None else None,
                "data_category": row[5],
                "is_key": bool(row[6]) if row[6] is not None else None,
                "table_name": row[7]
            })
        
        return columns
    finally:
        conn.close()

@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=2),
    type: Optional[str] = Query(None, pattern="^(workspace|dataset|table|column|measure)$")
):
    """Search across all Power BI entities"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        results = {"workspaces": [], "datasets": [], "tables": [], "columns": [], "measures": []}
        search_term = f"%{q}%"
        
        if not type or type == "workspace":
            cursor.execute("SELECT id, name, type FROM workspaces WHERE name LIKE ? LIMIT 10", (search_term,))
            results["workspaces"] = [{"id": r[0], "name": r[1], "type": r[2]} for r in cursor.fetchall()]
        
        if not type or type == "dataset":
            cursor.execute("""
                SELECT d.id, d.name, w.name as workspace_name 
                FROM datasets d 
                JOIN workspaces w ON d.workspace_id = w.id 
                WHERE d.name LIKE ? LIMIT 10
            """, (search_term,))
            results["datasets"] = [{"id": r[0], "name": r[1], "workspace_name": r[2]} for r in cursor.fetchall()]
        
        if not type or type == "table":
            cursor.execute("""
                SELECT t.id, t.name, d.name as dataset_name 
                FROM tables t 
                JOIN datasets d ON t.dataset_id = d.id 
                WHERE t.name LIKE ? LIMIT 10
            """, (search_term,))
            results["tables"] = [{"id": r[0], "name": r[1], "dataset_name": r[2]} for r in cursor.fetchall()]
        
        if not type or type == "column":
            cursor.execute("""
                SELECT c.id, c.name, t.name as table_name, c.data_type 
                FROM columns c 
                JOIN tables t ON c.table_id = t.id 
                WHERE c.name LIKE ? LIMIT 10
            """, (search_term,))
            results["columns"] = [{"id": r[0], "name": r[1], "table_name": r[2], "data_type": r[3]} for r in cursor.fetchall()]
        
        if not type or type == "measure":
            cursor.execute("""
                SELECT m.id, m.name, d.name as dataset_name 
                FROM measures m 
                JOIN datasets d ON m.dataset_id = d.id 
                WHERE m.name LIKE ? LIMIT 10
            """, (search_term,))
            results["measures"] = [{"id": r[0], "name": r[1], "dataset_name": r[2]} for r in cursor.fetchall()]
        
        return results
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)