from msal import ConfidentialClientApplication
import requests
from .config import Config
from .models import AnalyzerOutput, Workspace, Dataset

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

    # Stub for further REST/XMLA logic
    def analyze(self):
        workspaces = self.list_workspaces()
        # Only minimal output for now
        ws_models = [Workspace(id=ws["id"], name=ws["name"], datasets=[]) for ws in workspaces]
        return AnalyzerOutput(workspaces=ws_models)
