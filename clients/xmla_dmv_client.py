# xmla_dmv_client.py
"""
Client per interrogazione modelli Power BI via XMLA/DMV.
"""

import os
from pyadomd import Pyadomd

class XmlaDMVClient:
    def __init__(self, workspace_name, dataset_name, access_token=None):
        self.workspace_name = workspace_name
        self.dataset_name = dataset_name
        self.access_token = access_token or os.environ.get("PBI_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("No access token provided. Set PBI_ACCESS_TOKEN or pass as argument.")
        self.endpoint = f"powerbi://api.powerbi.com/v1.0/myorg/{self.workspace_name}"

    def run_dmv_query(self, query):
        connection_str = (
            f"Provider=MSOLAP;Data Source={self.endpoint};"
            f"Initial Catalog={self.dataset_name};"
            f"User ID=;Password=;"
            f"Persist Security Info=True;"
            f"Impersonation Level=Impersonate;"
            f"Auth Token={self.access_token};"
        )
        with Pyadomd(connection_str) as conn:
            with conn.cursor().execute(query) as cur:
                columns = [col[0] for col in cur.description]
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    def list_tables(self):
        query = "SELECT * FROM $SYSTEM.TMSCHEMA_TABLES"
        return self.run_dmv_query(query)
