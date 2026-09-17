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

## 2. Git Workflow

- Remote repository: `https://github.com/Luckyyaduvanshiofficial/polllabs.git`
- Default branch: `main`
- Maintain clean atomic commits with conventional commit messages (`feat:`, `fix:`, `chore:`).
- Push to `origin main` whenever code changes are made.
- Ensure author email matches privacy/noreply settings.

## 3. Technology Stack & Directory Structure

- **Frontend (`frontend/`)**:
  - Package manager: `pnpm` exclusively (`corepack pnpm`).
  - Framework: Astro with folder-based routing in `src/pages/`.
  - UI Integrations: React for Dashboard state (`@astrojs/react`), Svelte for lightweight iframe embed (`@astrojs/svelte`), Tailwind CSS v4.
- **Backend (`backend/`)**:
  - Framework: FastAPI with Pydantic v2 schemas.
  - Runtime: Python 3.12 virtual environment (`backend/.venv`).
  - API Versioning: `/api/v1/...`.
- **Database (`database/`)**:
  - Engine: PocketBase standalone binary with SQLite.
  - Ignored: `database/pb_data/`, `database/pocketbase` (binary).
  - Tracked: `database/pb_migrations/`, `database/pb_schema.json`.
