"""
Test Power BI REST API connectivity using App Registration (Service Principal)
This script authenticates via client credentials and lists all workspaces (admin/groups endpoint).
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.environ["TENANT_ID"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["SECRET_VALUE"]

def get_access_token():
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    token_data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }
    r = requests.post(token_url, data=token_data)
    r.raise_for_status()
    return r.json()["access_token"]

def list_workspaces(token):
    # Add $top=100 to comply with API requirements
    api_url = "https://api.powerbi.com/v1.0/myorg/admin/groups?$top=100"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(api_url, headers=headers)
    print("Status code:", resp.status_code)
    try:
        print("Response:", resp.json())
    except Exception:
        print(resp.text)

if __name__ == "__main__":
    print("[INFO] Authenticating using App Registration (Service Principal)...")
    token = get_access_token()
    print("[INFO] Access token obtained (truncated):", token[:40] + "..." )
    print("[INFO] Querying Power BI admin/groups endpoint...")
    list_workspaces(token)
