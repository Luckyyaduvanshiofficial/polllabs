# PollLabs — Self-Hosting Guide

This guide walks through deploying a self-hosted instance of PollLabs using Docker, commodity VPS, or bare-metal Linux.

---

## 🏗️ Architecture Overview

PollLabs consists of three core components:
1. **PocketBase** (`:8090`): Embedded SQLite database, OAuth2 provider, and file store.
2. **FastAPI Backend** (`:8000`): Rate-limiting proxy, abuse mitigation engine, and REST API.
3. **Astro Frontend** (`:4321`): Server/static frontend, Svelte embed widgets (< 15KB), and React management dashboard.

---

## ⚙️ Environment Configuration

Create a `.env` file in the project root:

```env
# PocketBase Service
POCKETBASE_URL=http://127.0.0.1:8090
POCKETBASE_ADMIN_EMAIL=admin@example.com
POCKETBASE_ADMIN_PASSWORD=change_this_strong_password

# FastAPI Backend
API_V1_STR=/api/v1
PROJECT_NAME=PollLabs API
VERSION=0.1.0
ENVIRONMENT=production
FRONTEND_URL=https://polls.yourdomain.com
BACKEND_CORS_ORIGINS=["https://polls.yourdomain.com"]

# Security & Abuse Mitigation
IP_HASH_SALT=generate_a_random_32_byte_hex_salt_here
VOTE_RATE_LIMIT_PER_MINUTE=30
```

---

## 🚀 Deployment Steps

### 1. Run PocketBase
```bash
cd database
./pocketbase serve --http="127.0.0.1:8090" --migrationsDir="./pb_migrations"
```
On first launch, navigate to `http://127.0.0.1:8090/_/` and create your admin account matching `.env`.

### 2. Run FastAPI Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Build & Serve Frontend
```bash
cd frontend
corepack pnpm install
corepack pnpm run build
node ./dist/server/entry.mjs
```

---

## 🔒 Security & Reverse Proxy (Nginx)

We recommend placing Nginx or Caddy in front of all services:

```nginx
server {
    server_name polls.yourdomain.com;

    # Frontend pages and embeds
    location / {
        proxy_pass http://127.0.0.1:4321;
        proxy_set_header Host $host;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # PocketBase Admin (restrict to trusted IPs)
    location /_/ {
        allow 10.0.0.0/8;
        deny all;
        proxy_pass http://127.0.0.1:8090;
    }
}
```

---

## 🪂 Fly.io Deployment (Alternative Deployment Path)

Fly.io provides an alternative single-app deployment with persistent NVMe volumes for PocketBase SQLite (PRD §6):

### 1. Create Persistent Volume for PocketBase
```bash
fly volumes create pb_data --region iad --size 1
```

### 2. Configure `fly.toml`
```toml
app = "polllabs"
primary_region = "iad"

[mounts]
  source = "pb_data"
  destination = "/pb_data"

[env]
  POCKETBASE_URL = "http://127.0.0.1:8090"
  API_V1_STR = "/api/v1"
  ENVIRONMENT = "production"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1

[[services.ports]]
  handlers = ["http"]
  port = 80

[[services.ports]]
  handlers = ["tls", "http"]
  port = 443
```

### 3. Deploy
```bash
fly secrets set POCKETBASE_ADMIN_PASSWORD="your-strong-password" IP_HASH_SALT="your-random-salt"
fly deploy
```
