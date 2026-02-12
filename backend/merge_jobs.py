import glob
import json
import os
from urllib.parse import urlparse


def infer_company(job, source, company_fallback=""):
    explicit_company = job.get("company")
    if explicit_company:
        return explicit_company

    if source == "greenhouse":
        url = job.get("absolute_url") or job.get("url") or ""
        try:
            path_parts = [p for p in urlparse(url).path.split("/") if p]
            if len(path_parts) >= 2 and path_parts[1] == "jobs":
                return path_parts[0]
        except Exception:
            pass

    return company_fallback


def normalize_job(job, source, company_fallback=""):
    normalized = {
        "title": job.get("title") or "",
        "company": infer_company(job, source, company_fallback=company_fallback),
        "location": "",
        "url": job.get("absolute_url") or job.get("url") or "",
        "date_posted": job.get("updated_at", "").split("T")[0] if "updated_at" in job else job.get("date_posted", ""),
        "id": job.get("id") or "",
    }
    if source == "greenhouse":
        loc = job.get("location")
        if isinstance(loc, dict):
            normalized["location"] = loc.get("name", "")
        elif isinstance(loc, str):
            normalized["location"] = loc
    elif source == "lever":
        normalized["location"] = job.get("categories", {}).get("location", "")
    return normalized


def load_jobs_from_folder(folder, source):
    jobs = []
    for file_path in glob.glob(os.path.join(folder, "*.json")):
        company_fallback = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, "r", encoding="utf-8") as f:
            raw_jobs = json.load(f)
            for job in raw_jobs:
                jobs.append(normalize_job(job, source, company_fallback=company_fallback))
    return jobs


all_jobs = []
all_jobs.extend(load_jobs_from_folder("data/greenhouse", "greenhouse"))
all_jobs.extend(load_jobs_from_folder("data/lever", "lever"))

# Deduplicate by company + title + location
unique = {}
for job in all_jobs:
    key = (job["company"], job["title"], job["location"])
    unique[key] = job

merged_jobs = list(unique.values())

os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump(merged_jobs, f, indent=2, ensure_ascii=False)

print(f"Merged {len(merged_jobs)} jobs into data/jobs.json")
