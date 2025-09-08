import json
from pathlib import Path

data_dir = Path("data")
jobs_file = data_dir / "jobs.json"

with open(jobs_file, "r", encoding="utf-8") as f:
    jobs = json.load(f)

# Extract unique companies and locations
companies = sorted({job.get("company") for job in jobs if job.get("company")})
locations = sorted({job.get("location") for job in jobs if job.get("location")})

# Save
with open(data_dir / "companies.json", "w", encoding="utf-8") as f:
    json.dump(companies, f, indent=2)

with open(data_dir / "locations.json", "w", encoding="utf-8") as f:
    json.dump(locations, f, indent=2)

print("companies.json and locations.json generated!")
