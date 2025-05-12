# rest_client.py
"""
Client per chiamate REST verso Power BI Service (autenticazione utente tramite Device Code Flow e chiamate API).
"""
import msal
import requests

class PowerBIRestClient:
    def __init__(self, client_id: str, tenant_id: str = "common"):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.scope = ["https://analysis.windows.net/powerbi/api/.default"]
        self.access_token = self.authenticate()

    def authenticate(self):
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.PublicClientApplication(self.client_id, authority=authority)
        flow = app.initiate_device_flow(scopes=self.scope)
        if "user_code" not in flow:
            raise Exception("Impossibile iniziare il device code flow.")
        print(f"Per autenticarti, visita {flow['verification_uri']} e inserisci il codice: {flow['user_code']}")
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Autenticazione fallita: {result}")

    def get(self, url, **kwargs):
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        return requests.get(url, headers=headers, **kwargs)

    def get_workspaces(self):
        url = "https://api.powerbi.com/v1.0/myorg/groups"
        response = self.get(url)
        response.raise_for_status()
        return response.json()
