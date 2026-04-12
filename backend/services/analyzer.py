"""Main analyze orchestrator: fetches GitHub data, scores, and saves a progress snapshot."""

import asyncio

from backend.services.github_service import (
    fetch_profile,
    fetch_all_repos,
    fetch_readme,
    fetch_recent_commits,
    fetch_pinned_repos,
)
from backend.services.scorer import score_profile_full
from backend.services.progress_tracker import save_snapshot


async def analyze_and_score(
    username: str,
    job_description: str | None = None,
    role_category: str = "other",
) -> dict:
    """Full pipeline: fetch GitHub data, score, save snapshot.

    Returns {profile, repos, readmes, pinned, commit_count_90d, score, snapshot}.
    """
    # Fetch GitHub data
    profile, repos = await asyncio.gather(
        fetch_profile(username),
        fetch_all_repos(username),
    )

    # Fetch READMEs + commits + pinned concurrently
    readme_tasks = {r["name"]: fetch_readme(username, r["name"]) for r in repos[:5]}
    readme_results = await asyncio.gather(*readme_tasks.values())
    readmes = dict(zip(readme_tasks.keys(), readme_results))

    commit_count, pinned = await asyncio.gather(
        fetch_recent_commits(username, repos),
        fetch_pinned_repos(username),
    )

    # Score
    score = score_profile_full(profile, repos, readmes, commit_count, job_description)

    # Aggregate metadata
    total_stars = sum(r.get("stars", 0) for r in repos)
    metadata = {"repo_count": len(repos), "total_stars": total_stars}

    # Save snapshot (auto-tracks progress)
    snapshot = save_snapshot(username, role_category, score, metadata)

    return {
        "profile": profile,
        "repos": repos,
        "readmes": readmes,
        "pinned": pinned,
        "commit_count_90d": commit_count,
        "score": score,
        "snapshot": snapshot,
    }
