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

**Attenzione:** Al momento l'utilizzo delle DMV tramite Pyadomd (es. estrazione tabelle via XMLA/DMV) non funziona correttamente su Windows, a causa di problemi di caricamento delle DLL native e dipendenze di ADOMD.NET. 

- Anche se tutte le DLL richieste sono presenti nella cartella `lib`, la libreria Pyadomd potrebbe non riuscire a caricare alcune dipendenze native (es. `System.Data.SqlXml.dll`, `Microsoft.Data.SqlClient.dll`).
- L'errore tipico è "Could not load file or assembly 'Microsoft.AnalysisServices.AdomdClient' or one of its dependencies".
- Il supporto per l'accesso alle DMV è in fase di troubleshooting e la soluzione non è ancora stabile.

**Workaround**: consultare `DLL_LIST.txt` per la lista delle DLL richieste e seguire eventuali aggiornamenti nel repository.

- No app registration is required: the public Power BI client_id is used (same as Tabular Editor/DAX Studio)
- MFA is fully supported via device code flow
- For custom integrations, use the `PowerBIRestClient` class in `clients/rest_client.py`

## Example
See `test_powerbi_connection.py` for a minimal working example.
