from msal import ConfidentialClientApplication
import requests
from .config import Config
from .models import (
    AnalyzerOutput, Workspace, Dataset, Table, Column, Measure, Relationship, Role, RLSRule
)
import os
import platform
# Add local 'lib' directory to PATH for ADOMD.NET DLL (cross-platform)
dll_dir = os.path.join(os.path.dirname(__file__), "lib")
adomd_dll = os.path.join(dll_dir, "Microsoft.AnalysisServices.AdomdClient.dll")
PYADOMD_AVAILABLE = False
if platform.system() == "Windows" and os.path.isdir(dll_dir) and os.path.isfile(adomd_dll):
    os.environ["PATH"] += os.pathsep + dll_dir
    try:
        import pyadomd
        PYADOMD_AVAILABLE = True
    except ImportError:
        print("[WARN] pyadomd non disponibile. Le query DMV/XMLA sono disabilitate.")
else:
    print(f"[INFO] Funzionalità XMLA/DMV disabilitata (non Windows o DLL mancante)")
# ---
# Per abilitare le query DMV/XMLA, assicurarsi di essere su Windows e avere la DLL corretta. In futuro questa sezione sarà riattivata per utenti Windows.

class PBISemanticAnalyzer:
    def __init__(self, config: Config):
        self.config = config
        self.token = self.authenticate()

    def authenticate(self):
        app = ConfidentialClientApplication(
            client_id=self.config.client_id,
            client_credential=self.config.client_secret,
            authority=f"https://login.microsoftonline.com/{self.config.tenant_id}"
        )
        result = app.acquire_token_for_client(scopes=["https://analysis.windows.net/powerbi/api/.default"])
        if "access_token" not in result:
            raise Exception(f"Authentication failed: {result}")
        return result["access_token"]

    def list_workspaces(self):
        url = "https://api.powerbi.com/v1.0/myorg/groups"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("value", [])

    def list_datasets(self, workspace_id):
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("value", [])

    def list_reports(self, workspace_id):
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json().get("value", [])

    def get_dataset_refresh(self, workspace_id, dataset_id):
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            refreshes = response.json().get("value", [])
            if refreshes:
                return refreshes[0].get("startTime", None)
        return None

    def get_dataset_datasources(self, workspace_id, dataset_id):
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/datasources"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return [ds.get("datasourceType") for ds in response.json().get("value", [])]
        return []

    def get_dataset_owner(self, workspace_id, dataset_id):
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("configuredBy", None)
        return None

    def analyze_dataset_xmla(self, workspace_id, dataset_id):
        # Connessione XMLA endpoint usando pyadomd
        # NB: endpoint_url deve essere configurato o calcolato
        endpoint_url = f"powerbi://api.powerbi.com/v1.0/myorg/{workspace_id}"
        conn_str = f"Provider=MSOLAP;Data Source={endpoint_url};Initial Catalog={dataset_id};User ID=app:{self.config.client_id};Password={self.config.client_secret};"
        tables, relationships, roles = [], [], []
        try:
            with pyadomd.Connection(conn_str) as conn:
                # Tabelle e colonne
                tables = self._extract_tables_and_columns(conn)
                # Misure
                self._extract_measures(conn, tables)
                # Relazioni
                relationships = self._extract_relationships(conn)
                # Ruoli e RLS
                roles = self._extract_roles(conn)
        except Exception as e:
            # Gestione errori di connessione XMLA
            print(f"[XMLA] Error analyzing dataset {dataset_id} in workspace {workspace_id}: {e}")
        return tables, relationships, roles

    def _extract_tables_and_columns(self, conn):
        tables = []
        cmd = pyadomd.Command("SELECT * FROM $SYSTEM.TMSCHEMA_TABLES", conn)
        result = cmd.ExecuteReader()
        table_map = {}
        for row in result:
            table = Table(name=row["name"], columns=[], measures=[])
            table_map[row["id"]] = table
        # Colonne
        cmd = pyadomd.Command("SELECT * FROM $SYSTEM.TMSCHEMA_COLUMNS", conn)
        result = cmd.ExecuteReader()
        for row in result:
            col = Column(name=row["name"], data_type=row.get("dataType"))
            table_id = row["tableID"]
            if table_id in table_map:
                table_map[table_id].columns.append(col)
        tables = list(table_map.values())
        return tables

    def _extract_measures(self, conn, tables):
        cmd = pyadomd.Command("SELECT * FROM $SYSTEM.TMSCHEMA_MEASURES", conn)
        result = cmd.ExecuteReader()
        table_dict = {t.name: t for t in tables}
        for row in result:
            measure = Measure(name=row["name"], expression=row["expression"], table=row["tableID"])
            if measure.table in table_dict:
                table_dict[measure.table].measures.append(measure)

    def _extract_relationships(self, conn):
        relationships = []
        cmd = pyadomd.Command("SELECT * FROM $SYSTEM.TMSCHEMA_RELATIONSHIPS", conn)
        result = cmd.ExecuteReader()
        for row in result:
            relationships.append(Relationship(
                from_table=row["fromTableID"],
                from_column=row["fromColumnID"],
                to_table=row["toTableID"],
                to_column=row["toColumnID"],
                relationship_type=row.get("crossFilteringBehavior")
            ))
        return relationships

    def _extract_roles(self, conn):
        roles = []
        cmd = pyadomd.Command("SELECT * FROM $SYSTEM.TMSCHEMA_ROLES", conn)
        result = cmd.ExecuteReader()
        for row in result:
            role_name = row["name"]
            rules = self._extract_rls_rules(conn, row["id"])
            roles.append(Role(name=role_name, rules=rules))
        return roles

    def _extract_rls_rules(self, conn, role_id):
        rules = []
        cmd = pyadomd.Command(f"SELECT * FROM $SYSTEM.TMSCHEMA_ROWLEVELSECURITY WHERE roleID = '{role_id}'", conn)
        result = cmd.ExecuteReader()
        for row in result:
            rules.append(RLSRule(table=row["tableID"], filter_expression=row["filterExpression"]))
        return rules

    def analyze(self):
        workspaces = self.list_workspaces()
        ws_models = []
        for ws in workspaces:
            ws_id = ws["id"]
            ws_name = ws["name"]
            datasets = self.list_datasets(ws_id)
            ds_models = []
            for ds in datasets:
                ds_id = ds["id"]
                ds_name = ds["name"]
                owner = self.get_dataset_owner(ws_id, ds_id)
                refresh = self.get_dataset_refresh(ws_id, ds_id)
                datasources = self.get_dataset_datasources(ws_id, ds_id)
                tables, relationships, roles = self.analyze_dataset_xmla(ws_id, ds_id)
                ds_models.append(Dataset(
                    id=ds_id,
                    name=ds_name,
                    owner=owner,
                    refresh_schedule=refresh,
                    data_sources=datasources,
                    tables=tables,
                    relationships=relationships,
                    roles=roles
                ))
            ws_models.append(Workspace(id=ws_id, name=ws_name, datasets=ds_models))
        return AnalyzerOutput(workspaces=ws_models)
