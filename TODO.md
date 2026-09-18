# Polls Lab — Project Roadmap & Progress Tracker

This document tracks all tasks, deliverables, and implementation phases according to the [PRD](poll-leaderboard-prd.md). It is continuously updated as tasks are completed.

---

## 📊 Overall Progress

- **Phase 1: Setup & Scaffolding** — **100%** (Completed)
- **Phase 2: Database Layer (PocketBase)** — **100%** (Completed)
- **Phase 3: Backend API & Security (FastAPI)** — **100%** (Completed & Reviewed)
- **Phase 4: Embeddable Widgets (Svelte & SVG)** — **100%** (Completed & Reviewed)
- **Phase 5: Frontend Web & Dashboard (Astro + React)** — **100%** (Completed & Standards/Spec Hardened)
- **Phase 6: Testing, Polish & Documentation** — **100%** (Completed)
- **Phase 7: Custom Poll Themes** — **100%** (Completed)
- **Phase 8: Production Deployment (Dokploy & Docker)** — **100%** (Live in Production)

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
  - [x] Issue `polls-lab_device_token` httpOnly cookie and return token in response
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
- [x] Multi-Framework Isolation (`AGENTS.md § 6`): Svelte 5 strictly confined to `/embed` with marketing hero and standalone poll pages embedding via isolated iframe (`<iframe src="/embed?id=..." />`)
- [x] Centralized URL configuration (`src/lib/config.ts`) and embed snippets / clipboard logic (`src/lib/embed.ts`) eliminating shotgun surgery and code duplication across 7+ files
- [x] Landing page (`/`) with isolated embed iframe preview, dynamic embed generator, and technical architecture benchmarks
- [x] Public Leaderboard (`/leaderboard`) with live API queries (`/trending`, `/top`), search filter, and dynamic embed dialog
- [x] Standalone poll pages (`/polls/[id]` and runtime dynamic `/polls?id=...`) with isolated voting embed and instant badge generator
- [x] Isolated iframe embed route (`/embed/[id]` and dynamic `/embed?id=...`) with `<15KB` bundle footprint (achieved **4.2KB** gzipped)
- [x] Dashboard console (`/dashboard`) with live API data fetch, Edit poll modal (`PATCH /api/v1/polls/{id}`), real poll deletion (`DELETE /api/v1/polls/{id}`), and real 7-day account deletion grace period dispatch (`POST /api/v1/auth/delete-account`)
- [x] Poll creator studio (`/dashboard/create`) with React 19, rich media options, 8-state tactile buttons, and live preview (fixed React `className` syntax)
- [x] Connect React `PollCreator` to FastAPI `/api/v1/polls` with moderation validation and token auth
- [x] Owner Analytics studio (`/dashboard/[id]/analytics`) with votes timeline histogram, option breakdown, embed referrer sources, authenticated blob downloads for CSV/JSON (`Authorization: Bearer`), and real error recovery state
- [x] Documentation & Playground (`/docs`) with interactive embed builder (SVG vs PNG vs Iframe), REST API reference cards, and self-hosting quickstart (scoped to PRD specs)
- [x] GitHub OAuth integration: sign-in/out navbar controls with auth state detection and callback handling route (`/auth/callback.astro`)
- [x] Astro View Transitions (`<ClientRouter />`) with directional cross-fades and tactile microinteractions
- [x] Verified mobile responsiveness across 320px–1440px with `overflow-x: clip` and 44px touch targets

---

## 🧪 Phase 6: Testing & Quality Assurance
- [x] Backend unit tests for content moderation (`test_moderation.py`)
- [x] Backend unit tests for IP hashing & rate limiting (`test_rate_limit.py`)
- [x] Backend integration tests for API endpoints, CORS, admin auth, & validation guards (`test_api_endpoints.py`) (20/20 passed)
- [x] Full static site build verification with 20 static routes (`corepack pnpm run build`)
- [x] Embed widget bundle footprint verification: **4.2 KB gzipped** (well below the `< 15KB` threshold)
- [x] Zero-tolerance secret hygiene verification: clean `git diff` with zero tracked secrets
- [x] Agent memory file (`memory.md`) created for fast onboarding and context handoff
- [x] End-to-end integration with frontend & PocketBase running concurrently
- [x] Verify SEO meta tags and social open-graph previews

---

