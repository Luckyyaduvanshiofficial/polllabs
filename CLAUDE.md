# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

`AGENTS.md` holds the binding repository rules (secret hygiene, commit conventions, framework standards). `memory.md` is a longer onboarding narrative with per-file annotations and a gotchas list. Read both before non-trivial work; this file is the short operational summary.

## Commands

Three services, each started from its own directory.

```bash
# Database (PocketBase) — admin UI at http://127.0.0.1:8090/_/
./database/pocketbase serve --dir ./database/pb_data

# Backend (FastAPI) — OpenAPI docs at http://127.0.0.1:8000/docs
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

# Frontend (Astro) — http://localhost:4321
corepack pnpm --dir frontend dev
```

Tests and builds:

```bash
cd backend && .venv/bin/pytest tests              # full suite (60 tests)
cd backend && .venv/bin/pytest tests/test_behaviors.py -q
cd backend && .venv/bin/pytest tests/test_behaviors.py::test_name -q
corepack pnpm --dir frontend run build            # static build to frontend/dist
```

`backend/.venv` is gitignored and holds an absolute interpreter path, so it breaks if the repo is moved or cloned fresh. Recreate with `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`. Always invoke `.venv/bin/python` / `.venv/bin/pytest` directly rather than relying on an activated shell.

`pnpm` only, via `corepack pnpm`. `package-lock.json` is gitignored on purpose; `pnpm-lock.yaml` is the tracked lockfile. There is no lint or typecheck script — `astro build` is the only frontend gate.

Full-stack containers: `docker compose up --build` (db, backend, frontend behind nginx). Production runs on Dokploy with each service deployed separately; `.env.production.example` is the template.

## Architecture

Three pillars, no shared code between them. They communicate over HTTP only.

**`database/`** — PocketBase standalone binary + SQLite. Collections: `polls`, `votes`, `abuse_reports`, `users` (GitHub OAuth only). `pb_data/` and the binary are gitignored; the binary must be downloaded separately. Schema changes require both a migration in `pb_migrations/` and a re-export of `pb_schema.json`. `votes` and `abuse_reports` relate to `polls` with `cascadeDelete: true`. The `votes.createRule` is locked so writes must go through the backend, which is what makes the abuse checks enforceable.

**`backend/`** — FastAPI, Python 3.12, Pydantic v2. `app/main.py` wires a lifespan that creates one `AsyncPocketBaseService` and parks it on `app.state`; `app/core/dependencies.py` exposes it as `PocketBaseDep`. All PocketBase access flows through `app/services/pocketbase_service.py`, which authenticates as the PocketBase superuser, pools connections through a single `httpx.AsyncClient`, and re-creates that client when the running event loop changes (needed for `TestClient`). Routers live in `app/api/v1/` and are assembled by `router.py` under the `/api/v1` prefix.

**`frontend/`** — Astro 7 static output, three rendering technologies with strict role separation:
- Pure Astro for marketing, docs, leaderboard, SEO pages
- React 19 for state-heavy dashboard components only (`components/dashboard/`)
- Svelte 5 runes for the embed widget only (`components/embed/PollWidget.svelte`, ~4.9 KB gzipped against a 15 KB budget)

Marketing pages that show a poll do it through `<iframe src="/embed?id=...">`, never by mounting `PollWidget` directly. That isolation is what keeps Svelte out of the main bundle.

### Cross-cutting mechanisms

**Scoped CORS** (`ScopedCORSMiddleware` in `app/main.py`) is hand-rolled rather than `CORSMiddleware` because two policies coexist: vote/badge/health and public GET endpoints reflect any origin so embeds work on third-party sites, while management and analytics endpoints only accept origins in `BACKEND_CORS_ORIGINS`. It reflects the request origin instead of `*` because `credentials: 'include'` forbids the wildcard. Changing this breaks embedded voting.

**Abuse mitigation** is two independent signals in `POST /api/v1/votes/{poll_id}`: a salted-SHA256 IP hash feeding an in-process sliding-window limiter (`app/core/rate_limit.py`), plus a `polls-lab_device_token` accepted from the request body, the httpOnly cookie, or the `x-device-token` header. The limiter is per-process memory, so it does not hold across the multi-worker production deployment.

**Result masking** happens server-side. `result_display` (`show_counts` / `show_percentage` / `hidden_until_close`) is applied by `sanitize_poll_options_for_display` before responses leave the backend, including in the vote response, so counts never reach a client that should not see them. Poll owners get unmasked data via `OptionalUser`.

**Auth** is PocketBase GitHub OAuth. The backend reads the user ID out of the JWT payload without verifying the signature. `x-dev-user-id` is a development shortcut and is rejected outright when `ENVIRONMENT=production`.

**Badges** (`app/api/v1/badges.py`) are CPU-bound and therefore use `def`, not `async def`. SVG is generated by string templating and PNG through Pillow. Missing polls return a valid error badge with HTTP 200 so READMEs never show a broken image.

**URL helpers** live in `frontend/src/lib/config.ts` (`getApiUrl`, `getSiteUrl`, `getPbUrl`, reading `PUBLIC_*` env vars with localhost fallbacks) and `frontend/src/lib/embed.ts` (badge, poll, embed, and snippet builders). Do not hardcode base URLs anywhere else. `PUBLIC_*` vars are baked in at build time, which is why the Dockerfile takes them as build args.

## Non-obvious constraints

- `getEmbedUrl(id)` produces `/embed?id=<id>`, a query param, not `/embed/<id>`. The path form 404s under static output for polls that were not known at build time.
- `PollWidget.svelte` resolves its poll ID in a fixed order: `pollId` prop, then `?id=` query param, then trailing URL path segment. Preserve that order.
- `BadgeData.__iter__` yields `(label, value, is_error, target_url)`. Callers destructure positionally.
- Analytics export uses `fetch` plus a blob download, not `<a download>`, because the endpoint requires an `Authorization` header.
- `VoteRequest` accepts both a list and a legacy single string for `option_id`; multi-select merges new selections with existing ones and validates against `max_selections`.
- PocketBase JSON fields have byte caps set in migration `1789639490`: `options` 20,000, `appearance` 5,000.
- `RootLayout.astro` includes `<ClientRouter />`, so every navigation is a view transition. Scripts that assume a full page load need `astro:page-load`.

## Working agreements

- Update `TODO.md` in the same change as any completed task. `AGENTS.md` treats this as mandatory, not optional.
- Never put real credentials in `.env.example`, `.env.production.example`, or docs. Run `git diff` before staging.
- Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`), pushed to `origin main`.
- Backend style: `async def` for I/O, plain `def` for CPU work, `Annotated[T, Depends(...)]` for injection, `status.HTTP_*` constants, explicit return types or `response_model` on every endpoint, `str | None` over `Optional`, `ConfigDict(from_attributes=True)` over `class Config`, and no `...` as a field default.
