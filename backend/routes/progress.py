"""Route handler for progress tracking endpoint.
Plain async function — will be wired to FastAPI in Phase 9."""

from backend.services.progress_tracker import get_progress, compute_deltas


async def get_user_progress(
    username: str,
    role_category: str | None = None,
    days: int = 90,
) -> dict:
    """GET /api/progress/{username}?role_category=...&days=90

    Returns snapshots and human-readable delta descriptions.
    """
    snapshots = get_progress(username, role_category=role_category, days=days)
    deltas = compute_deltas(snapshots)

    latest = snapshots[-1] if snapshots else None

    return {
        "username": username,
        "snapshot_count": len(snapshots),
        "latest_score": latest.get("overall_score") if latest else None,
        "latest_timestamp": latest.get("timestamp") if latest else None,
        "deltas": deltas,
        "snapshots": snapshots,
    }
