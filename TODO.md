# PollLabs — Project Roadmap & Progress Tracker

This document tracks all tasks, deliverables, and implementation phases according to the [PRD](poll-leaderboard-prd.md). It is continuously updated as tasks are completed.

---

## 📊 Overall Progress

- **Phase 1: Setup & Scaffolding** — **100%** (Completed)
- **Phase 2: Database Layer (PocketBase)** — **100%** (Completed)
- **Phase 3: Backend API & Security (FastAPI)** — **25%** (Up Next)
- **Phase 4: Embeddable Widgets (Svelte & SVG)** — **25%** (In Progress)
- **Phase 5: Frontend Web & Dashboard (Astro + React)** — **30%** (In Progress)
- **Phase 6: Testing, Polish & Documentation** — **0%**

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
- [x] Configure collection API Rules (public read for public polls, owner-only edit/delete, anonymous vote submission)
- [x] Export schema to `database/pb_schema.json`
- [x] Add PocketBase migration scripts in `database/pb_migrations/1789619075_init_schema.js`

---

## ⚡ Phase 3: Backend API & Abuse Mitigation (FastAPI)
- [x] Setup FastAPI core with CORS, OpenAPI docs, and lifespan context manager
- [x] Implement IP hashing and sliding-window rate limiter (`rate_limit.py`)
- [x] Align schemas and endpoints with Pydantic v2 (no ellipsis, ConfigDict, return types, status constants)
- [ ] GitHub OAuth authentication flow (sign-in required for poll creators)
- [ ] Poll CRUD endpoints (`/api/v1/polls`):
  - [ ] `POST /` — Create poll (owner-authenticated, profanity filtered)
  - [ ] `GET /` — List public polls
  - [ ] `GET /{id}` — Get single poll details
  - [ ] `PATCH /{id}` — Edit poll (owner-only)
  - [ ] `DELETE /{id}` — Delete poll (owner-only)
- [ ] Voting endpoint (`/api/v1/votes/{poll_id}`):
  - [x] Rate limit check (IP hash with `HTTP_429_TOO_MANY_REQUESTS`)
  - [ ] Device token validation (one vote per voter per poll)
  - [ ] Record vote in PocketBase
- [ ] Public leaderboard endpoint (`/api/v1/leaderboard`):
  - [ ] Trending / top voted queries (filtered to `public` visibility)
- [ ] Owner Analytics endpoints (`/api/v1/analytics/{poll_id}`):
  - [ ] Timeline of votes
  - [ ] Option breakdown & percentages
  - [ ] Referrer / embed sources breakdown
  - [ ] Raw export in CSV and JSON formats
- [x] Dynamic SVG badge generation (`/api/v1/badges/{poll_id}.svg`) with cache headers
- [ ] Account deletion request with 7-day grace period (§7)

---

## 🧩 Phase 4: Embeddable Deliverables
- [x] Prototype Svelte embed widget (`PollWidget.svelte`)
- [ ] Refine embed widget to guarantee `< 15KB` gzipped bundle footprint
- [ ] Support text, emoji, and image options in embed
- [ ] Result display modes (`show_counts`, `show_percentage`, `hidden_until_close`)
- [ ] Graceful "This poll is no longer available" fallback state
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
- [ ] Add Owner Analytics page (`/dashboard/[id]/analytics`) with charts & export buttons
- [ ] Build documentation pages (`/docs`) with copyable embed snippets & API reference
- [ ] GitHub login integration button in navbar & auth guard for dashboard

---

## 🧪 Phase 6: Testing & Quality Assurance
- [ ] Backend unit & integration tests with `pytest`
- [ ] Test vote abuse prevention (duplicate device tokens & IP flooding)
- [ ] Verify CORS rules (open for votes & badges, restricted for management)
- [ ] Verify SEO meta tags and social open-graph previews
