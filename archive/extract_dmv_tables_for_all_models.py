import os
# Ensure the DLL directory is in PATH for pyadomd/ADOMD.NET
os.environ["PATH"] += os.pathsep + os.path.abspath("lib")

import json
from clients.rest_client import PowerBIRestClient
from clients.xmla_dmv_client import XmlaDMVClient
from dotenv import load_dotenv

load_dotenv()

# Load semantic models list
with open("all_semantic_models.json", "r", encoding="utf-8") as f:
    all_models = json.load(f)

# Authenticate and get access token (reuse device code flow)
client = PowerBIRestClient()
access_token = client.access_token
os.environ["PBI_ACCESS_TOKEN"] = access_token  # For XmlaDMVClient

enriched_models = []

for model in all_models:
    ws_name = model["workspace_name"]
    ds_name = model["dataset_name"]
    try:
        dmv_client = XmlaDMVClient(ws_name, ds_name, access_token=access_token)
        tables = dmv_client.list_tables()
        model["tables"] = tables
        print(f"[SUCCESS] Extracted {len(tables)} tables for: {ws_name} / {ds_name}")
    except Exception as e:
        model["tables"] = None
        model["dmv_error"] = str(e)
        print(f"[ERROR] Failed DMV extraction for: {ws_name} / {ds_name} -- {e}")
    enriched_models.append(model)

with open("all_semantic_models_with_tables.json", "w", encoding="utf-8") as f:
    json.dump(enriched_models, f, indent=2, ensure_ascii=False)

print(f"\nDone. Enriched metadata saved to all_semantic_models_with_tables.json")
