from flask import Flask, jsonify, render_template
import sqlite3
import re
from pathlib import Path
import subprocess
import sys
import json
from hashlib import sha256
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
TEMPLATE_DIR = FRONTEND_DIR if FRONTEND_DIR.exists() else BACKEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR if FRONTEND_DIR.exists() else BACKEND_DIR / "static"
STATIC_URL_PATH = "/static"
DB_PATH = ROOT_DIR / "db" / "jobs.db"
LEGACY_DB_PATH = BACKEND_DIR / "db" / "jobs.db"
JOBS_JSON_PATH = ROOT_DIR / "data" / "jobs.json"
RESOLVED_DB_PATH = None


def db_row_count(path):
    if not path.exists():
        return -1
    try:
        conn = sqlite3.connect(str(path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
        if cur.fetchone() is None:
            conn.close()
            return 0
        cur.execute("SELECT COUNT(*) FROM applications")
        count = cur.fetchone()[0]
        conn.close()
        return count
    except sqlite3.Error:
        return -1


def resolve_db_path():
    """Prefer legacy backend/db only when it clearly has more job rows."""
    primary_count = db_row_count(DB_PATH)
    legacy_count = db_row_count(LEGACY_DB_PATH)

    if legacy_count > primary_count and legacy_count > 0:
        return LEGACY_DB_PATH

    return DB_PATH


def get_db_path():
    global RESOLVED_DB_PATH
    if RESOLVED_DB_PATH is None:
        RESOLVED_DB_PATH = resolve_db_path()
    return RESOLVED_DB_PATH


def stable_job_hash(record):
    key = record.get("id") or record.get("url") or f"{record.get('company','')}::{record.get('title','')}::{record.get('location','')}"
    return sha256(str(key).encode("utf-8")).hexdigest()


def hydrate_db_from_jobs_json(conn):
    """Backfill DB from data/jobs.json when the DB only has seed/empty data."""
    if not JOBS_JSON_PATH.exists():
        return

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applications")
    row_count = cur.fetchone()[0]
    if row_count > 1:
        return

    try:
        raw_jobs = json.loads(JOBS_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        return

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    inserted = 0
    for job in raw_jobs:
        if not isinstance(job, dict):
            continue
        cur.execute(
            """
            INSERT OR IGNORE INTO applications
            (external_id, company, title, location, url, source, date_posted, date_scraped, job_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(job.get("id") or ""),
                job.get("company") or "",
                job.get("title") or "",
                job.get("location") or "",
                job.get("url") or "",
                "json_backfill",
                job.get("date_posted") or "",
                now,
                stable_job_hash(job),
            ),
        )
        inserted += cur.rowcount > 0

    if inserted:
        conn.commit()


def ensure_database():
    """Ensure SQLite DB schema exists using backend/db_init.py."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='applications'")
    has_apps_table = cur.fetchone() is not None
    conn.close()

    if not has_apps_table:
        subprocess.run([sys.executable, str(ROOT_DIR / "backend" / "db_init.py")], check=True)


app = Flask(
    __name__,
    template_folder=str(TEMPLATE_DIR),
    static_folder=str(STATIC_DIR),
    static_url_path=STATIC_URL_PATH,
)


def normalize_location(loc):
    """Normalize location strings for consistency."""
    if not loc:
        return "Unknown"

    cleaned = loc.strip()
    if "remote" in cleaned.lower():
        return "Remote"

    cleaned = re.sub(r"\s*-\s*", ", ", cleaned)
    cleaned = re.sub(r",\s*,+", ",", cleaned)
    return cleaned.strip(", ")


def query_db(query, args=()):
    ensure_database()
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    hydrate_db_from_jobs_json(conn)
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/jobs")
def get_jobs():
    rows = query_db("SELECT company, location, title, url FROM applications ORDER BY id DESC")
    for row in rows:
        row["location"] = normalize_location(row.get("location"))
    return jsonify(rows)


@app.route("/companies")
def get_companies():
    rows = query_db("SELECT DISTINCT company FROM applications WHERE company IS NOT NULL AND company != '' ORDER BY company")
    return jsonify([row["company"] for row in rows])


@app.route("/locations")
def get_locations():
    rows = query_db("SELECT DISTINCT location FROM applications")
    locations = sorted({normalize_location(row.get("location")) for row in rows})
    return jsonify(locations)


if __name__ == "__main__":
    app.run(debug=True)
