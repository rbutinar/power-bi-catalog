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

## Requirements
- Python 3.9+
- See `requirements.txt` for dependencies

## Usage

### Full Tenant Analysis (Recommended)
Run the main analyzer with service principal authentication:
```bash
python pbi_tenant_analyzer.py
```
- Scans all workspaces and datasets in the tenant.
- Extracts detailed metadata and outputs structured JSON.

### Fallback and Diagnostics
Scripts in `examples/` provide:
- User authentication (device code flow) for basic listing of semantic models when app registration is not available.
- Diagnostic scripts for REST API and XMLA connectivity.

Example:
```bash
python examples/test_powerbi_connection.py
```

### Legacy Scripts
Legacy or superseded scripts are in the `archive/` directory. These are not maintained but available for reference.

## Directory Overview
```
|-- pbi_tenant_analyzer.py         # Main entry point (service principal, full tenant analysis)
|-- archive/                       # Legacy, unfinished, or experimental code (not used in main workflow)
|-- utilities/                     # Utility scripts (e.g., token analysis)
|-- README.md, requirements.txt, .env, etc.
```

## Active Code

- **pbi_tenant_analyzer.py**: Main script for tenant-wide semantic analysis using **service principal authentication** (app registration, client credentials flow). Outputs detailed metadata for all datasets in the tenant to `tenant_analysis_service_principal/`. _Recommended for automation and production._

- **list_all_semantic_models_user_auth.py**: Fallback script for listing all semantic models (datasets) in the tenant using **user authentication** (device code flow). Outputs a basic listing to `tenant_analysis_user_auth/`. Use this if service principal authentication is not available. Depends on `clients/rest_client.py`.

- **clients/**: Only `rest_client.py` is used for user authentication fallback. All other modules are archived.

### Authentication & Output Summary

| Script                                 | Authentication         | Output Directory                     | Purpose                                  |
|----------------------------------------|------------------------|--------------------------------------|------------------------------------------|
| pbi_tenant_analyzer.py                 | Service Principal      | tenant_analysis_service_principal/   | Full tenant scan, detailed metadata      |
| list_all_semantic_models_user_auth.py  | User (Device Code)    | tenant_analysis_user_auth/           | List all accessible semantic models      |


## Legacy, Unfinished, or Experimental Code
- **archive/** contains scripts and modules that are not part of the current main workflow. These are kept for reference or possible future development, but are not maintained or recommended for use. Notable files:
  - `analyzer.py`: Early or alternative class-based analyzer abstraction.
  - `app.config`: Legacy or experimental configuration file (possibly for DLL or .NET integration).
  - `langchain_wrapper.py`: Experimental LLM/LangChain integration (not part of main workflow).
  - `config.py`, `models.py`: Configuration and data models used only by legacy or experimental code.
  - `config/`, `config.yaml`: Project configuration directory and file, currently unused.
  - `clients/`: REST/XMLA client modules, now archived as reference code.
  - Other scripts that have been superseded or are unfinished.

---

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
