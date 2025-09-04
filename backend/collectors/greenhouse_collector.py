import json
import requests
import sqlite3
from hashlib import sha256
from datetime import datetime

SOURCE = "greenhouse_direct"

# --- Helper functions ---
def sha256_hash(value):
    return sha256(value.encode("utf-8")).hexdigest()

def parse_location(job):
    loc = job.get("location")
    if isinstance(loc, list):
        return ", ".join([l.get("name","") for l in loc])
    elif isinstance(loc, dict):
        return loc.get("name", "")
    return ""

def insert_job_if_new(conn, company, job_record):
    cursor = conn.cursor()
    key = job_record.get("external_id") or job_record.get("url") or (job_record.get("title") + job_record.get("location"))
    job_hash = sha256_hash(key)
    cursor.execute("SELECT id FROM applications WHERE job_hash = ?", (job_hash,))
    if cursor.fetchone():
        return False
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO applications
        (external_id, company, title, location, url, source, date_posted, date_scraped, job_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_record.get("external_id"),
        company,
        job_record.get("title"),
        job_record.get("location"),
        job_record.get("url"),
        SOURCE,
        job_record.get("date_posted"),
        now,
        job_hash
    ))
    conn.commit()
    return True

# --- Collector ---
def fetch_jobs(handle, api_url=None):
    if not api_url:
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{handle}/jobs"
    resp = requests.get(api_url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("jobs", [])

def main(companies_file):
    with open(companies_file) as f:
        companies_list = json.load(f)

    conn = sqlite3.connect("db/jobs.db")

    total_added = 0
    for entry in companies_list:
        if isinstance(entry, str):
            handle = entry
            api_url = None
        elif isinstance(entry, dict):
            handle = entry.get("handle")
            api_url = entry.get("api")
        else:
            continue

        print(f"[INFO] scanning {handle}")
        try:
            jobs = fetch_jobs(handle, api_url)
            added = 0
            for job in jobs:
                if insert_job_if_new(conn, handle, {
                    "external_id": str(job.get("id")),
                    "title": job.get("title"),
                    "location": parse_location(job),
                    "url": job.get("absolute_url"),
                    "date_posted": job.get("updated_at") or job.get("created_at")
                }):
                    added += 1
            print(f"[INFO] added {added} jobs for {handle}")
            total_added += added
        except requests.HTTPError as e:
            print(f"[HTTP ERROR] {handle}: {e.response.status_code} {e.response.reason}")
        except Exception as e:
            print(f"[ERROR] {handle}: {e}")

    print(f"[DONE] total added: {total_added}")
    conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies", required=True, help="Path to companies.json")
    args = parser.parse_args()
    main(args.companies)
