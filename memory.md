# Polls Lab — Agent Memory & Codebase Context

> **Last updated**: 2026-09-17 · **HEAD commit**: `113be2f` on `main`
> Read this file first before touching any code. It gives you the full context in ~5 minutes.

---

## 1. What Is This Project?

**Polls Lab** is an embeddable polling platform. Users create polls, share them, embed them anywhere (GitHub READMEs, blogs, dashboards), and view live leaderboards & analytics.

Key deliverables per the [PRD](./poll-leaderboard-prd.md):
- Embeddable `<iframe>` widget (< 15KB gzipped, Svelte 5) with **5 visual themes**
- Dynamic SVG/PNG badge for GitHub READMEs
- Public leaderboard with trending algorithm
- Owner analytics with CSV/JSON export
- GitHub OAuth authentication with 7-day account-deletion grace period
- Rate limiting, IP hashing, one-vote-per-device enforcement
- **Poll behaviors**: multi-select, quiz mode, visible voters
- **Image options**: upload images per option (YouTube grid layout)
- **Canvas confetti** celebration on vote

---

## 2. Repository Layout

```
polls-lab/
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
│   │   │   ├── polls.py         ← CRUD + image upload + behaviors
│   │   │   ├── votes.py         ← POST /votes/{poll_id} with multi-select + quiz support
│   │   │   ├── analytics.py     ← GET /analytics/{poll_id}[/export]
│   │   │   ├── badges.py        ← GET /badges/{poll_id}.svg|.png
│   │   │   ├── leaderboard.py   ← GET /leaderboard/trending|top|most-voted-options
│   │   │   ├── auth.py          ← GitHub OAuth, /me, /delete-account
│   │   │   └── health.py        ← GET /health
│   │   ├── schemas/
│   │   │   ├── poll.py          ← PollAppearance (theme, colors, radius, font, effect, layout)
│   │   │   ├── vote.py          ← VoteRequest supports multi-select option_ids list
│   │   │   └── ...              ← auth, analytics, leaderboard, health
│   │   └── services/
│   │       ├── pocketbase_service.py  ← Async PocketBase HTTP client
│   │       ├── moderation.py          ← Profanity filter
│   │       ├── poll_utils.py          ← is_poll_closed(), appearance helpers
│   │       └── image_upload.py        ← PocketBase file upload service
│   └── tests/
│       ├── test_api_endpoints.py  ← Core API integration tests
│       ├── test_appearance.py     ← PollAppearance schema + endpoint tests
│       ├── test_behaviors.py      ← Multi-select, quiz, visible voters tests
│       ├── test_image_upload.py   ← Image upload service tests
│       ├── test_moderation.py
│       └── test_rate_limit.py
│       → 60/60 PASSING ✅
├── database/
│   ├── pb_schema.json             ← Version-controlled schema (committed)
│   └── pb_migrations/
│       ├── 1789619075_init_schema.js
│       ├── 1789629521_add_abuse_reports_and_deletion_fields.js
│       ├── 1789638852_poll_appearance.js   ← appearance JSON field
│       ├── 1789639466_json_size_limits.js
│       ├── 1789639490_json_size_limits_fix.js
│       ├── 1789640817_poll_images.js        ← image file field
│       └── 1789641000_behaviors.js          ← multi-select, quiz, visible_voters fields
│   (pb_data/ and binary are gitignored)
└── frontend/                      ← Astro static site
    ├── astro.config.mjs           ← output: "static", React + Svelte integrations
    ├── package.json               ← pnpm only (corepack pnpm)
    └── src/
        ├── styles/global.css      ← Design tokens (Obsidian/Slate), JetBrains Mono + Inter
        ├── layouts/RootLayout.astro ← Base HTML shell + ClientRouter (View Transitions)
        ├── lib/
        │   ├── config.ts   ← getApiUrl(), getSiteUrl(), getPbUrl() — SINGLE SOURCE OF TRUTH
        │   └── embed.ts    ← getBadgeUrl(), getEmbedUrl(), getPollUrl(),
        │                      getMarkdownBadgeSnippet(), getIframeSnippet(), copyToClipboard()
        ├── components/
        │   ├── common/
        │   │   ├── Navbar.astro   ← Auth state detection, sign-in/out controls (flash-free)
        │   │   └── Footer.astro
        │   ├── dashboard/
        │   │   ├── PollCreator.tsx    ← React 19 — theme picker, customizer, behaviors toggles,
        │   │   │                         image uploads, confetti, rich poll creation + live preview
        │   │   └── PollAnalytics.tsx  ← React 19 — charts, CSV/JSON authenticated export
        │   └── embed/
        │       └── PollWidget.svelte  ← Svelte 5 Runes — ONLY Svelte component
        │                                 Supports: 5 themes, multi-select, quiz, visible voters,
        │                                 image options (youtube-grid layout), canvas confetti (915 lines)
        └── pages/
            ├── index.astro            ← Awwwards-level landing page (redesigned)
            ├── auth/callback.astro    ← GitHub OAuth callback handler
            ├── leaderboard/index.astro
            ├── polls/
            │   ├── index.astro        ← Runtime /polls?id=... resolver
            │   └── [id]/index.astro   ← SSG standalone poll page
            ├── embed/
            │   ├── index.astro        ← Runtime /embed?id=... resolver
            │   └── [id]/index.astro   ← SSG embed page (loads PollWidget.svelte)
            ├── theme-samples/index.astro ← Theme showcase page
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
- Dev mode: token stored in `localStorage` key `polls-lab_auth_token`
- Request headers: `Authorization: Bearer <token>` + `x-dev-user-id: <token>`
- Navbar auth flash fixed: script runs before first paint to avoid flicker

### PollWidget.svelte (Svelte 5 Runes) — 915 lines
- Reads poll ID from: (1) `pollId` prop, (2) `?id=` query param, (3) URL path segment
- **5 themes** via `data-theme` attribute on root element + CSS vars:
  - `minimal` (default), `whatsapp`, `telegram`, `story`, `youtube-grid`
- **Behaviors**: `allow_multi_select`, `is_quiz`, `show_voter_names`
- **Image options**: renders images in youtube-grid layout when options have image URLs
- **Canvas confetti**: hand-rolled, fires on successful vote
- Gzipped bundle: **~4.9 KB** (still under 15KB limit)

### PollAppearance Schema (poll.py)
- Fields: `theme` (str), `bg` (hex), `accent` (hex), `ink` (hex), `radius` (0-24), `font` (str), `effect` (str), `layout` (str)
- Stored as `appearance` JSON field in `polls` PocketBase collection
- Legacy polls without `appearance` field get `None` (backward compatible)
- Size limits enforced: `options` max 20,000 bytes, `appearance` max 5,000 bytes

### VoteRequest (vote.py)
- `option_ids: list[str]` — supports multiple selections for `allow_multi_select` polls
- `option_id: str | None` — legacy single-vote field (still accepted)
- Backend enforces quiz correct-answer check when `is_quiz = True`

### Multi-Framework Isolation
- Marketing pages embed Svelte via `<iframe src="/embed?id=...">` NOT `<PollWidget client:load />`
- Svelte 100% isolated to `/embed` routes

### Analytics Export
- Authenticated `fetch` + blob download (NOT `<a href download>`)
- Sends `Authorization: Bearer <token>` header

### BadgeData Dataclass (badges.py)
- `@dataclass(frozen=True)`: `label`, `value`, `is_error`, `target_url`
- `__iter__` → `(label, value, is_error, target_url)` — do NOT reorder
- `target_url` → `/polls/{poll_id}` per PRD §4.4

### URL Helpers
- `getEmbedUrl(id)` → `/embed?id=<id>` (query param — avoids SSG 404)
- `getPollUrl(id)` → `/polls/<id>`
- Badge markdown links to `/polls/` NOT `/embed/`

---

## 5. Running the Project Locally

```bash
# 1. Start PocketBase
./database/pocketbase serve --dir ./database/pb_data

