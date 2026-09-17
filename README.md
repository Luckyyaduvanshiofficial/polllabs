# Polls Lab

> Embeddable polls, live SVG badges, and public leaderboards for developer communities.

[![Which web framework is your team prioritizing in 2026?](https://YOUR_API_URL/api/v1/badges/demo-frameworks.svg)](https://YOUR_FRONTEND_URL/polls/demo-frameworks)

> **Note:** Replace `YOUR_API_URL` and `YOUR_FRONTEND_URL` with your deployed URLs. See [Self-Hosting Guide](docs/self-hosting.md) for deployment options.

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

## Embed a Poll

### GitHub README (SVG Badge)
GitHub renders SVG badges that link to your poll page:

```markdown
[![Poll Title](https://YOUR_API_URL/api/v1/badges/POLL_ID.svg)](https://YOUR_FRONTEND_URL/polls/POLL_ID)
```

### Website / Blog (Interactive Iframe)
Embed a fully interactive voting widget:

```html
<iframe
  src="https://YOUR_FRONTEND_URL/embed?id=POLL_ID"
  width="400"
  height="340"
  frameborder="0"
></iframe>
```

### Markdown Blogs (Hugo, Astro, etc.)
```markdown
![Poll](https://YOUR_API_URL/api/v1/badges/POLL_ID.svg)
```

## License
Apache 2.0 - See [LICENSE](LICENSE) for details.