## 🎨 Phase 7: Custom Poll Themes (Telegram / WhatsApp / Instagram / YouTube styles + user customization)
- [x] Phase 1 — Data model: `PollAppearance` Pydantic schema (theme, bg/accent/ink hex, radius, font, effect, layout) with server-side validation, `appearance` JSON field migration (`1789638852_poll_appearance.js`, field `ugvszf94`), create/update/response endpoint wiring with legacy-None fallback, 9 new tests (29/29 pass)
- [x] Phase 2 — Preset theme pack in widget (minimal/whatsapp/telegram/story/youtube-grid via data-theme + CSS vars, radius/font hooks, grid layout, data-effect hook for Phase 6, gzip 4.9KB < 15KB, live PB→API appearance round-trip verified) + fixed pre-existing 0-byte JSON write block (options 20000 / appearance 5000)
- [x] Phase 3 — Creator studio theme picker (5 preset cards) + customizer (bg/accent/ink pickers with hex validation, corners, font, layout, confetti toggle), theme-aware simulated preview, appearance POST, live widget iframe in success modal
- [x] Phase 4 — Image uploads (`POST /polls/{id}/images` + PB file storage) + YouTube-style grid layout
- [x] Phase 5 — Behaviors: multiple answers, quiz mode, visible voters (60 tests pass, 915-line widget, PollCreator toggles, PB migration `1789641000_behaviors.js`, pb_schema.json synced)
- [x] Phase 6 — Hand-rolled confetti celebration + docs + bundle verification

---

## 🚢 Phase 8: Production Deployment (Dokploy & Docker)
- [x] Multi-stage Dockerfile for Astro frontend with `node:22-alpine` and static Nginx serving
- [x] Lightweight Python 3.12 slim Dockerfile for FastAPI backend with unprivileged user & healthchecks
- [x] Alpine-based PocketBase Dockerfile with auto-applied migrations and persistent volume mount
- [x] Production Docker Compose orchestration for local & VPS setups
- [x] Template `.env.production.example` for secure secret management
- [x] Frontend, Backend, and Database live deployment verified on Dokploy


---

## 🔐 Phase 9: Backend Security & Spec-Conformance Remediation
Two-axis review (standards vs. PRD) of the whole FastAPI backend, then remediation. 72 tests pass.

### Critical — authentication
- [x] Verify auth tokens with PocketBase (`pb.verify_user_token` → `/api/collections/users/auth-refresh`) instead of base64-decoding the JWT payload. A forged unsigned token previously resolved to any user id, making every ownership check decorative
- [x] Remove hardcoded admin fallback key `"polls-lab-admin-secret"`; administrative endpoints now require `ADMIN_API_KEY` and are disabled when it is unset, compared with `secrets.compare_digest`
- [x] Remove published default `IP_HASH_SALT`; production refuses to start without a salt, development generates an ephemeral per-process one
- [x] Gate the `x-dev-user-id` shortcut behind `ALLOW_DEV_AUTH_HEADERS` (default off, rejected in production)
- [x] Default `ENVIRONMENT=production` in `backend/Dockerfile` so an image deployed without it fails closed
- [x] Regression suite `tests/test_auth_security.py` (11 tests) covering token forgery, admin key, and fail-closed startup

### Deployment config
- [x] Fix env var name mismatch: compose exported `SECRET_SALT`/`ALLOWED_ORIGINS`, backend read `IP_HASH_SALT`/`BACKEND_CORS_ORIGINS`. Canonical names now used, old names accepted as aliases
- [x] Pin all backend dependencies to exact versions; drop unused `pocketbase` SDK (service uses raw `httpx`)

### Abuse mitigation & privacy
- [x] Device token precedence: server-issued cookie/header now wins over the request body, which allowed unlimited voting via per-request token rotation
- [x] Bound rate-limiter memory (sweep + `MAX_TRACKED_IPS`); documented that it is per-worker, not a global quota
- [x] Stop leaking raw PocketBase error text to clients (logged server-side instead)
- [x] Whitelist poll `sort` fields; previously passed through to PocketBase unsanitized
- [x] Escape CSV formula injection via client-supplied `embed_referrer` in analytics export

### PRD §3.2 result-display masking
- [x] `show_counts` reveals raw counts only after the viewer has voted; `/polls/{id}` detects this via the device token
- [x] Badges mask raw counts for `show_percentage` polls (previously emitted `62% (418)`)
- [x] `/leaderboard/most-voted-options` excludes polls that mask counts rather than republishing them

### Correctness
- [x] Fix multi-select double-count: repeat votes update the existing record and count only newly added options
- [x] Fix `TypeError: unhashable type: 'list'` crashing analytics and export on every multi-select poll
- [x] Rewrite moderation filter: topic words (`hate`, `spam`, `crypto`) no longer rejected; profanity matched on whole words, scam solicitation on phrases
- [x] Trending keyed on `updated` (vote activity) rather than `created`, so surging older polls trend
- [x] Purge deletes owned polls before the user record, since `polls.owner` is not a cascading relation and they were orphaned
- [x] Expose `deletion_status`/`deletion_scheduled_for` on `/auth/me`; previously written but never read back