# 2. Start Backend (FastAPI)
backend/.venv/bin/uvicorn backend.app.main:app --reload --port 8000

# 3. Start Frontend (Astro dev)
corepack pnpm --dir frontend dev

# 4. Run Tests
backend/.venv/bin/pytest backend/tests   # → 60/60 pass

# 5. Build Frontend (static)
corepack pnpm --dir frontend run build
```

---

## 6. Progress Summary — ALL PHASES COMPLETE ✅

| Phase | Status |
|-------|--------|
| Phase 1: Setup & Scaffolding | ✅ 100% |
| Phase 2: PocketBase Schema | ✅ 100% |
| Phase 3: FastAPI Backend | ✅ 100% |
| Phase 4: Svelte Embed Widget | ✅ 100% |
| Phase 5: Astro Frontend | ✅ 100% |
| Phase 6: Testing, Polish & SEO | ✅ 100% |
| Phase 7: Custom Poll Themes + Behaviors | ✅ 100% |
| Phase 8: Production Deployment (Dokploy & Docker) | ✅ 100% (Live) |

**All phases and deployment milestones completed.**

---

## 7. Database Schema Summary (PocketBase)

| Collection | Key Fields | Notes |
|-----------|-----------|-------|
| `users` | GitHub OAuth fields, `deletion_status`, `deletion_scheduled_for` | GitHub OAuth only |
| `polls` | `title`, `description`, `options (json)`, `visibility`, `result_display`, `close_at`, `owner`, `appearance (json)`, `images (file[])`, `allow_multi_select`, `is_quiz`, `correct_option_id`, `show_voter_names` | 7 migrations applied |
| `votes` | `poll_id (cascadeDelete)`, `option_id`, `option_ids (json)`, `device_token`, `ip_hash`, `embed_referrer`, `voter_name` | Supports multi-select |
| `abuse_reports` | `poll_id (cascadeDelete)`, `reason`, `ip_hash` | — |

---

## 8. Environment Variables

### Backend `.env` (gitignored)
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

## 9. Test Results (as of HEAD 113be2f)

```
backend/.venv/bin/pytest backend/tests  →  60 passed ✅
  test_api_endpoints.py   (core API)
  test_appearance.py      (PollAppearance schema + endpoint)
  test_behaviors.py       (multi-select, quiz, visible voters)
  test_image_upload.py    (image upload service)
  test_moderation.py
  test_rate_limit.py
