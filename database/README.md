# PocketBase Database Layer

This directory contains the local PocketBase executable, collections schema, and version-controlled database migrations.

## Quickstart

To start the local database server:

```bash
./pocketbase serve
```

Once running:
- **REST API:** `http://127.0.0.1:8090/api/`
- **Admin UI:** `http://127.0.0.1:8090/_/`

## Admin Setup
On first startup, navigate to `http://127.0.0.1:8090/_/` to create your initial local superuser account.

## Data & Migrations
- `pb_data/`: Ignored by Git. Contains local SQLite data and uploaded files.
- `pb_migrations/`: Tracked in Git. Contains JavaScript/Go migration files for schema changes.
- `pb_schema.json`: Tracked in Git. Exported schema definition of your collections.
