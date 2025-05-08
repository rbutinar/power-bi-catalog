from pydantic import BaseModel
from typing import List, Optional

class Dataset(BaseModel):
    id: str
    name: str
    owner: Optional[str]
    refresh_schedule: Optional[str]
    data_sources: Optional[List[str]]

class Workspace(BaseModel):
    id: str
    name: str
    datasets: List[Dataset] = []

class AnalyzerOutput(BaseModel):
    workspaces: List[Workspace]
