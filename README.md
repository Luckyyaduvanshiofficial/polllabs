# PollLabs

[![Which web framework is your team prioritizing in 2026?](http://localhost:8000/api/v1/badges/demo-frameworks.svg)](http://localhost:4321/polls/demo-frameworks)

An open-source, lightweight platform for embeddable polls and leaderboards.

## Features
- **Embeddable Polls:** Renderable as static SVG badges (for GitHub READMEs) or interactive iframe widgets.
- **Folder-based Frontend:** Built on Astro with React for dashboard state and Svelte for ultra-lightweight embeds.
- **FastAPI Backend:** Secure, versioned REST API with built-in voter abuse mitigation (device tokens + IP-hash rate limiting).
- **PocketBase Persistence:** Single-binary database engine with embedded SQLite.

## Structure
- `frontend/` - Astro web application with folder-based routing (`/dashboard`, `/leaderboard`, `/embed/[id]`, `/docs`).
- `backend/` - FastAPI service (`/api/v1`) with Python 3.12 virtual environment.
- `database/` - Local PocketBase executable, migrations, and schema definitions.

## Quickstart

### 1. Database (PocketBase)
```bash
cd database
./pocketbase serve
```
Admin UI will be available at `http://127.0.0.1:8090/_/`.

### 2. Backend (FastAPI)
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at `http://127.0.0.1:8000/docs`.

### 3. Frontend (Astro)
```bash
cd frontend
npm run dev
```
Frontend will be available at `http://localhost:4321`.

## License
Apache 2.0 - See [LICENSE](LICENSE) for details.