### Standards (AGENTS.md §4)
- [x] Replace `File(...)` ellipsis default with `Annotated[UploadFile, File()]`
- [x] Add `ConfigDict` to `VoteRequest` and type its validator
- [x] Validate export `format` as `Literal["json","csv"]` without shadowing the builtin
- [x] Remove dead code (`has_device_voted`, `list_voters_for_poll`, unused `pb=None` param); unify client timeout; move `PurgeResponse` to `app/schemas/`

### Known remaining gaps (not addressed)
- [ ] SPDX headers in source files (PRD §9) — 0 of 22 backend modules have one
- [ ] No scheduler invokes `/auth/purge-expired-accounts`; the 7-day lifecycle needs a cron trigger
- [ ] `show_voters` is non-functional (always returns `[]`); the PRD defers it, so it was left inert rather than built out
- [ ] Rate limiting is per-worker in-memory; a strict global quota needs Redis

---

## 🖥️ Phase 10: Frontend Rebuild (developer-tool dense) + Real OAuth
Full front-end rebuild in a mono-forward, data-dense direction, plus the auth wiring the
hardened backend requires. 27 pages build clean; embed widget 6.7 KB gzipped (budget 15 KB).

### Auth (was fully broken against the hardened API)
- [x] Real PocketBase GitHub OAuth2 with PKCE (`src/lib/auth.ts`). The callback previously
  fabricated a token from the OAuth code prefix (`github_${code.slice(0,16)}`), which the
  backend now rejects; every dashboard call also sent `x-dev-user-id`, disabled by default
- [x] `/auth/callback` exchanges the code with PocketBase, stores the signed token, and reports
  precise setup failures (provider not enabled, callback URL mismatch, replayed link)
- [x] Removed every `dev-user-local` fallback and `x-dev-user-id` header from the frontend
- [x] Signed-out gates on `/dashboard` and `/dashboard/create` instead of forms that cannot submit
- [x] 401 responses clear the session so the UI cannot loop on a dead token

### Logic layer
- [x] Typed API client (`src/lib/api.ts`) covering polls, votes, leaderboard, analytics, export,
  auth and image upload. Returns a tagged result union; every caller renders an error state
- [x] Loading, error, empty and unauthenticated states on every data-backed page
- [x] Added `/dashboard/analytics?id=<id>`: the SSG `[id]` route 404s for polls created after the
  last build, so the dashboard now links to a route that resolves any id
- [x] Analytics export keeps the authenticated fetch + blob download (needs an auth header)
- [x] Pending-deletion notice on the dashboard, reading the `deletion_status` now exposed by `/auth/me`
- [x] Footer API links resolve through `getApiUrl()`; they were hardcoded to `localhost:8000`

### Design system
- [x] `src/styles/tokens.css`: OKLCH palette, 4pt spacing, type scale, one radius scale, three
  easings. No component inlines a raw colour
- [x] Tailwind v4 `@theme inline` bridge so utilities consume the same tokens
- [x] Terminal theme (dark paper, mono display, phosphor accent), Workbench macrostructure,
  N8 terminal-command nav, Ft4 dense colophon footer
- [x] Buttons and inputs carry all eight states; focus rings show instantly and are never animated
- [x] Tabular numerals everywhere; hairline rules replace card boxes

### Pages rebuilt
- [x] `/` Workbench fold pairing the copyable snippet with the live widget, then three copy
  surfaces, a guarantees spec sheet, a verb-labelled flow, and a typographic close
- [x] `/polls` Index-First list with sort, pagination and a `?id=` resolver
- [x] `/polls/[id]` poll page with embed sidebar
- [x] `/leaderboard` three ranked tables behind one WAI-ARIA tab strip with arrow-key navigation
- [x] `/docs` Component Playground with a working embed builder and live badge preview
- [x] `/dashboard` owner list with embed, edit and delete dialogs replacing `confirm()`/`alert()`
- [x] `/theme-samples` now previews the five real poll themes; it was a self-labelled scratch
  sampler showing site design directions that were never product themes
- [x] `/embed` and `/embed/[id]` kept chrome-free and React-free (Svelte island only)
- [x] Accessibility: skip link, labelled controls, `aria-live` regions, 44px hit targets on mobile,
  reduced-motion honoured, text alternative for the analytics bar chart
- [x] No em-dashes in visible copy, per repo style

### Known remaining gaps
- [ ] The dashboard can only list **public** polls. `GET /polls` filters to `visibility="public"`
  and there is no owner-scoped listing, so private polls work but cannot be listed. Needs a
  backend endpoint (e.g. `GET /polls/mine`); the page states this rather than implying completeness
- [ ] GitHub OAuth must be enabled in the PocketBase admin UI, with the OAuth app's callback set
  to `<site>/auth/callback`, before sign-in works
- [ ] `PollCreator.tsx` keeps its original Tailwind styling; only its auth calls were rewritten.
  Restyling it to the token system is still open
