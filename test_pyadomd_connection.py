import os
# Aggiungi la cartella 'lib' al PATH per consentire a pyadomd di trovare la DLL AdomdClient
os.environ["PATH"] += os.pathsep + os.path.abspath("lib")

# DEBUG: verifica path e presenza DLL
lib_path = os.path.abspath("lib")
print(f"PATH aggiunto: {lib_path}")
try:
    print("Contenuto di lib:", os.listdir(lib_path))
except Exception as e:
    print(f"Errore nel listare la cartella lib: {e}")
dll_path = os.path.join(lib_path, "Microsoft.AnalysisServices.AdomdClient.dll")
print("DLL presente?", os.path.exists(dll_path))

import traceback
from dotenv import load_dotenv
from pyadomd import Pyadomd

load_dotenv()

# Parametri di test: inserisci qui workspace e dataset di un modello a cui hai accesso XMLA
WORKSPACE_NAME = os.getenv("TEST_WORKSPACE_NAME") or "INSERISCI_WORKSPACE_NAME"
DATASET_NAME = os.getenv("TEST_DATASET_NAME") or "INSERISCI_DATASET_NAME"
ACCESS_TOKEN = os.getenv("PBI_ACCESS_TOKEN") or "INSERISCI_ACCESS_TOKEN"

endpoint = f"powerbi://api.powerbi.com/v1.0/myorg/{WORKSPACE_NAME}"
connection_str = (
    f"Provider=MSOLAP;Data Source={endpoint};"
    f"Initial Catalog={DATASET_NAME};"
    f"User ID=;Password=;"
    f"Persist Security Info=True;"
    f"Impersonation Level=Impersonate;"
    f"Auth Token={ACCESS_TOKEN};"
)

print(f"Connessione a: {endpoint}\nDataset: {DATASET_NAME}")

try:
    with Pyadomd(connection_str) as conn:
        with conn.cursor().execute("SELECT * FROM $SYSTEM.TMSCHEMA_TABLES") as cur:
            columns = [col[0] for col in cur.description]
            rows = cur.fetchall()
            print(f"Colonne: {columns}")
            print(f"Numero righe restituite: {len(rows)}")
except Exception as e:
    print("Errore nella connessione Pyadomd o nell'esecuzione della query:")
    traceback.print_exc()
