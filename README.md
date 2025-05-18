# Power BI Semantic Analyzer

> **⚠️ NOTE: DMV extraction and ADOMD.NET/pyadomd functionality only work on Windows.**
>
> The DLLs in the `lib/` folder are Windows-only and require the Microsoft Analysis Services OLEDB provider (MSOLAP) to be installed on your system. This project will **not work on macOS, Linux, or iOS** for DMV/metadata extraction via XMLA. If you need this functionality on non-Windows platforms, you must use a Windows machine or VM.

Python module for large-scale analysis of semantic models published on Power BI Service. Designed for agentic integration (e.g., LangChain).

## Key Features
- **Authentication Options**:
  - User authentication via MSAL device code flow (with public client_id, no app registration required)
  - Service Principal authentication (app registration) for automated/headless scenarios
- **Power BI REST API** navigation (workspaces, datasets)
- **XMLA endpoint connection** (DMV extraction) with both user and service principal auth
- **Tenant-wide analysis** to extract metadata from all accessible workspaces and datasets
- **Structured JSON output** (Pydantic)
- **LangChain wrapper** (Tool/RunnableLambda)

## Setup

### User Authentication (Interactive)
- Copy `.env.example` to `.env` and set the required variables. At minimum, set:
  ```
  POWERBI_PUBLIC_CLIENT_ID=d3590ed6-52b3-4102-aeff-aad2292ab01c
  ```

### Service Principal Authentication (Automated/Headless)
- Register an app in Azure AD and grant it appropriate permissions in Power BI Admin Portal
- Add the following to your `.env` file:
  ```
  CLIENT_ID=your-app-registration-client-id
  TENANT_ID=your-tenant-id
  SECRET_VALUE=your-client-secret
  ```
- For XMLA/pyadomd access, ensure the service principal is added as a member to the target workspaces

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

### Interactive User Authentication
```sh
python test_powerbi_connection.py
```
- You will be prompted to authenticate via device code flow (open the URL and enter the code)
- If successful, your accessible workspaces will be listed

### Service Principal Authentication
```sh
python test_pbi_service_principal_api.py
```
- Uses client credentials flow with your app registration
- Lists all workspaces accessible to the service principal

### XMLA/pyadomd Connection with Service Principal
```sh
python test_pyadomd_service_principal.py
```
- Connects to a specific dataset using XMLA endpoint
- Extracts table metadata using DMVs

### Full Tenant Analysis
```sh
python pbi_tenant_analyzer.py
```
- Scans all workspaces and datasets accessible to the service principal
- Extracts detailed metadata for each dataset
- Generates a comprehensive JSON report

## Notes

### Authentication Methods

- **User Authentication (Interactive)**:
  - Uses device code flow with public client ID
  - Supports MFA
  - Works with REST APIs but not with XMLA/pyadomd
  - No app registration required

- **Service Principal Authentication (Automated)**:
  - Uses client credentials flow with app registration
  - Works with both REST APIs and XMLA/pyadomd
  - Requires proper configuration in Azure AD and Power BI Admin Portal
  - Service principal must be added as a member to workspaces for XMLA access

### XMLA/pyadomd Requirements

- **Workspace Type**: Only Premium, Fabric, or PPU workspaces support XMLA endpoints
- **Connection String Format**:
  ```
  Provider=MSOLAP;Data Source=powerbi://api.powerbi.com/v1.0/myorg/<workspace>;
  Initial Catalog=<dataset>;User ID=app:<client_id>@<tenant_id>;
  Password=<client_secret>;Integrated Security=ClaimsToken;
  ```
- **Permissions**: Service principal must have at least Viewer access to the workspace

### Tenant Analysis

The `pbi_tenant_analyzer.py` script provides a comprehensive solution for analyzing an entire Power BI tenant:

- Scans all accessible workspaces using admin REST APIs
- Lists all datasets in each workspace
- Extracts detailed metadata for each dataset using XMLA/pyadomd
- Generates structured JSON output with tables, columns, measures, and relationships
- Creates a summary report with statistics about the tenant

## Known Issues

- **Personal Workspaces**: XMLA access may not work on personal workspaces, even if they are on Premium capacity
- **Trial Capacities**: Some features may be limited on Fabric Trial (FT1) capacities
- **Propagation Delay**: Changes to service principal permissions may take up to an hour to propagate

## Dependencies

- The ADOMD.NET DLLs in the `lib/` folder are required for XMLA connectivity
- Microsoft Analysis Services OLEDB provider (MSOLAP) must be installed on your system
- The project is Windows-only for XMLA/pyadomd functionality

## Example
See `test_powerbi_connection.py` for a minimal working example.
