from clients.rest_client import PowerBIRestClient
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    try:
        print("[INFO] Avvio autenticazione device code flow...")
        client = PowerBIRestClient()
        workspaces = client.get_workspaces()
        if workspaces and 'value' in workspaces:
            print(f"[SUCCESS] Connessione riuscita! Workspace trovati: {len(workspaces['value'])}")
            for ws in workspaces['value']:
                print(f"- {ws.get('name')} (ID: {ws.get('id')})")
        else:
            print("[WARN] Connessione riuscita ma nessun workspace trovato.")
    except Exception as e:
        print(f"[ERROR] Connessione fallita: {e}")
