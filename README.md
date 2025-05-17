# Power BI Semantic Analyzer

> **⚠️ NOTE: DMV extraction and ADOMD.NET/pyadomd functionality only work on Windows.**
>
> The DLLs in the `lib/` folder are Windows-only and require the Microsoft Analysis Services OLEDB provider (MSOLAP) to be installed on your system. This project will **not work on macOS, Linux, or iOS** for DMV/metadata extraction via XMLA. If you need this functionality on non-Windows platforms, you must use a Windows machine or VM.

Python module for large-scale analysis of semantic models published on Power BI Service. Designed for agentic integration (e.g., LangChain).

## Key Features
- User authentication via MSAL device code flow (with public client_id, no app registration required)
- Power BI REST API navigation (workspaces, datasets)
- XMLA endpoint connection (DMV extraction)
- Structured JSON output (Pydantic)
- LangChain wrapper (Tool/RunnableLambda)

## Setup
- Copy `.env.example` to `.env` and set the required variables. At minimum, set:
  ```
  POWERBI_PUBLIC_CLIENT_ID=d3590ed6-52b3-4102-aeff-aad2292ab01c
  ```
- Other variables (e.g., for OpenAI) are optional unless you use those features.
- The project uses [python-dotenv](https://pypi.org/project/python-dotenv/) to load environment variables from `.env`.

## Requirements
- Python 3.9+
- See `requirements.txt` for dependencies

## Usage
1. Configure environment variables in `.env`
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Test authentication and connection:
   ```sh
   python test_powerbi_connection.py
   ```
   - You will be prompted to authenticate via device code flow (open the URL and enter the code)
   - If successful, your accessible workspaces will be listed

## Notes

## Known Issues

### Autenticazione ADOMD.NET / pyadomd su Power BI XMLA

- **Non è più un problema di librerie native/DLL**: ora tutte le dipendenze e le DLL risultano correttamente caricate e individuate dal sistema.
- **Il problema attuale è legato all'autenticazione**: la connessione tramite pyadomd/ADOMD.NET agli endpoint XMLA di Power BI fallisce se si utilizza un access token ottenuto tramite device code flow (login interattivo). Questo tipo di token funziona con le REST API di Power BI, ma non è accettato da ADOMD.NET per l'accesso XMLA.
- **Sono richiesti token specifici**: ADOMD.NET accetta solo token ottenuti tramite grant_type `client_credentials` (service principal) o, in alcuni casi, grant_type `password` (login diretto, se consentito dal tenant). I token device code flow non sono supportati per l'accesso XMLA.
- **Soluzione consigliata**: utilizzare un service principal abilitato per l'accesso XMLA e ottenere un token con grant_type `client_credentials`.
- **Workspace Premium/PPU**: si ricorda che solo i workspace Power BI Premium o Premium Per User supportano l'accesso XMLA.
- **[TODO]**: Il testing completo dell'accesso tramite app registration/service principal non è ancora stato ultimato e il ciclo di accesso alle DMV tramite ADOMD.NET è ancora in fase di chiusura. Aggiornamenti seguiranno.

### Pulizia dipendenze/librerie

- È necessario effettuare una revisione e pulizia delle dipendenze nel progetto per rimuovere librerie non più utilizzate o superflue, ora che la fase di troubleshooting sulle DLL è conclusa. Consultare `DLL_LIST.txt` e la sezione requirements per aggiornamenti futuri.

**Workaround**: consultare `DLL_LIST.txt` per la lista delle DLL richieste e seguire eventuali aggiornamenti nel repository.

- No app registration is required: the public Power BI client_id is used (same as Tabular Editor/DAX Studio)
- MFA is fully supported via device code flow

## Example
See `test_powerbi_connection.py` for a minimal working example.
