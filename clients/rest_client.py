# rest_client.py
"""
Client per chiamate REST verso Power BI Service (autenticazione utente tramite Device Code Flow e chiamate API).
"""
import msal
import requests

import os

import json
import time

class PowerBIRestClient:
    TOKEN_CACHE_FILE = ".pbi_token_cache.json"

    def __init__(self, client_id: str = None, tenant_id: str = "common"):
        self.client_id = client_id or os.environ.get('POWERBI_PUBLIC_CLIENT_ID')
        if not self.client_id:
            raise ValueError("client_id non specificato e variabile di ambiente POWERBI_PUBLIC_CLIENT_ID non trovata.")
        self.tenant_id = tenant_id
        self.scope = ["https://analysis.windows.net/powerbi/api/.default"]
        self.access_token = self.get_or_authenticate()

    def get_or_authenticate(self):
        # Try loading a cached token
        token_data = None
        if os.path.exists(self.TOKEN_CACHE_FILE):
            try:
                with open(self.TOKEN_CACHE_FILE, "r", encoding="utf-8") as f:
                    token_data = json.load(f)
                if token_data and token_data.get("expires_at", 0) > int(time.time()) + 60:  # 60s leeway
                    return token_data["access_token"]
            except Exception:
                pass  # Ignore errors and force re-authentication
        # Authenticate and save token
        token, expires_in = self.authenticate_with_expiry()
        expires_at = int(time.time()) + expires_in
        with open(self.TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({"access_token": token, "expires_at": expires_at}, f)
        return token

    def authenticate_with_expiry(self):
        authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        app = msal.PublicClientApplication(self.client_id, authority=authority)
        flow = app.initiate_device_flow(scopes=self.scope)
        if "user_code" not in flow:
            raise Exception("Impossibile iniziare il device code flow.")
        print(f"Per autenticarti, visita {flow['verification_uri']} e inserisci il codice: {flow['user_code']}")
        result = app.acquire_token_by_device_flow(flow)
        if "access_token" in result:
            return result["access_token"], result.get("expires_in", 3600)
        else:
            raise Exception(f"Autenticazione fallita: {result}")

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

    def get_datasets(self, workspace_id):
        """
        Returns all datasets (semantic models) for the given workspace.
        """
        url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
        response = self.get(url)
        response.raise_for_status()
        return response.json()
