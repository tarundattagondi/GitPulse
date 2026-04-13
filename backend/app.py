"""FastAPI application — wires all endpoints from Phases 1-8."""

import sys
import time
import logging
import traceback
from typing import Optional

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.config import validate

# ── App setup ─────────────────────────────────────────────────────
app = FastAPI(
    title="GitPulse API",
    description="Autonomous GitHub career agent — scores profiles, scans internships, opens PRs",
    version="0.1.0",
)

# ── CORS — MUST be first middleware, before any routes ────────────
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost(:\d+)?|.*\.vercel\.app|.*\.up\.railway\.app)|chrome-extension://.*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Logging ───────────────────────────────────────────────────────
logger = logging.getLogger("gitpulse")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# ── Rate limiter (Supabase-backed) ────────────────────────────────
DAILY_LIMIT = 5
RATE_LIMITED_PREFIXES = [
    "/api/analyze", "/api/score", "/api/scan-jobs", "/api/tri-match",
    "/api/interview-prep", "/api/pr/preview", "/api/pr/open",
]


@app.middleware("http")
async def log_and_rate_limit(request: Request, call_next):
    start = time.time()

    # Skip rate limiting for OPTIONS (CORS preflight) and non-API paths
    if request.method != "OPTIONS":
        path = request.url.path
        if any(path.startswith(p) for p in RATE_LIMITED_PREFIXES):
            api_key = request.headers.get("X-Anthropic-Key")
            if not api_key:
                client_ip = request.client.host if request.client else "unknown"
                try:
                    from backend.storage import record_rate_hit, count_rate_hits
                    total = count_rate_hits(client_ip, hours=24)
                    if total >= DAILY_LIMIT:
                        return JSONResponse(
                            status_code=429,
                            content={
                                "error": "rate_limit_exceeded",
                                "message": f"Daily limit of {DAILY_LIMIT} analyses exceeded. "
                                           f"Pass X-Anthropic-Key header for unlimited access.",
                                "limit": DAILY_LIMIT,
                                "used": total,
                            },
                        )
                    record_rate_hit(client_ip, endpoint=path)
                except Exception:
                    pass

    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration:.2f}s)")
    return response


