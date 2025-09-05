from flask import Flask, jsonify, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder="static")

# --- Serve the frontend ---
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# --- API Endpoints ---
@app.route("/jobs")
def jobs():
    conn = sqlite3.connect("db/jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT company, location, title, url
        FROM applications
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    # Convert to list of dicts
    return jsonify([
        {"company": r[0], "location": r[1], "title": r[2], "url": r[3]}
        for r in rows
    ])

@app.route("/companies")
def companies():
    conn = sqlite3.connect("db/jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT company FROM applications ORDER BY company
    """)
    rows = cursor.fetchall()
    conn.close()
    return jsonify([r[0] for r in rows])

@app.route("/locations")
def locations():
    conn = sqlite3.connect("db/jobs.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT location FROM applications ORDER BY location
    """)
    rows = cursor.fetchall()
    conn.close()
    return jsonify([r[0] for r in rows])

if __name__ == "__main__":
    print("Serving static from:", os.path.abspath(app.static_folder))
    app.run(debug=True)
