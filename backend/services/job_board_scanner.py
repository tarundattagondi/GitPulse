import asyncio
import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

import httpx

from backend.storage import save_cached_jobs, get_cached_jobs

SIMPLIFY_URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/README.md"


@dataclass
class JobListing:
    company: str
    role: str
    location: str
    link: str
    posted_date: str
    is_closed: bool
    sponsors_visa: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _parse_html_table(readme_text: str) -> list[JobListing]:
    """Parse the SimplifyJobs HTML table rows into JobListing objects."""
    listings = []
    current_company = ""

    # Split into <tr>...</tr> blocks
    rows = re.findall(r"<tr>(.*?)</tr>", readme_text, re.DOTALL)

    for row in rows:
        cells = re.findall(r"<td>(.*?)</td>", row, re.DOTALL)
        if len(cells) < 4:
            continue

        raw_company = cells[0].strip()
        role = cells[1].strip()
        location_raw = cells[2].strip()
        application_raw = cells[3].strip()
        age_raw = cells[4].strip() if len(cells) > 4 else ""

        # Skip header rows
        if role.lower() in ("role", "---"):
            continue

        # Company: extract from link or use ↳ for sub-listings
        if raw_company == "↳":
            company = current_company
        else:
            company_match = re.search(r">([^<]+)</a>", raw_company)
            company = company_match.group(1).strip() if company_match else re.sub(r"<[^>]+>", "", raw_company).strip()
            if company:
                current_company = company

        if not company or not role:
            continue

        # Clean role text
        role = re.sub(r"<[^>]+>", "", role).strip()

        # Location: handle <details> multi-location and plain text
        location_details = re.search(r"<summary><strong>(.*?)</strong></summary>(.*?)</details>", location_raw, re.DOTALL)
        if location_details:
            inner = location_details.group(2)
            locations = [loc.strip() for loc in re.split(r"<br\s*/?>", inner) if loc.strip()]
            location = "; ".join(locations) if locations else location_details.group(1)
        else:
            location = re.sub(r"<[^>]+>", "", location_raw).strip()

        # Application link
        link_match = re.search(r'href="([^"]*(?:greenhouse|lever|workday|icims|oracle|careers|jobs|apply)[^"]*)"', application_raw, re.IGNORECASE)
        if not link_match:
            link_match = re.search(r'href="([^"]*)"', application_raw)
        link = link_match.group(1) if link_match else ""
        # Remove tracking params
        link = re.sub(r"[?&]utm_source=Simplify.*", "", link)
        link = re.sub(r"[?&]ref=Simplify.*", "", link)

        # Closed check: 🔒 in company or application cell
        is_closed = "🔒" in raw_company or "🔒" in application_raw

        # Visa sponsorship: 🛂 means does NOT sponsor
        sponsors_visa = "🛂" not in raw_company and "🛂" not in row

        # Posted date: convert age like "0d", "1d", "5d" to date string
        age_match = re.search(r"(\d+)d", age_raw)
        if age_match:
            days_ago = int(age_match.group(1))
            posted_dt = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            from datetime import timedelta
            posted_dt -= timedelta(days=days_ago)
            posted_date = posted_dt.strftime("%Y-%m-%d")
        else:
            posted_date = ""

        listings.append(JobListing(
            company=company,
            role=role,
            location=location,
            link=link,
            posted_date=posted_date,
            is_closed=is_closed,
            sponsors_visa=sponsors_visa,
        ))

    return listings


async def fetch_simplify_jobs(force_refresh: bool = False) -> list[JobListing]:
    """Fetch and parse SimplifyJobs listings, with 24hr Supabase cache."""
    # Check cache in Supabase
    if not force_refresh:
        cached = get_cached_jobs(max_age_hours=24)
        if cached:
            jobs = []
            for row in cached:
                raw = row.get("raw", {})
                if raw:
                    try:
                        jobs.append(JobListing(**{k: raw[k] for k in JobListing.__dataclass_fields__ if k in raw}))
                    except Exception:
                        pass
            if jobs:
                return jobs

    # Fetch fresh
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(SIMPLIFY_URL)
        resp.raise_for_status()
        readme_text = resp.text

    listings = _parse_html_table(readme_text)

    # Cache to Supabase
    save_cached_jobs([j.to_dict() for j in listings])

    return listings


def filter_jobs(
    jobs: list[JobListing],
    role_keywords: list[str] | None = None,
    location_keywords: list[str] | None = None,
    exclude_closed: bool = True,
) -> list[JobListing]:
    """Filter jobs by role keywords, location keywords, and open/closed status."""
    filtered = jobs

    if exclude_closed:
        filtered = [j for j in filtered if not j.is_closed]

    if role_keywords:
        kw_lower = [k.lower() for k in role_keywords]
        filtered = [
            j for j in filtered
            if any(k in j.role.lower() or k in j.company.lower() for k in kw_lower)
        ]

    if location_keywords:
        loc_lower = [k.lower() for k in location_keywords]
        filtered = [
            j for j in filtered
            if any(k in j.location.lower() for k in loc_lower)
        ]

    return filtered


async def scan_jobs_for_user(
    username: str,
    role_filters: list[str] | None = None,
    location_filters: list[str] | None = None,
    max_jobs: int = 30,
) -> list[dict]:
    """Fetch GitHub profile, scan jobs, and run JD analyzer + matcher in parallel.
    Returns jobs ranked by match_score descending."""
    from backend.services.github_service import fetch_profile, fetch_all_repos, fetch_readme
    from backend.services.jd_analyzer import analyze_jd
    from backend.services.matcher import match_profile_to_jd

    # Step 1: Fetch GitHub data and jobs concurrently
    profile_task = fetch_profile(username)
    repos_task = fetch_all_repos(username)
    jobs_task = fetch_simplify_jobs()

    profile, repos, all_jobs = await asyncio.gather(profile_task, repos_task, jobs_task)

    # Fetch READMEs for top repos
    readmes = {}
    for r in repos[:5]:
        readmes[r["name"]] = await fetch_readme(username, r["name"])

    github_data = {"profile": profile, "repos": repos, "readmes": readmes}

    # Step 2: Filter jobs
    filtered = filter_jobs(all_jobs, role_keywords=role_filters, location_keywords=location_filters)
    candidates = filtered[:max_jobs]

    if not candidates:
        return []

    # Step 3: Analyze and match in parallel with semaphore
    semaphore = asyncio.Semaphore(5)

    async def _analyze_and_match(job: JobListing) -> dict:
        async with semaphore:
            loop = asyncio.get_event_loop()
            jd_text = f"{job.company} - {job.role}\nLocation: {job.location}"

            try:
                # Run CPU/IO-bound Claude calls in executor
                jd_analysis = await loop.run_in_executor(None, analyze_jd, jd_text)
                match_result = await loop.run_in_executor(
                    None, match_profile_to_jd, github_data, jd_analysis
                )
                return {
                    **job.to_dict(),
                    "match_score": match_result.get("overall_match_pct", 0),
                    "match_details": match_result,
                }
            except Exception as e:
                return {
                    **job.to_dict(),
                    "match_score": 0,
                    "match_details": {"error": str(e)},
                }

    results = await asyncio.gather(*[_analyze_and_match(j) for j in candidates])

    # Sort by match score descending
    ranked = sorted(results, key=lambda x: x["match_score"], reverse=True)
    return ranked
