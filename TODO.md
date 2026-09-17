# PollLabs — Project Roadmap & Progress Tracker

This document tracks all tasks, deliverables, and implementation phases according to the [PRD](poll-leaderboard-prd.md). It is continuously updated as tasks are completed.

---

## 📊 Overall Progress

- **Phase 1: Setup & Scaffolding** — **100%** (Completed)
- **Phase 2: Database Layer (PocketBase)** — **100%** (Completed)
- **Phase 3: Backend API & Security (FastAPI)** — **100%** (Completed & Reviewed)
- **Phase 4: Embeddable Widgets (Svelte & SVG)** — **100%** (Completed)
- **Phase 5: Frontend Web & Dashboard (Astro + React)** — **100%** (Completed & Redesigned from Scratch)
- **Phase 6: Testing, Polish & Documentation** — **90%** (In Progress)

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
- [x] Create `abuse_reports` collection:
  - Fields: `poll_id` (relation to `polls` with `cascadeDelete: true`), `reason`, `ip_hash`
  - Index: `idx_abuse_poll` (`poll_id`)
- [x] Configure collection API Rules (locked `votes.createRule` to enforce FastAPI backend checks)
- [x] Configure `users` collection to GitHub OAuth only (PRD §2) with account deletion lifecycle fields (`deletion_status`, `deletion_scheduled_for`)
- [x] Export schema to `database/pb_schema.json`
- [x] Add PocketBase migration scripts in `database/pb_migrations/1789619075_init_schema.js`

---

## ⚡ Phase 3: Backend API & Abuse Mitigation (FastAPI)
- [x] Setup FastAPI core with scoped CORS (PRD §4.7) and OpenAPI docs (`/docs`)
- [x] Implement IP hashing and sliding-window rate limiter (`rate_limit.py`)
- [x] Align schemas and endpoints with Pydantic v2 (no ellipsis, ConfigDict, return types, status constants)
- [x] GitHub OAuth authentication endpoints (`/api/v1/auth/github/url`, `/api/v1/auth/me`)
- [x] Account deletion request with 7-day grace period lifecycle (`/auth/delete-account`, `/auth/cancel-delete-account`, `/auth/purge-expired-accounts`)
- [x] Content moderation & profanity filtering service (`moderation.py`)
- [x] Asynchronous PocketBase service (`pocketbase_service.py`) with connection pooling, automatic vote pagination, and atomic increments
- [x] Poll CRUD endpoints (`/api/v1/polls`):
  - [x] `POST /` — Create poll (owner-authenticated, profanity filtered, supports text, emoji, images)
  - [x] `GET /` — List public polls (with pagination, sort, and result display formatting)
  - [x] `GET /{id}` — Get single poll details (respects `show_counts`, `show_percentage`, `hidden_until_close`; unmasked for owner)
  - [x] `PATCH /{id}` — Edit poll (owner-only authorization)
  - [x] `DELETE /{id}` — Delete poll (owner-only authorization)
  - [x] `POST /{id}/report` — Report abuse on public polls with persistent storage
- [x] Voting endpoint (`/api/v1/votes/{poll_id}`):
  - [x] Rate limit check (IP hash with `HTTP_429_TOO_MANY_REQUESTS`)
  - [x] Device token validation (prevents duplicate voting; supports cookie, header, and localStorage fallback)
  - [x] Concurrency-safe atomic vote increment in PocketBase (`total_votes+`)
  - [x] Issue `polllabs_device_token` httpOnly cookie and return token in response
  - [x] Respect result display masking so voter responses do not leak counts
- [x] Public leaderboard endpoint (`/api/v1/leaderboard`):
  - [x] Trending polls query (`/trending`)
  - [x] Top polls query (`/top`)
  - [x] Most-voted options query (`/most-voted-options`)
- [x] Owner Analytics endpoints (`/api/v1/analytics/{poll_id}`):
  - [x] Timeline of votes (`votes_over_time`)
  - [x] Option breakdown & percentages
  - [x] Referrer / embed sources breakdown
  - [x] Raw export in valid CSV and JSON formats (`/export`)