```

---

## 10. Git History (last 16 commits since initial completion)

```
113be2f  docs: fix README badge and add embed instructions
2143f9d  docs: add live poll badge to README
1841d2e  fix: seed demo polls, fix navbar auth flash
23e2d45  fix: complete E2E integration verification
ea6903d  fix: complete SEO meta tags and og-image
8f59f80  feat: Awwwards-level landing page redesign
1a74d30  feat: Phase 6 — canvas confetti celebration on vote
c7f14b5  feat: Phase 4+5 — image uploads + poll behaviors (multi-select, quiz, visible voters)
5a206f4  feat(themes): Phase 3 creator theme picker, customizer, and live preview
069c31a  feat(themes): Phase 2 widget theme pack with whatsapp/telegram/story/youtube-grid presets
ed7fb74  feat(themes): Phase 1 poll appearance data model with validation and migration
4db4e21  fix(database): add missing abuse_reports collection and user deletion fields
90acd14  chore: update TODO.md to mark memory.md as done
f7bacf6  docs: add memory.md for fast agent onboarding and context handoff
6ca526f  fix(review): remediate standards and spec findings across backend and frontend
d830125  feat(frontend): complete Phase 5 redesign from scratch with UI/UX Pro Max, Hallmark, and React 19
```

---

## 11. Known Gotchas

1. **`getEmbedUrl(id)` → `/embed?id=<id>`** (query param), NOT `/embed/<id>` (path).
2. **Svelte poll ID resolution order**: prop → `?id=` query param → URL path. Don't break this.
3. **`BadgeData.__iter__`** → `(label, value, is_error, target_url)` — do NOT reorder fields.
4. **Analytics export** uses `fetch` + blob + `Authorization: Bearer` — NOT `<a href download>`.
5. **CORS**: reflects `Origin` + `Allow-Credentials: true` + exposes `X-Device-Token`. Changing breaks embed voting.
6. **PocketBase binary** is gitignored. Download separately and place in `database/`.
7. **View Transitions**: `<ClientRouter />` is in `RootLayout.astro`. All navigations cross-fade.
8. **Dev auth**: `localStorage.polls-lab_auth_token` — Navbar reads this to show/hide Sign In/Out.
9. **JSON size limits**: `options` field max 20,000 bytes, `appearance` max 5,000 bytes (enforced in migration `1789639490`).
10. **Multi-select voting**: `VoteRequest.option_ids` (list) takes priority over legacy `option_id` (str).
11. **graphify knowledge graph**: `graphify-out/graph.html` (349 nodes, 596 edges) — open in browser for visual codebase navigation.

---

## 12. Tools Installed

| Tool | Version | Location |
|------|---------|---------|
| graphify | 0.9.63 | `~/.local/bin/graphify` |
| Skill | registered | `~/.claude/skills/graphify/SKILL.md` |
| Knowledge graph | built | `graphify-out/graph.html` (349 nodes, 596 edges, 16 communities) |
