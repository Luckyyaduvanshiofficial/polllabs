# PollLabs — Agent Memory & Codebase Context

> **Last updated**: 2026-09-17 · **HEAD commit**: `c7f14b5` on `main`
> Read this file first before touching any code. It gives you the full context in ~5 minutes.

---

## 1. What Is This Project?

**PollLabs** is an embeddable polling platform. Users create polls, share them, embed them anywhere (GitHub READMEs, blogs, dashboards), and view live leaderboards & analytics.

Key deliverables per the [PRD](./poll-leaderboard-prd.md):
- Embeddable `<iframe>` widget (< 15KB gzipped, Svelte 5)
- Dynamic SVG/PNG badge for GitHub READMEs
- Public leaderboard with trending algorithm
- Owner analytics with CSV/JSON export
- GitHub OAuth authentication with 7-day account-deletion grace period
- Rate limiting, IP hashing, one-vote-per-device enforcement

---

## 2. Repository Layout

```
polllabs/
├── AGENTS.md              ← MANDATORY RULES — read before any code change
├── TODO.md                ← Progress tracker — MUST be updated after every task
├── poll-leaderboard-prd.md← Full product requirements document
├── memory.md              ← THIS FILE
├── CONTRIBUTING.md
├── backend/               ← FastAPI + Python 3.12
│   ├── .env               ← Real credentials (gitignored, never commit)
│   ├── .env.example       ← Placeholder template only
│   ├── .venv/             ← Python venv (gitignored)
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py              ← FastAPI app + lifespan + CORS
│   │   ├── core/
│   │   │   ├── config.py        ← Settings (reads .env)
│   │   │   ├── dependencies.py  ← PocketBaseDep, CurrentUser DI
│   │   │   └── rate_limit.py    ← Sliding-window IP rate limiter
│   │   ├── api/v1/
│   │   │   ├── router.py        ← Assembles all sub-routers
│   │   │   ├── polls.py         ← CRUD: GET/POST/PATCH/DELETE /polls
│   │   │   ├── votes.py         ← POST /votes/{poll_id}
│   │   │   ├── analytics.py     ← GET /analytics/{poll_id}[/export]
│   │   │   ├── badges.py        ← GET /badges/{poll_id}.svg|.png
│   │   │   ├── leaderboard.py   ← GET /leaderboard/trending|top|most-voted-options
│   │   │   ├── auth.py          ← GitHub OAuth, /me, /delete-account
│   │   │   └── health.py        ← GET /health
│   │   ├── schemas/             ← Pydantic v2 models (one file per domain)
│   │   └── services/
│   │       ├── pocketbase_service.py  ← Async PocketBase HTTP client
│   │       ├── moderation.py          ← Profanity filter
│   │       └── poll_utils.py          ← is_poll_closed() helper
│   └── tests/
│       ├── test_api_endpoints.py  ← 20 integration tests (all passing)
│       ├── test_moderation.py
│       └── test_rate_limit.py
├── database/
│   ├── pb_schema.json             ← Version-controlled schema (committed)
│   └── pb_migrations/
│       └── 1789619075_init_schema.js
│   (pb_data/ and binary are gitignored)
└── frontend/                      ← Astro static site
    ├── astro.config.mjs           ← output: "static", React + Svelte integrations
    ├── package.json               ← pnpm only (corepack pnpm)
    └── src/
        ├── styles/global.css      ← Design tokens (Obsidian/Slate), JetBrains Mono + Inter
        ├── layouts/Layout.astro   ← Base HTML shell + ClientRouter (View Transitions)
        ├── lib/
        │   ├── config.ts   ← getApiUrl(), getSiteUrl(), getPbUrl() — SINGLE SOURCE OF TRUTH
        │   └── embed.ts    ← getBadgeUrl(), getEmbedUrl(), getPollUrl(),
        │                      getMarkdownBadgeSnippet(), getIframeSnippet(), copyToClipboard()
        ├── components/
        │   ├── common/
        │   │   ├── Navbar.astro   ← Auth state detection, sign-in/out controls
        │   │   └── Footer.astro
        │   ├── dashboard/
        │   │   ├── PollCreator.tsx    ← React 19 — rich poll creation + live preview
        │   │   └── PollAnalytics.tsx  ← React 19 — charts, CSV/JSON authenticated export
        │   └── embed/
        │       └── PollWidget.svelte  ← Svelte 5 Runes — ONLY Svelte component in whole repo
        └── pages/                     ← Folder-based routing (1:1 with URLs)
            ├── index.astro            ← Landing page
            ├── auth/callback.astro    ← GitHub OAuth callback handler
            ├── leaderboard/index.astro
            ├── polls/
            │   ├── index.astro        ← Runtime /polls?id=... resolver
            │   └── [id]/index.astro   ← SSG standalone poll page
            ├── embed/
            │   ├── index.astro        ← Runtime /embed?id=... resolver
            │   └── [id]/index.astro   ← SSG embed page (loads PollWidget.svelte)
            ├── dashboard/
            │   ├── index.astro        ← Dashboard console (live polls, edit, delete)
            │   ├── create/index.astro ← Poll Creator (uses PollCreator.tsx)
            │   └── [id]/analytics/index.astro ← Analytics (uses PollAnalytics.tsx)
            └── docs/index.astro       ← API docs + embed builder playground
```