- [x] Dynamic SVG & PNG badge generation (`/api/v1/badges/{poll_id}.svg`, `/{poll_id}.png`) with live interactive link & graceful fallback
- [x] Comprehensive Pytest suite with 20 passing unit and integration tests
- [x] Self-hosting deployment guide (`docs/self-hosting.md`) and contributing guide (`CONTRIBUTING.md`)

---

## 🧩 Phase 4: Embeddable Deliverables
- [x] Prototype Svelte embed widget (`PollWidget.svelte`)
- [x] Refactor Svelte 5 embed widget with modern Runes (`$props`, `$state.raw`, `$derived`, `{#snippet}`)
- [x] Dynamic SVG & PNG badge generator (`/api/v1/badges/{poll_id}.svg`, `/{poll_id}.png`) with leading option breakdown, `hidden_until_close` masking, live clickable link & fallback
- [x] Guarantee `< 15KB` gzipped bundle footprint (achieved **4.2KB** gzipped!)
- [x] Support text, emoji, and image options in embed with snippet deduplication
- [x] Result display modes (`show_counts`, `show_percentage`, `hidden_until_close`)
- [x] Scoped CORS middleware reflecting `Origin` with `Access-Control-Allow-Credentials: true` and `X-Device-Token`
- [x] One-vote-per-voter enforcement via cookie + `localStorage` fallback
- [x] Inline abuse reporting trigger (`POST /api/v1/polls/{id}/report`)
- [x] Dynamic iframe embed pages in Astro (`/embed/[id]` and `/embed/?id=<poll_id>`)
- [x] Admin-protected expired account purge (`POST /api/v1/auth/purge-expired-accounts`)
- [x] Trending polls query with 7-day velocity window
- [x] Fly.io deployment guide with SQLite NVMe persistent volume setup (`docs/self-hosting.md`)
- [x] Verify static SVG badge rendering for GitHub markdown / READMEs

---

## 🖥️ Phase 5: Frontend Web & Dashboard (Astro + React)
- [x] Redesigned from Scratch with UI/UX Pro Max, Frontend Design, Hallmark, and React 19 standards
- [x] Obsidian & Slate developer design system tokens in `global.css` with JetBrains Mono & Inter fonts
- [x] Landing page (`/`) with live interactive Svelte 5 demo, real-time embed generator, and technical architecture benchmarks
- [x] Public Leaderboard (`/leaderboard`) with Trending (7-day velocity), Top All-Time, Most-Voted Options, and search filter
- [x] Standalone poll page (`/polls/[id]`) with live voting widget, embed snippet generator, and clipboard copy
- [x] Isolated iframe embed route (`/embed/[id]`) and standalone embed route (`/embed`)
- [x] Dashboard console (`/dashboard`) with stats bar, poll cards, embed code dialog, and account deletion grace period management
- [x] Poll creator studio (`/dashboard/create`) with React 19, rich media options, 8-state tactile buttons, and live side-by-side preview
- [x] Connect React `PollCreator` to FastAPI `/api/v1/polls` with moderation validation and token auth
- [x] Owner Analytics studio (`/dashboard/[id]/analytics`) with votes timeline histogram, option breakdown, embed referrer sources, and one-click CSV/JSON export
- [x] Documentation & Playground (`/docs`) with interactive embed builder (SVG vs PNG vs Iframe), REST API reference cards, and self-hosting quickstart
- [x] Astro View Transitions (`<ClientRouter />`) with directional cross-fades and tactile microinteractions
- [x] Verified mobile responsiveness across 320px–1440px with `overflow-x: clip` and 44px touch targets

---

## 🧪 Phase 6: Testing & Quality Assurance
- [x] Backend unit tests for content moderation (`test_moderation.py`)
- [x] Backend unit tests for IP hashing & rate limiting (`test_rate_limit.py`)
- [x] Backend integration tests for API endpoints, CORS, admin auth, & validation guards (`test_api_endpoints.py`) (20/20 passed)
- [x] Full static site build verification with 18 static routes (`corepack pnpm run build`)
- [x] Embed widget bundle footprint verification: **4.2 KB gzipped** (well below the `< 15KB` threshold)
- [ ] End-to-end integration with frontend & PocketBase running concurrently
- [ ] Verify SEO meta tags and social open-graph previews
