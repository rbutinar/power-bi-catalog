from clients.rest_client import PowerBIRestClient
from dotenv import load_dotenv
import json

load_dotenv()

if __name__ == "__main__":
    client = PowerBIRestClient()
    workspaces = client.get_workspaces().get("value", [])
    all_models = []
    for ws in workspaces:
        ws_name = ws.get('name')
        ws_id = ws.get('id')
        datasets = client.get_datasets(ws_id).get("value", [])
        for ds in datasets:
            model_info = {
                "workspace_name": ws_name,
                "workspace_id": ws_id,
                "dataset_name": ds.get('name'),
                "dataset_id": ds.get('id')
            }
            all_models.append(model_info)
            print(f"Workspace: {ws_name} (ID: {ws_id}) -> Semantic Model: {ds.get('name')} (ID: {ds.get('id')})")
    # Optionally, save as JSON
    import os
    from pathlib import Path
    output_dir = "tenant_analysis_user_auth"
    Path(output_dir).mkdir(exist_ok=True)
    json_path = os.path.join(output_dir, "all_semantic_models.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_models, f, indent=2, ensure_ascii=False)
    print(f"\nTotal semantic models found: {len(all_models)}. Full list saved to {json_path}")
