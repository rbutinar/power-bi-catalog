from pydantic import BaseModel
from typing import List, Optional

class Measure(BaseModel):
    name: str
    expression: str
    table: str

class Column(BaseModel):
    name: str
    data_type: Optional[str]

class Table(BaseModel):
    name: str
    columns: List[Column] = []
    measures: List[Measure] = []

class Relationship(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: Optional[str]

class RLSRule(BaseModel):
    table: str
    filter_expression: str

class Role(BaseModel):
    name: str
    rules: List[RLSRule] = []

class Dataset(BaseModel):
    id: str
    name: str
    owner: Optional[str]
    refresh_schedule: Optional[str]
    data_sources: Optional[List[str]]
    tables: List[Table] = []
    relationships: List[Relationship] = []
    roles: List[Role] = []

class Workspace(BaseModel):
    id: str
    name: str
    datasets: List[Dataset] = []

class AnalyzerOutput(BaseModel):
    workspaces: List[Workspace]
