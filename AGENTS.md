# Agent Guidelines & Repository Rules

## 1. Strict Security & Secret Hygiene (Zero-Tolerance)

- **NEVER commit secrets, credentials, or actual emails/passwords**:
  - Do not hardcode credentials in code (`config.py`, settings, tests, scripts, etc.).
  - Do not place real credentials in `.env.example` or any documentation file.
  - Template files (`.env.example`) must exclusively use placeholder values (e.g., `admin@example.com`, `change_this_password`, `your-secret-salt`).
- **Local Environment**:
  - Real development and production credentials reside **only** in local, untracked `.env` files.
  - Verify `.env` files remain in `.gitignore`.
- **Pre-Commit Verification**:
  - Always run `git diff` before staging and committing to ensure zero secrets, tokens, or credentials are being tracked.

## 2. Progress & Task Tracking (Mandatory Rule)

- **ALWAYS update `TODO.md`**:
  - Whenever completing a task, implementing a feature, or progressing through milestones, update `TODO.md` immediately.
  - Keep checkmarks (`[x]`), percentages, and status indicators in sync with the repository state.
  - Never finish an interaction where work was completed without reflecting it in `TODO.md`.

## 3. Git Workflow

- Remote repository: `https://github.com/Luckyyaduvanshiofficial/polls-lab.git`
- Default branch: `main`
- Maintain clean atomic commits with conventional commit messages (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`).
- Push to `origin main` whenever code or documentation changes are made.
- Ensure author email matches privacy/noreply settings.

## 4. Backend (FastAPI & Pydantic v2) Standards

- **Async vs Sync Operations**:
  - Use `async def` for I/O-bound endpoints (database calls, network requests, HTTP clients).
  - Use `def` for CPU-bound tasks (e.g., SVG badge generation) to prevent blocking the event loop.
- **Pydantic v2 Conventions**:
  - NEVER use Ellipsis (`...`) as default for required fields; use `Field(min_length=...)` directly.
  - Use `model_config = ConfigDict(from_attributes=True)` instead of v1 `class Config`.
  - Use `@field_validator` and `@model_validator` instead of `@validator`.
  - Use union syntax (`str | None`) instead of `Optional[str]`.
- **FastAPI Conventions**:
  - Declare `prefix` and `tags` directly on `APIRouter(prefix="/...", tags=["..."])`.
  - Use HTTP status constants from `fastapi.status` (e.g., `status.HTTP_429_TOO_MANY_REQUESTS`).
  - Use `Annotated[T, Depends(...)]` for dependency injection.
  - Use `@asynccontextmanager async def lifespan(app: FastAPI)` instead of `@app.on_event`.
  - Explicit return types or `response_model` on all endpoints.

## 5. Database (PocketBase) Standards

- **Engine & Files**:
  - PocketBase standalone binary with SQLite in `database/`.
  - `database/pb_data/` and binary must remain ignored in `.gitignore`.
  - Version-controlled schema migrations must live in `database/pb_migrations/` and `database/pb_schema.json`.
- **Relations & Integrity**:
  - Enforce `cascadeDelete: true` on child relations (e.g. `votes` on `polls`) to prevent orphaned records.
  - Use specialized field types (`select` for enums, `json` for arrays/structures, `relation` for references).
  - Index frequently filtered/sorted fields (`poll_id`, `visibility`, `device_token`, `ip_hash`).

## 6. Frontend (Astro, React, Svelte) Standards

- **Package manager**: `pnpm` exclusively (`corepack pnpm`).
- **Folder-based routing**: All routes must reside in `src/pages/` mapping 1:1 with URLs.
- **Multi-framework isolation**:
  - Use React for state-heavy components in `/dashboard`.
  - Use Svelte for ultra-lightweight embeds in `/embed/[id]` (< 15KB bundle footprint).
  - Use pure Astro components for SEO, marketing, and docs.