# ── Global exception handlers ────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "bad_request", "message": str(exc)},
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(
        status_code=403,
        content={"error": "forbidden", "message": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": str(exc)},
    )


# ── Health check ──────────────────────────────────────────────────
@app.get("/")
async def health():
    return {"status": "ok", "service": "gitpulse", "version": "0.1.0"}


# ── Phase 1: Analyze & Score ──────────────────────────────────────
from backend.services.analyzer import analyze_and_score  # noqa: E402


class AnalyzeRequest(BaseModel):
    jd_text: str = ""


@app.post("/api/analyze/{username}")
async def analyze_post(username: str, request: AnalyzeRequest, role_category: str = "other"):
    import asyncio as _aio

    jd_text = (request.jd_text or "").strip()
    has_jd = len(jd_text) >= 50
    mode = "jd_match" if has_jd else "profile_audit"
    jd = jd_text if has_jd else None

    result = await analyze_and_score(username, job_description=jd, role_category=role_category)
    score = result["score"]

    category_scores = {}
    for cat, d in score.get("breakdown", {}).items():
        category_scores[cat] = d.get("score", d) if isinstance(d, dict) else d

    jd_analysis = None
    match_result = None
    recommendations = None
    if has_jd:
        loop = _aio.get_event_loop()
        from backend.services.jd_analyzer import analyze_jd
        from backend.services.matcher import match_profile_to_jd
        from backend.services.recommender import generate_recommendations

        github_data = {"profile": result["profile"], "repos": result["repos"], "readmes": result["readmes"]}
        jd_analysis = await loop.run_in_executor(None, analyze_jd, jd)
        match_result = await loop.run_in_executor(None, match_profile_to_jd, github_data, jd_analysis)
        recommendations = await loop.run_in_executor(None, generate_recommendations, github_data, jd_analysis, match_result)

    total_stars = sum(r.get("stars", 0) for r in result["repos"])

    full_result = {
        "username": username,
        "mode": mode,
        "overall_score": score.get("total_score", 0),
        "category_scores": category_scores,
        "score": score,
        "jd_analysis": jd_analysis,
        "match_result": match_result,
        "recommendations": recommendations,
        "github_summary": {
            "profile": result["profile"],
            "repos": result["repos"][:15],
            "total_stars": total_stars,
            "repo_count": len(result["repos"]),
            "commit_count_90d": result.get("commit_count_90d", 0),
        },
        "snapshot": result["snapshot"],
    }

    from backend.storage import save_analysis
    save_analysis(
        username=username,
        role_category=role_category,
        overall_score=score.get("total_score", 0),
        category_scores=category_scores,
        jd_analysis=jd_analysis,
        match_result=match_result,
        recommendations=recommendations,
        github_summary=full_result["github_summary"],
    )

    return full_result


@app.get("/api/analysis/{username}/latest")
async def get_latest_analysis_endpoint(username: str):
    from backend.storage import get_latest_analysis
    data = get_latest_analysis(username)
    if not data:
        raise HTTPException(status_code=404, detail="No analysis found. Run one first.")
    return data


@app.get("/api/analyze/{username}")
async def analyze_get(username: str, role_category: str = "other"):
    result = await analyze_and_score(username, role_category=role_category)
    return {
        "username": username,
        "profile": result["profile"],
        "repos_count": len(result["repos"]),
        "score": result["score"],
        "snapshot": result["snapshot"],
    }


@app.get("/api/score/{username}")
async def score(username: str, job_description: str = None, role_category: str = "other"):
    result = await analyze_and_score(username, job_description=job_description, role_category=role_category)
    return {
        "username": username,
        "score": result["score"],
    }


# ── Phase 3: Job scanning ────────────────────────────────────────
from backend.services.job_board_scanner import fetch_simplify_jobs, filter_jobs  # noqa: E402
from backend.routes.scan_jobs import post_scan_jobs, get_scan_jobs_status  # noqa: E402


class ScanJobsRequest(BaseModel):
    username: str
    role_filters: Optional[list[str]] = None
    location_filters: Optional[list[str]] = None
    max_jobs: int = 30


@app.post("/api/scan-jobs")
async def scan_jobs(req: ScanJobsRequest):
    return await post_scan_jobs(
        username=req.username,
        role_filters=req.role_filters,
        location_filters=req.location_filters,
        max_jobs=req.max_jobs,
    )


@app.get("/api/scan-jobs/status/{scan_id}")
async def scan_jobs_status(scan_id: str):
    return await get_scan_jobs_status(scan_id)


@app.get("/api/jobs")
async def list_jobs(
    role: Optional[str] = None,
    location: Optional[str] = None,
    exclude_closed: bool = True,
):
    jobs = await fetch_simplify_jobs()
    role_kw = role.split(",") if role else None
    loc_kw = location.split(",") if location else None
    filtered = filter_jobs(jobs, role_keywords=role_kw, location_keywords=loc_kw, exclude_closed=exclude_closed)
    return {
        "total": len(filtered),
        "jobs": [j.to_dict() for j in filtered[:50]],
    }


# ── Phase 4: PR agent ────────────────────────────────────────────
from backend.routes.pr import post_pr_preview, post_pr_open  # noqa: E402


class PRPreviewRequest(BaseModel):
    username: str
    repo_name: str
    token: str


class PROpenRequest(BaseModel):
    username: str
    repo_name: str
    new_readme_content: str
    token: str


@app.post("/api/pr/preview")
async def pr_preview(req: PRPreviewRequest):
    return await post_pr_preview(req.username, req.repo_name, req.token)


@app.post("/api/pr/open")
async def pr_open(req: PROpenRequest):
    return await post_pr_open(req.username, req.repo_name, req.new_readme_content, req.token)


# ── Phase 5: Progress tracking ───────────────────────────────────
from backend.routes.progress import get_user_progress  # noqa: E402


@app.get("/api/progress/{username}")
async def progress(username: str, role_category: Optional[str] = None, days: int = 90):
    return await get_user_progress(username, role_category=role_category, days=days)


# ── Phase 6: Tri-source matching ─────────────────────────────────
from backend.routes.tri_match import post_tri_match  # noqa: E402


@app.post("/api/tri-match")
async def tri_match(
    github_username: str = Form(...),
    jd_text: str = Form(...),
    resume: UploadFile = File(...),
):
    resume_bytes = await resume.read()
    return await post_tri_match(github_username, jd_text, resume_bytes, resume.filename)


# ── Phase 7: Company benchmarking ─────────────────────────────────
from backend.routes.benchmark import get_benchmark, get_available_companies  # noqa: E402


@app.get("/api/benchmark/companies")
async def benchmark_companies():
    return await get_available_companies()


@app.get("/api/benchmark/{username}/{company}")
async def benchmark(username: str, company: str):
    return await get_benchmark(username, company)


# ── Phase 8: Interview prep ──────────────────────────────────────
from backend.routes.interview_prep import post_interview_prep  # noqa: E402


class InterviewPrepRequest(BaseModel):
    username: str
    jd_text: str


@app.post("/api/interview-prep")
async def interview_prep(req: InterviewPrepRequest):
    return await post_interview_prep(req.username, req.jd_text)


# ── Startup ──────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    validate()
    logger.info("GitPulse API started")


# Startup confirmation for Railway logs
print(f"GitPulse app loaded with {len(app.user_middleware)} middleware", file=sys.stderr)
