# Contributing to PollLabs

Thank you for your interest in contributing to PollLabs! We welcome community contributions, bug reports, and enhancements.

## Code of Conduct & Core Values
- Be respectful, constructive, and inclusive.
- Prioritize user privacy, anonymous frictionless voting, and secret hygiene.

## Repository Architecture
PollLabs is structured into three clean pillars:
- **`frontend/`**: Astro 5/7 + React (dashboard) + Svelte 5 (embed widget < 15KB) + Tailwind CSS v4. Package manager: `pnpm` exclusively (`corepack pnpm`).
- **`backend/`**: FastAPI (async I/O, sync CPU tasks) + Pydantic v2. Virtualenv in `backend/.venv` (Python 3.12).
- **`database/`**: PocketBase v0.22 standalone binary with SQLite. Schema migrations in `pb_migrations/`.

## Development Setup

### 1. Prerequisites
- Node.js 20+ & `corepack enable`
- Python 3.12 & `venv`
- PocketBase v0.22+ binary in `database/`

### 2. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
pytest tests/
```

### 3. Frontend Setup
```bash
cd frontend
corepack pnpm install
corepack pnpm run build
```

## Coding & Security Standards
1. **Zero Secret Hygiene**: NEVER commit real secrets, tokens, or personal emails/passwords. Template files (`.env.example`) must exclusively use placeholders.
2. **Atomic Commits**: Use conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
3. **Pydantic v2**: Use `str | None` union syntax, `ConfigDict(from_attributes=True)`, and explicit `response_model` on endpoints.
4. **PocketBase**: Enforce `cascadeDelete: true` on child relations and maintain migrations in `database/pb_migrations/`.

## Pull Request Workflow
1. Fork the repo and create a feature branch (`feat/your-feature`).
2. Verify all pytest tests pass and frontend builds with zero errors:
   ```bash
   pytest backend/tests
   corepack pnpm --dir frontend run build
   ```
3. Run `git diff` to ensure zero credentials or untracked cache files are staged.
4. Submit your pull request with a descriptive summary of changes.
