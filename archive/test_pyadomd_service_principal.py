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

WORKSPACE_NAME = os.getenv("WORKSPACE_NAME", "INSERISCI_WORKSPACE_NAME")
if WORKSPACE_NAME.startswith('"') and WORKSPACE_NAME.endswith('"'):
    WORKSPACE_NAME = WORKSPACE_NAME[1:-1]
print(f"[DEBUG] WORKSPACE_NAME: {WORKSPACE_NAME}")
DATASET_NAME = os.getenv("DATASET_NAME", "INSERISCI_DATASET_NAME")
if DATASET_NAME.startswith('"') and DATASET_NAME.endswith('"'):
    DATASET_NAME = DATASET_NAME[1:-1]
print(f"[DEBUG] DATASET_NAME: {DATASET_NAME}")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("SECRET_VALUE")
TENANT_ID = os.getenv("TENANT_ID")

if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
    raise Exception("CLIENT_ID, SECRET_VALUE e TENANT_ID devono essere settati in .env!")

endpoint = f"powerbi://api.powerbi.com/v1.0/myorg/{WORKSPACE_NAME}"

connection_str = (
    f"Provider=MSOLAP;Data Source={endpoint};"
    f"Initial Catalog={DATASET_NAME};"
    f"User ID=app:{CLIENT_ID}@{TENANT_ID};"
    f"Password={CLIENT_SECRET};"
    f"Integrated Security=ClaimsToken;"
)

# Stampa la connection string oscurando il secret
conn_str_dbg = connection_str.replace(CLIENT_SECRET, "***SECRET***") if CLIENT_SECRET else connection_str
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
