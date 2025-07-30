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

## What NOT to do
- Don’t use any paid dependencies for MVP
- Don’t scaffold unused boilerplate

## Tasks AI Should Help With
- Scaffold backend models, endpoints, and DB migrations
- Generate TypeScript interfaces from backend models
- Build asset search and detail UI components
- Suggest test cases for API endpoints

## Current State (as of July 2025)
- This is an MVP/prototype.
- The code currently **does NOT have a frontend interface** and does **NOT use FastAPI**.
- The core logic is a Python module/script that scans Power BI assets, extracts metadata, and writes to a local database (likely SQLite or CSV).
- There is **no REST API** or user-facing UI at this stage.
- Goal: Evolve this codebase toward a full web application with FastAPI backend and React frontend, while keeping core scan logic modular and reusable.