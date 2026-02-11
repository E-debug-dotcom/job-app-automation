# Job Application Automation

A lightweight job aggregation app that:
- collects jobs from Greenhouse board APIs into SQLite,
- serves a searchable/filterable job board via Flask,
- tracks applications in a local database.

## Architecture

Runtime path (recommended):
- **Backend API:** `backend/api.py`
- **Collector:** `backend/collectors/greenhouse_collector.py`
- **Database:** `db/jobs.db`
- **Frontend:** served from `backend/static/`

Supporting scripts:
- `backend/db_init.py` initializes schema and optional sample seed data.
- `backend/merge_jobs.py` merges raw JSON dumps in `data/greenhouse` + `data/lever`.
- `generate_meta.py` regenerates `data/companies.json` and `data/locations.json` from `data/jobs.json`.

## Prerequisites

- Python 3.10+

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Initialize the database

```bash
python3 backend/db_init.py
```

This creates `db/jobs.db` and only seeds sample rows when tables are empty.

## Collect Greenhouse jobs

Use the provided config file of board handles:

```bash
python3 backend/collectors/greenhouse_collector.py --companies config/companies.json
```

Optional destructive cleanup (off by default):

```bash
python3 backend/collectors/greenhouse_collector.py --companies config/companies.json --prune-bad
```

## Run the app

```bash
python3 backend/api.py
```

Open: `http://127.0.0.1:5000/`

## API endpoints

- `GET /jobs` → list of jobs
- `GET /companies` → distinct companies
- `GET /locations` → normalized locations

## Optional JSON workflow

If you are working from raw JSON exports instead of DB-backed collector output:

```bash
python3 backend/merge_jobs.py
python3 generate_meta.py
python3 backend/app.py
```

## Suggested next improvements

1. Add a `Makefile` for one-command setup/run.
2. Add tests for DB pathing and API endpoint responses.
3. Consolidate duplicate frontend copies (`frontend/` and inline static variants) once runtime path is finalized.
