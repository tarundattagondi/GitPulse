"""Phase 5 test: progress tracking with snapshots and deltas."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import validate
from backend.services.analyzer import analyze_and_score
from backend.services.progress_tracker import (
    get_progress,
    compute_deltas,
    save_snapshot,
    PROGRESS_PATH,
)
from backend.routes.progress import get_user_progress
from backend.storage import read_json


def test_save_and_get():
    """Test save_snapshot and get_progress with synthetic data."""
    print("\n  [Unit] Testing save_snapshot + get_progress...")

    # Save two snapshots with different scores
    s1 = save_snapshot("test_user_p5", "backend", {
        "total_score": 55,
        "breakdown": {
            "skills_match": {"score": 20},
            "project_relevance": {"score": 15},
            "readme_quality": {"score": 10},
            "activity_level": {"score": 5},
            "profile_completeness": {"score": 5},
        },
    }, {"repo_count": 5, "total_stars": 3})

    assert s1["overall_score"] == 55
    assert s1["delta_since_last"] is None  # first snapshot
    print("  ✓ First snapshot saved (no delta)")

    s2 = save_snapshot("test_user_p5", "backend", {
        "total_score": 68,
        "breakdown": {
            "skills_match": {"score": 28},
            "project_relevance": {"score": 18},
            "readme_quality": {"score": 12},
            "activity_level": {"score": 5},
            "profile_completeness": {"score": 5},
        },
    }, {"repo_count": 7, "total_stars": 8})

    assert s2["overall_score"] == 68
    assert s2["delta_since_last"] is not None
    assert s2["delta_since_last"]["overall"] == 13  # 68 - 55
    assert s2["delta_since_last"]["categories"]["skills_match"] == 8  # 28 - 20
    print(f"  ✓ Second snapshot saved (delta: +{s2['delta_since_last']['overall']})")

    # Get progress
    snapshots = get_progress("test_user_p5", role_category="backend")
    assert len(snapshots) >= 2
    print(f"  ✓ get_progress returned {len(snapshots)} snapshots")

    # Compute deltas
    deltas = compute_deltas(snapshots[-2:])
    assert len(deltas) == 1
    assert "+13" in deltas[0]
    print(f"  ✓ compute_deltas: {deltas[0]}")

    # Clean up test data
    history = read_json(PROGRESS_PATH)
    if "test_user_p5" in history:
        del history["test_user_p5"]
        from backend.storage import write_json
        write_json(PROGRESS_PATH, history)
    print("  ✓ Cleaned up test data")


async def test_live_analyze():
    """Run analyze_and_score on tarundattagondi and verify snapshot is saved."""
    username = "tarundattagondi"

    print(f"\n  [Live] Running analyze_and_score for {username}...")
    result = await analyze_and_score(username, role_category="fullstack")

    assert "profile" in result
    assert "score" in result
    assert "snapshot" in result

    score = result["score"]
    snapshot = result["snapshot"]

    print(f"  ✓ Score: {score['total_score']}/100")
    print(f"  ✓ Snapshot saved at {snapshot['timestamp']}")
    print(f"    Role: {snapshot['role_category']}")
    print(f"    Repos: {snapshot['repo_count']}, Stars: {snapshot['total_stars']}")

    for cat, val in snapshot["category_scores"].items():
        print(f"    {cat}: {val}")

    if snapshot["delta_since_last"]:
        delta = snapshot["delta_since_last"]
        print(f"    Delta: {'+' if delta['overall'] >= 0 else ''}{delta['overall']} "
              f"(since {delta['days_since_last']}d ago)")
    else:
        print("    Delta: first snapshot (no prior data)")

    # Verify it's in get_progress
    progress = get_progress(username)
    assert len(progress) >= 1
    print(f"  ✓ get_progress shows {len(progress)} total snapshots")

    return result


async def test_route():
    """Test the route handler."""
    print(f"\n  [Route] Testing GET /api/progress/tarundattagondi...")
    response = await get_user_progress("tarundattagondi")

    assert response["username"] == "tarundattagondi"
    assert response["snapshot_count"] >= 1
    assert response["latest_score"] is not None
    print(f"  ✓ Latest score: {response['latest_score']}/100")
    print(f"  ✓ Snapshots: {response['snapshot_count']}")
    if response["deltas"]:
        for d in response["deltas"]:
            print(f"    {d}")
    else:
        print("    (single snapshot, no deltas yet)")


if __name__ == "__main__":
    validate()

    print(f"{'=' * 60}")
    print(f"  Phase 5 — Progress Tracking Tests")
    print(f"{'=' * 60}")

    # Unit tests (synchronous)
    test_save_and_get()

    # Live test
    asyncio.run(test_live_analyze())

    # Route test
    asyncio.run(test_route())

    print(f"\n{'=' * 60}")
    print(f"  Phase 5 — All tests passed ✓")
    print(f"{'=' * 60}\n")
