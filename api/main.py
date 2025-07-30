"""
FastAPI backend for Power BI Catalog
"""
import os
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
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

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Power BI Catalog API", "status": "running"}

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

@app.get("/api/workspaces")
async def get_workspaces():
    """
    Get Power BI workspaces.
    TODO: Implement actual Power BI API integration
    """
    # Check if configured
    config_response = await get_config()
    if not config_response.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Power BI tenant not configured. Please configure your credentials first."
        )
    
    # Placeholder response
    return {
        "workspaces": [],
        "message": "Power BI API integration coming soon"
    }

@app.get("/api/datasets")
async def get_datasets():
    """
    Get Power BI datasets.
    TODO: Implement actual Power BI API integration
    """
    # Check if configured
    config_response = await get_config()
    if not config_response.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Power BI tenant not configured. Please configure your credentials first."
        )
    
    # Placeholder response
    return {
        "datasets": [],
        "message": "Power BI API integration coming soon"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)