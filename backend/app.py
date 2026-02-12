from flask import Flask, jsonify, render_template
import sqlite3
import re
from pathlib import Path
import subprocess
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
TEMPLATE_DIR = FRONTEND_DIR if FRONTEND_DIR.exists() else BACKEND_DIR / "templates"
STATIC_DIR = FRONTEND_DIR if FRONTEND_DIR.exists() else BACKEND_DIR / "static"
STATIC_URL_PATH = "" if FRONTEND_DIR.exists() else "/static"
DB_PATH = ROOT_DIR / "db" / "jobs.db"


def ensure_database():
    """Ensure SQLite DB schema exists using backend/db_init.py."""
    conn = sqlite3.connect(str(DB_PATH))
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
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
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
