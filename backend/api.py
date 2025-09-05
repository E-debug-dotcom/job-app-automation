from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3
import re

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)  # Allow cross-origin requests

DB_PATH = "db/jobs.db"

# ----------------- Helper Functions -----------------
def normalize_location(loc):
    """Normalize location strings for consistency."""
    if not loc:
        return "Unknown"
    loc = loc.strip()
    if "remote" in loc.lower():
        return "Remote"
    loc = re.sub(r"\s*-\s*", ", ", loc)
    loc = re.sub(r",\s*,+", ",", loc)
    loc = loc.strip(", ")
    return loc

def query_db(query, args=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ----------------- API Endpoints -----------------
@app.route("/jobs")
def get_jobs():
    rows = query_db("SELECT company, location, title, url FROM applications ORDER BY id DESC")
    # Normalize locations on the fly
    for row in rows:
        row["location"] = normalize_location(row["location"])
    return jsonify(rows)

@app.route("/companies")
def get_companies():
    rows = query_db("SELECT DISTINCT company FROM applications ORDER BY company")
    companies = [row["company"] for row in rows]
    return jsonify(companies)

@app.route("/locations")
def get_locations():
    rows = query_db("SELECT DISTINCT location FROM applications")
    locations = [normalize_location(row["location"]) for row in rows]
    # Remove duplicates after normalization
    locations = sorted(list(set(locations)))
    return jsonify(locations)

# ----------------- Serve Frontend -----------------
@app.route("/")
def index():
    return app.send_static_file("index.html")

# ----------------- Main -----------------
if __name__ == "__main__":
    print("Serving static from:", app.static_folder)
    app.run(debug=True)
