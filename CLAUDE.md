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

### Multi-Terminal Development Workflow (RECOMMENDED 2025)
**Best Practice**: Use separate WSL terminals for Claude Code and development servers

**Terminal Setup:**
- **Terminal 1**: Claude Code session (this terminal) - for code assistance, git, debugging
- **Terminal 2**: Backend server - dedicated for uvicorn FastAPI server  
- **Terminal 3**: Frontend server - dedicated for Vite React development server

**Why This Approach:**
- ✅ Parallel execution of both servers
- ✅ Resource isolation and easy monitoring  
- ✅ Quick server restarts without interrupting Claude Code
- ✅ Separate logs for backend/frontend debugging

### Python Backend (WSL - Terminal 2)
- **Virtual Environments Available:**
  - `.venv` - Python 3.11.9 environment with FastAPI, uvicorn, and web dependencies (RECOMMENDED for backend development)
  - `.venv38` - Python 3.8.0 environment with Power BI analysis tools (langchain, pyadomd, msal - used for PBI scanning)
- Use `.venv/Scripts/python.exe` for running FastAPI backend and API scripts in WSL
- Use `.venv38/Scripts/python.exe` for running Power BI scanning and analysis scripts
- Remember you are working in a Windows WSL emulation

**Start Backend Server (Terminal 2):**
```bash
cd /mnt/c/codebase/power-bi-catalog
.venv/Scripts/python.exe -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### React Frontend (WSL - Terminal 3)
- **Best Practice 2025**: Run React frontend in WSL2 for optimal performance and hot reload
- **Why WSL2**: 20x faster builds, proper file watching, consistent development environment
- **Network Configuration**: Vite configured with `host: '0.0.0.0'` for Windows browser access

**Start Frontend Server (Terminal 3):**
```bash
cd /mnt/c/codebase/power-bi-catalog/frontend
npm install  # if needed
npm run dev
```

**Access Points:**
- **Backend API**: `http://localhost:8000` (Swagger docs: `http://localhost:8000/docs`)
- **Frontend App**: `http://localhost:5173`
- **Both accessible from Windows browser**

## Current State (as of July 2025)
- This is an MVP/prototype.
- **Frontend**: React app with configuration UI and sidebar navigation ✅
- **Backend**: Python module/script that scans Power BI assets, extracts metadata, and writes to SQLite
- **Missing**: FastAPI backend to connect frontend to Python scanning logic
- **Goal**: Complete the FastAPI backend to bridge React frontend with existing Python Power BI scanning functionality