"""Supabase-backed storage layer for GitPulse.

All functions maintain backward-compatible names where possible.
Tables: analyses, snapshots, cached_jobs, pr_log, rate_limits, company_benchmarks.
"""

import logging
from datetime import datetime, timezone, timedelta

from supabase import create_client, Client

from backend.config import SUPABASE_URL, SUPABASE_SERVICE_KEY

logger = logging.getLogger(__name__)

_client: Client = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


# ── Analyses (full analysis results) ─────────────────────────────

def save_analysis(username: str, role_category: str, overall_score: int,
                  category_scores: dict, jd_analysis: dict = None,
                  match_result: dict = None, recommendations: dict = None,
                  github_summary: dict = None) -> dict:
    row = {
        "username": username,
        "role_category": role_category,
        "overall_score": overall_score,
        "category_scores": category_scores,
        "jd_analysis": jd_analysis,
        "match_result": match_result,
        "recommendations": recommendations,
        "github_summary": github_summary,
    }
    res = get_client().table("analyses").insert(row).execute()
    return res.data[0] if res.data else {}


def get_latest_analysis(username: str) -> dict | None:
    res = (get_client().table("analyses")
           .select("*")
           .eq("username", username)
           .order("created_at", desc=True)
           .limit(1)
           .execute())
    return res.data[0] if res.data else None


def get_analyses_history(username: str, limit: int = 10) -> list:
    res = (get_client().table("analyses")
           .select("*")
           .eq("username", username)
           .order("created_at", desc=True)
           .limit(limit)
           .execute())
    return res.data or []


# ── Snapshots (progress tracking) ────────────────────────────────

def save_snapshot(username: str, role_category: str, overall_score: int,
                  category_scores: dict, repo_count: int = 0,
                  total_stars: int = 0, delta_since_last: dict = None) -> dict:
    row = {
        "username": username,
        "role_category": role_category,
        "overall_score": overall_score,
        "category_scores": category_scores,
        "repo_count": repo_count,
        "total_stars": total_stars,
        "delta_since_last": delta_since_last,
    }
    res = get_client().table("snapshots").insert(row).execute()
    return res.data[0] if res.data else {}


def get_snapshots(username: str, role_category: str = None, days: int = 90) -> list:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    query = (get_client().table("snapshots")
             .select("*")
             .eq("username", username)
             .gte("created_at", cutoff)
             .order("created_at", desc=False))
    if role_category:
        query = query.eq("role_category", role_category)
    res = query.execute()
    return res.data or []


# ── Cached jobs ──────────────────────────────────────────────────

def save_cached_jobs(jobs: list) -> int:
    if not jobs:
        return 0
    rows = [
        {
            "company": j.get("company"),
            "role": j.get("role"),
            "location": j.get("location"),
            "link": j.get("link"),
            "posted_date": j.get("posted_date") or None,
            "is_closed": j.get("is_closed", False),
            "sponsors_visa": j.get("sponsors_visa", True),
            "raw": j,
        }
        for j in jobs if j.get("link")
    ]
    res = get_client().table("cached_jobs").upsert(rows, on_conflict="link").execute()
    return len(res.data or [])


def get_cached_jobs(max_age_hours: int = 24) -> list:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=max_age_hours)).isoformat()
    res = (get_client().table("cached_jobs")
           .select("*")
           .gte("fetched_at", cutoff)
           .execute())
    return res.data or []


# ── PR log ───────────────────────────────────────────────────────

def log_pr_attempt(action: str, username: str, repo_name: str, status: str,
                   details: dict = None) -> dict:
    row = {
        "username": username,
        "repo_name": repo_name,
        "action": action,
        "status": status,
        "pr_url": (details or {}).get("pr_url"),
        "pr_number": (details or {}).get("pr_number"),
        "branch_name": (details or {}).get("branch_name"),
        "error_message": (details or {}).get("error") or (details or {}).get("reason"),
    }
    res = get_client().table("pr_log").insert(row).execute()
    return res.data[0] if res.data else {}


def get_pr_history(username: str) -> list:
    res = (get_client().table("pr_log")
           .select("*")
           .eq("username", username)
           .order("created_at", desc=True)
           .execute())
    return res.data or []


# ── Rate limiting ────────────────────────────────────────────────

def record_rate_hit(identifier: str, endpoint: str = None):
    get_client().table("rate_limits").insert({
        "identifier": identifier,
        "endpoint": endpoint,
    }).execute()


def count_rate_hits(identifier: str, hours: int = 24) -> int:
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    res = (get_client().table("rate_limits")
           .select("id", count="exact")
           .eq("identifier", identifier)
           .gte("created_at", cutoff)
           .execute())
    return res.count or 0


# ── Company benchmarks ───────────────────────────────────────────

def get_company_benchmark(company_name: str) -> dict | None:
    res = (get_client().table("company_benchmarks")
           .select("*")
           .ilike("company_name", company_name)
           .limit(1)
           .execute())
    return res.data[0] if res.data else None


def list_company_names() -> list:
    res = get_client().table("company_benchmarks").select("company_name").order("company_name").execute()
    return [r["company_name"] for r in (res.data or [])]


def upsert_company_benchmark(company_name: str, data: dict):
    row = {"company_name": company_name, **data}
    get_client().table("company_benchmarks").upsert(row, on_conflict="company_name").execute()
