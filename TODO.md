# PollLabs — Project Roadmap & Progress Tracker

This document tracks all tasks, deliverables, and implementation phases according to the [PRD](poll-leaderboard-prd.md). It is continuously updated as tasks are completed.

---

## 📊 Overall Progress

- **Phase 1: Setup & Scaffolding** — **100%** (Completed)
- **Phase 2: Database Layer (PocketBase)** — **100%** (Completed)
- **Phase 3: Backend API & Security (FastAPI)** — **100%** (Completed & Reviewed)
- **Phase 4: Embeddable Widgets (Svelte & SVG)** — **60%** (Up Next)
- **Phase 5: Frontend Web & Dashboard (Astro + React)** — **40%** (In Progress)
- **Phase 6: Testing, Polish & Documentation** — **60%** (In Progress)

---

## 🚀 Phase 1: Project Setup & Baseline Scaffolding
- [x] Initialize Git repository and connect remote `origin main`
- [x] Create 3-pillar directory structure: `frontend/`, `backend/`, and `database/`
- [x] Configure Python 3.12 virtual environment in `backend/.venv` with required packages
- [x] Download, verify, and document PocketBase v0.22 binary in `database/`
- [x] Initialize Astro frontend with `pnpm`
- [x] Configure `@astrojs/react`, `@astrojs/svelte`, and Tailwind CSS v4
- [x] Set up folder-based routing structure in `frontend/src/pages/`
- [x] Document strict security & secret hygiene rules in `AGENTS.md`
- [x] Set up `.gitignore` to protect `.venv`, `node_modules`, `pb_data/`, and `.env`
- [x] Integrate FastAPI & PocketBase best practice standards into rulebook (`AGENTS.md`)

---

## 🗄️ Phase 2: Database Schema & Collections (PocketBase)
- [x] Create `polls` collection:
  - Fields: `title`, `description`, `options` (json), `visibility` (`public`/`private`), `result_display` (`show_counts`/`show_percentage`/`hidden_until_close`), `close_at`, `owner` (relation to users)
  - Indexes: `idx_polls_visibility` (`visibility, created`), `idx_polls_owner` (`owner`)
- [x] Create `votes` collection:
  - Fields: `poll_id` (relation to `polls` with `cascadeDelete: true`), `option_id`, `device_token`, `ip_hash`, `embed_referrer`
  - Indexes: `idx_votes_poll` (`poll_id`), `idx_votes_device_poll` (`poll_id, device_token`), `idx_votes_ip_poll` (`poll_id, ip_hash`)
- [x] Configure collection API Rules (locked `votes.createRule` to enforce FastAPI backend checks)
- [x] Configure `users` collection to GitHub OAuth only (PRD §2)
- [x] Export schema to `database/pb_schema.json`
- [x] Add PocketBase migration scripts in `database/pb_migrations/1789619075_init_schema.js`

---

## ⚡ Phase 3: Backend API & Abuse Mitigation (FastAPI)
- [x] Setup FastAPI core with scoped CORS (PRD §4.7) and OpenAPI docs
- [x] Implement IP hashing and sliding-window rate limiter (`rate_limit.py`)
- [x] Align schemas and endpoints with Pydantic v2 (no ellipsis, ConfigDict, return types, status constants)
- [x] GitHub OAuth authentication endpoints (`/api/v1/auth/github/url`, `/api/v1/auth/me`)
- [x] Account deletion request with 7-day grace period lifecycle (`/auth/delete-account`, `/auth/cancel-delete-account`)
- [x] Content moderation & profanity filtering service (`moderation.py`)
- [x] Asynchronous PocketBase service (`pocketbase_service.py`) with automatic vote pagination
- [x] Poll CRUD endpoints (`/api/v1/polls`):
  - [x] `POST /` — Create poll (owner-authenticated, profanity filtered, supports text, emoji, images)
  - [x] `GET /` — List public polls (with pagination, sort, and result display formatting)
  - [x] `GET /{id}` — Get single poll details (respects `show_counts`, `show_percentage`, `hidden_until_close`)
  - [x] `PATCH /{id}` — Edit poll (owner-only authorization)
  - [x] `DELETE /{id}` — Delete poll (owner-only authorization)
  - [x] `POST /{id}/report` — Report abuse on public polls
- [x] Voting endpoint (`/api/v1/votes/{poll_id}`):
  - [x] Rate limit check (IP hash with `HTTP_429_TOO_MANY_REQUESTS`)
  - [x] Device token validation (prevents duplicate voting by same voter)
  - [x] Record vote in PocketBase with option increment
  - [x] Issue `polllabs_device_token` httpOnly cookie
- [x] Public leaderboard endpoint (`/api/v1/leaderboard`):
  - [x] Trending polls query (`/trending` with engagement threshold)
  - [x] Top polls query (`/top`)
  - [x] Most-voted options query (`/most-voted-options`)
- [x] Owner Analytics endpoints (`/api/v1/analytics/{poll_id}`):
  - [x] Timeline of votes (`votes_over_time`)
  - [x] Option breakdown & percentages
  - [x] Referrer / embed sources breakdown
  - [x] Raw export in valid CSV and JSON formats (`/export`)
- [x] Dynamic SVG badge generation (`/api/v1/badges/{poll_id}.svg`) with "no longer available" graceful fallback
- [x] Comprehensive Pytest suite with 12 passing unit and integration tests

---

## 🧩 Phase 4: Embeddable Deliverables
- [x] Prototype Svelte embed widget (`PollWidget.svelte`)
- [x] Dynamic SVG badge generator (`/api/v1/badges/{poll_id}.svg`) with graceful "no longer available" fallback
- [ ] Refine embed widget to guarantee `< 15KB` gzipped bundle footprint
- [ ] Support text, emoji, and image options in embed
- [ ] Result display modes (`show_counts`, `show_percentage`, `hidden_until_close`)
- [ ] Verify static SVG badge rendering on GitHub markdown / READMEs

---

## 🖥️ Phase 5: Frontend Web & Dashboard (Astro + React)
- [x] Landing page (`/`) with live interactive demo
- [x] Leaderboard page route (`/leaderboard`)
- [x] Standalone poll page (`/polls/[id]`)
- [x] Isolated iframe embed route (`/embed/[id]`)
- [x] Dashboard page (`/dashboard`)
- [x] Poll creator page (`/dashboard/create`) with React component
- [ ] Connect React `PollCreator` to FastAPI `/api/v1/polls`
- [ ] Connect Svelte `PollWidget` to `/api/v1/votes/{poll_id}`
- [ ] Add Owner Analytics page (`/dashboard/[id]/analytics`) with charts & export buttons
- [ ] Build documentation pages (`/docs`) with copyable embed snippets & API reference
- [ ] GitHub login integration button in navbar & auth guard for dashboard

---

## 🧪 Phase 6: Testing & Quality Assurance
- [x] Backend unit tests for content moderation (`test_moderation.py`)
- [x] Backend unit tests for IP hashing & rate limiting (`test_rate_limit.py`)
- [x] Backend integration tests for API endpoints & validation guards (`test_api_endpoints.py`)
- [ ] End-to-end integration with frontend & PocketBase running concurrently
- [ ] Verify SEO meta tags and social open-graph previews
