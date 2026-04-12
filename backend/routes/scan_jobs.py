"""Route handlers for job scanning endpoints."""

import asyncio
import uuid
from datetime import datetime, timezone

from backend.services.job_board_scanner import scan_jobs_for_user

# In-memory scan status tracker (ephemeral — scan results don't persist across restarts)
_scan_status: dict[str, dict] = {}


async def post_scan_jobs(
    username: str,
    role_filters: list[str] | None = None,
    location_filters: list[str] | None = None,
    max_jobs: int = 30,
) -> dict:
    """POST /api/scan-jobs — start a job scan for a user."""
    scan_id = str(uuid.uuid4())[:8]
    _scan_status[scan_id] = {
        "scan_id": scan_id,
        "username": username,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "total_jobs_scanned": 0,
        "matched_jobs": 0,
        "results": [],
        "error": None,
    }

    async def _run_scan():
        try:
            results = await scan_jobs_for_user(
                username=username,
                role_filters=role_filters,
                location_filters=location_filters,
                max_jobs=max_jobs,
            )
            _scan_status[scan_id].update({
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "total_jobs_scanned": len(results),
                "matched_jobs": sum(1 for r in results if r.get("match_score", 0) > 0),
                "results": results,
            })
        except Exception as e:
            _scan_status[scan_id].update({
                "status": "failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
            })

    asyncio.create_task(_run_scan())
    return {"scan_id": scan_id, "status": "running"}


async def get_scan_jobs_status(scan_id: str) -> dict:
    """GET /api/scan-jobs/status/{scan_id} — check scan progress."""
    if scan_id in _scan_status:
        status = _scan_status[scan_id]
        response = {
            "scan_id": status["scan_id"],
            "username": status["username"],
            "status": status["status"],
            "started_at": status["started_at"],
            "completed_at": status["completed_at"],
            "total_jobs_scanned": status["total_jobs_scanned"],
            "matched_jobs": status["matched_jobs"],
            "error": status["error"],
        }
        if status["status"] == "completed":
            response["results"] = status["results"]
        return response

    return {"scan_id": scan_id, "status": "not_found", "error": "Scan ID not found"}
