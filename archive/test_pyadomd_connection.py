import os
# Aggiungi la cartella 'lib' al PATH per consentire a pyadomd di trovare la DLL AdomdClient
os.environ["PATH"] += os.pathsep + os.path.abspath("lib")

# Aggiungi anche la directory di installazione ADOMD.NET (modifica il path secondo la versione installata)
adomd_dir = r"C:\Program Files\Microsoft.NET\ADOMD.NET\160"
os.environ["PATH"] += os.pathsep + adomd_dir
import sys
sys.path.append(adomd_dir)
print(f"PATH aggiunto anche: {adomd_dir}")

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
WORKSPACE_NAME = os.getenv("WORKSPACE_NAME", "INSERISCI_WORKSPACE_NAME")
# Rimuovi virgolette se presenti
if WORKSPACE_NAME.startswith('"') and WORKSPACE_NAME.endswith('"'):
    WORKSPACE_NAME = WORKSPACE_NAME[1:-1]
print(f"[DEBUG] WORKSPACE_NAME: {WORKSPACE_NAME}")
DATASET_NAME = os.getenv("DATASET_NAME", "INSERISCI_DATASET_NAME")
# Rimuovi virgolette se presenti
if DATASET_NAME.startswith('"') and DATASET_NAME.endswith('"'):
    DATASET_NAME = DATASET_NAME[1:-1]
print(f"[DEBUG] DATASET_NAME: {DATASET_NAME}")
ACCESS_TOKEN = os.getenv("PBI_ACCESS_TOKEN") or "INSERISCI_ACCESS_TOKEN"

endpoint = f"powerbi://api.powerbi.com/v1.0/myorg/{WORKSPACE_NAME}"
# Ottieni un token usando client credentials (service principal)
import requests
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
# Usa SECRET_VALUE come client secret
CLIENT_SECRET = os.getenv("SECRET_VALUE")
TENANT_ID = os.getenv("TENANT_ID")
SCOPE = "https://analysis.windows.net/powerbi/api/.default"

if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
    raise Exception("CLIENT_ID, SECRET_VALUE e TENANT_ID devono essere settati in .env!")

token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
data = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": SCOPE,
}
resp = requests.post(token_url, data=data)
if resp.status_code != 200:
    raise Exception(f"Errore ottenimento token: {resp.text}")
ACCESS_TOKEN = resp.json()["access_token"]
print(f"[DEBUG] Token ottenuto via client_credentials: {ACCESS_TOKEN[:8]}...{ACCESS_TOKEN[-8:]}")

connection_str = (
    f"Provider=MSOLAP;Data Source={endpoint};"
    f"Initial Catalog={DATASET_NAME};"
    f"User ID=;"
    f"Password={'*'*8 + ACCESS_TOKEN[-4:] if ACCESS_TOKEN else ''};"
    f"Persist Security Info=True;"
    f"Impersonation Level=Impersonate;"
)

# Stampa la connection string oscurando il token
conn_str_dbg = connection_str.replace(ACCESS_TOKEN, "***TOKEN***") if ACCESS_TOKEN else connection_str
print(f"Connessione stringa: {conn_str_dbg}")
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