---

## 3. Critical Rules (from AGENTS.md — always re-read before coding)

| Rule | Requirement |
|------|-------------|
| **Secret hygiene** | NEVER commit credentials. `.env` is gitignored. `.env.example` uses placeholders only. Run `git diff` before every commit. |
| **TODO.md** | MUST update immediately after completing any task. |
| **Git** | Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`). Push to `origin main` after every change. |
| **Python venv** | Always use `backend/.venv/bin/python` / `backend/.venv/bin/pytest` |
| **Package manager** | `corepack pnpm` exclusively. Never `npm` or `yarn`. |
| **Multi-framework** | React → `/dashboard` only. Svelte 5 → `/embed` only (< 15KB). Everything else → pure Astro. |
| **Pydantic v2** | No `...` as default. Use `Field(min_length=...)`. `model_config = ConfigDict(from_attributes=True)`. `str | None` not `Optional[str]`. |
| **FastAPI** | `async def` for I/O, `def` for CPU. `Annotated[T, Depends(...)]`. `status.HTTP_*` constants. |

---

## 4. Key Design Decisions & Patterns

### Auth
- Dev mode: token stored in `localStorage` key `polllabs_auth_token`
- Request headers: `Authorization: Bearer <token>` + `x-dev-user-id: <token>`
- Production: real PocketBase JWT via GitHub OAuth
- OAuth flow: `GET /api/v1/auth/github/url` → GitHub → `GET /auth/callback` (Astro page stores token)

### PollWidget.svelte (Svelte 5 Runes)
- Reads poll ID from: (1) `pollId` prop, (2) `?id=` query param, (3) URL path segment
- Uses `$props()`, `$state.raw()`, `$derived()`, `{#snippet}` — strict Runes mode
- `apiBase` defaults to `http://localhost:8000` if no prop provided
- Gzipped bundle: **4,252 bytes (4.15 KB)** — well under 15KB limit

### BadgeData Dataclass (badges.py)
- `@dataclass(frozen=True)` with fields: `label`, `value`, `is_error`, `target_url`
- Implements `__iter__` → `(label, value, is_error, target_url)` for backward-compatible tuple unpacking
- `target_url` points to `/polls/{poll_id}` per PRD §4.4 (NOT `/embed/`)

### URL Helpers
- `getApiUrl()` → reads `PUBLIC_API_URL` env var, falls back to `http://localhost:8000`
- `getSiteUrl()` → reads `window.location.origin` (client) or `PUBLIC_SITE_URL` env var
- `getEmbedUrl(id)` → always `/embed?id=<id>` (query param, NOT path — avoids SSG 404)
- `getPollUrl(id)` → `/polls/<id>`
- Badge markdown: `[![title](badge.svg)](site/polls/id)` — links to `/polls/` NOT `/embed/`

### Multi-Framework Isolation
- Marketing pages embed the Svelte widget via `<iframe src="/embed?id=...">` NOT `<PollWidget client:load />`
- Svelte 100% isolated to `/embed` routes only

### Analytics Export
- Authenticated `fetch` + blob download (NOT `<a href download>`)
- Sends `Authorization: Bearer <token>` header

---

## 5. Running the Project Locally

```bash
# 1. Start PocketBase (from project root)
./database/pocketbase serve --dir ./database/pb_data

# 2. Start Backend (FastAPI)
backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8000

# 3. Start Frontend (Astro dev)
corepack pnpm --dir frontend dev

# 4. Run Tests
backend/.venv/bin/pytest backend/tests   # → 20/20 pass

# 5. Build Frontend (static)
corepack pnpm --dir frontend run build   # → 20 pages
```

---

## 6. Progress Summary

### ✅ Completed (Phases 1–5 + most of Phase 6)

| Phase | Status | Key Commits |
|-------|--------|-------------|
| Phase 1: Setup & Scaffolding | ✅ 100% | `1b6515e`, `3ea05fd` |
| Phase 2: PocketBase Schema | ✅ 100% | `bfe6225` |
| Phase 3: FastAPI Backend | ✅ 100% | `8630bb5`, `ceb2c7b`, `522fd84` |
| Phase 4: Svelte Embed Widget | ✅ 100% | `b7b6534`, `87eb897` |
| Phase 5: Astro Frontend | ✅ 100% | `d830125`, `6ca526f` |
| Phase 6: Testing & QA | 🔄 95% | `6ca526f` |

### 🔄 Remaining Work

```
[ ] End-to-end integration test: run PocketBase + backend + frontend concurrently
    and exercise all major flows (vote, create poll, view leaderboard, export CSV)
[ ] Verify SEO meta tags and social open-graph preview tags on all pages
```

---

## 7. Database Schema Summary (PocketBase)

| Collection | Key Fields | Notes |
|-----------|-----------|-------|
| `users` | GitHub OAuth fields, `deletion_status`, `deletion_scheduled_for` | GitHub OAuth only |
| `polls` | `title`, `description`, `options (json)`, `visibility (select)`, `result_display (select)`, `close_at`, `owner (relation→users)` | Indexed: `visibility+created`, `owner` |
| `votes` | `poll_id (relation→polls, cascadeDelete)`, `option_id`, `device_token`, `ip_hash`, `embed_referrer` | Indexed: `poll_id`, `poll_id+device_token`, `poll_id+ip_hash` |
| `abuse_reports` | `poll_id (relation→polls, cascadeDelete)`, `reason`, `ip_hash` | Indexed: `poll_id` |

---

## 8. Environment Variables

### Backend `.env` (gitignored — real values locally only)
```
POCKETBASE_URL=http://127.0.0.1:8090
POCKETBASE_ADMIN_EMAIL=admin@example.com   ← placeholder in .env.example
POCKETBASE_ADMIN_PASSWORD=change_this      ← placeholder in .env.example
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_secret
SECRET_SALT=your-secret-salt
ALLOWED_ORIGINS=http://localhost:4321
```

### Frontend (Astro public env)
```
PUBLIC_API_URL=http://localhost:8000
PUBLIC_SITE_URL=http://localhost:4321
PUBLIC_PB_URL=http://localhost:8090
```

---

## 9. Test Results (as of commit 6ca526f)

```
backend/.venv/bin/pytest backend/tests  →  20 passed
corepack pnpm --dir frontend run build  →  20 pages built cleanly
gzip PollWidget.*.js | wc -c            →  4,252 bytes (4.15 KB) < 15KB ✅
git diff                                →  zero secrets ✅
```

---

## 10. Known Gotchas

1. **`getEmbedUrl(id)` returns `/embed?id=<id>`** (query param), NOT `/embed/<id>` (path). This avoids SSG 404s.
2. **Svelte poll ID resolution order**: prop `pollId` → `?id=` query param → URL path segment. Never break this chain.
3. **`BadgeData.__iter__`** returns `(label, value, is_error, target_url)` — do NOT reorder fields.
4. **Analytics export** uses `fetch` + blob + `Authorization: Bearer` — NOT a plain `<a href download>`.
5. **CORS**: Backend reflects `Origin` with `Allow-Credentials: true`, exposes `X-Device-Token`. Changing CORS breaks embed iframe voting.
6. **PocketBase binary** is gitignored. Download separately. Run from `database/` directory.
7. **View Transitions**: `<ClientRouter />` is in `Layout.astro`. All page navigations use cross-fade.
8. **Dev auth**: `localStorage.polllabs_auth_token` stores the token. Navbar script reads this to show/hide Sign In/Out.
