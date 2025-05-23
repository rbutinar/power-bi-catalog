"""
Power BI Datasource Analyzer
---------------------------
This script scans a Power BI tenant using service principal authentication to:
1. List all workspaces (admin/groups endpoint)
2. List all datasets in each workspace
3. Retrieve datasource info for each dataset using the REST API

Outputs all datasource info to a JSON file.
"""
import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["SECRET_VALUE"]
TENANT_ID = os.environ["TENANT_ID"]
OUTPUT_DIR = "tenant_analysis_service_principal"

Path(OUTPUT_DIR).mkdir(exist_ok=True)

def log(message):
    print(f"[{datetime.now()}] {message}")

def get_access_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default"
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def get_workspaces(token):
    url = "https://api.powerbi.com/v1.0/myorg/admin/groups?%24top=5000"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["value"]

def get_datasets_in_workspace(token, workspace_id):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["value"]

def get_datasources_in_dataset(token, workspace_id, dataset_id):
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/datasets/{dataset_id}/datasources"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["value"]

def main():
    token = get_access_token()
    log("Fetched access token.")
    workspaces = get_workspaces(token)
    log(f"Found {len(workspaces)} workspaces.")
    all_datasources = []
    for ws in workspaces:
        ws_id = ws["id"]
        ws_name = ws.get("name", "<no name>")
        log(f"Processing workspace: {ws_name} ({ws_id})")
        try:
            datasets = get_datasets_in_workspace(token, ws_id)
        except Exception as e:
            log(f"Failed to get datasets for workspace {ws_name}: {e}")
            continue
        for ds in datasets:
            ds_id = ds["id"]
            ds_name = ds.get("name", "<no name>")
            log(f"  Dataset: {ds_name} ({ds_id})")
            try:
                datasources = get_datasources_in_dataset(token, ws_id, ds_id)
            except Exception as e:
                log(f"    Failed to get datasources for dataset {ds_name}: {e}")
                continue
            for datasource in datasources:
                entry = {
                    "workspace_id": ws_id,
                    "workspace_name": ws_name,
                    "dataset_id": ds_id,
                    "dataset_name": ds_name,
                    "datasource": datasource
                }
                all_datasources.append(entry)
    output_path = os.path.join(OUTPUT_DIR, "datasources_info.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_datasources, f, indent=2)
    log(f"Datasource info written to {output_path}")

if __name__ == "__main__":
    main()
