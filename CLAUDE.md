# CLAUDE.md

## Project Overview
Power BI Catalog is a [Python FastAPI] backend and [React] frontend web application.  
The goal is to provide a **data catalog and internal marketplace** for Power BI and data assets, including asset search, tagging, metadata, and access requests.

## Key Technologies
- Backend: Python 3.11+, FastAPI, SQLAlchemy, SQLite (MVP), Docker
- Frontend: React (Vite, TypeScript), Material UI

## Conventions & Architecture
- Use Pydantic models for all API schemas
- Endpoints should be RESTful (e.g., /api/assets, /api/requests)
- DB models must be normalized; asset relationships, owners, and permissions modeled clearly
- Favor async functions for API routes
- UI should be clean, mobile-friendly, and use a sidebar for navigation

## Coding Style
- Use type hints throughout Python
- Write concise docstrings for each function and class
- React: use functional components and hooks, keep state local unless shared
- Use PascalCase for React components, snake_case for Python

## Development Environment Setup
### Python Backend (WSL)
- Before running tests, remember to activate the Python virtual environment in .venv
- Use `.venv/Scripts/python.exe` for running Python scripts in WSL
- Remember you are working in a Windows WSL emulation

### React Frontend (Windows)
- **Important**: Run React development server from Windows, not WSL
- WSL network binding issues prevent browser access to localhost from Windows
- **Commands to run from Windows PowerShell/CMD:**
  ```cmd
  cd C:\codebase\power-bi-catalog\frontend
  npm install
  npm run dev
  ```
- **Why**: WSL runs the server internally but Windows browser cannot access WSL localhost
- **Alternative**: In WSL, use `npx vite --host 0.0.0.0` and access via WSL IP address

## Current State (as of July 2025)
- This is an MVP/prototype.
- **Frontend**: React app with configuration UI and sidebar navigation ✅
- **Backend**: Python module/script that scans Power BI assets, extracts metadata, and writes to SQLite
- **Missing**: FastAPI backend to connect frontend to Python scanning logic
- **Goal**: Complete the FastAPI backend to bridge React frontend with existing Python Power BI scanning functionality