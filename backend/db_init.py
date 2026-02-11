import sqlite3
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_DIR = ROOT_DIR / "db"
DB_PATH = DB_DIR / "jobs.db"


def init_db(seed_sample_data=True):
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            default_resume TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT,
            company TEXT,
            title TEXT,
            location TEXT,
            url TEXT,
            source TEXT,
            date_posted TEXT,
            date_scraped TEXT,
            date_applied TEXT,
            status TEXT DEFAULT 'pending',
            matched_skills TEXT,
            notes TEXT,
            job_hash TEXT UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER,
            doc_type TEXT,
            path TEXT,
            FOREIGN KEY(profile_id) REFERENCES profiles(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS application_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            event_type TEXT,
            event_date TEXT,
            notes TEXT,
            FOREIGN KEY(application_id) REFERENCES applications(id)
        )
    ''')

    if seed_sample_data:
        cursor.execute("SELECT COUNT(*) FROM profiles")
        profiles_count = cursor.fetchone()[0]
        if profiles_count == 0:
            cursor.execute('''
                INSERT INTO profiles (name, email, phone, default_resume)
                VALUES (?, ?, ?, ?)
            ''', ("Eleandro Girgis", "egirgis@email.com", "555-1234", "resume.pdf"))

        cursor.execute("SELECT COUNT(*) FROM applications")
        apps_count = cursor.fetchone()[0]
        if apps_count == 0:
            cursor.execute('''
                INSERT INTO applications (external_id, company, title, location, url, source, date_posted, date_scraped, job_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                "job123",
                "Example Corp",
                "IT Analyst",
                "Vancouver, BC",
                "https://example.com/job123",
                "ExampleSite",
                "2025-09-01",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sample-job-123"
            ))

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}.")


if __name__ == "__main__":
    init_db()
