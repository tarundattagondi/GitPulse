"""Route handler for interview prep generation.
Plain async function — will be wired to FastAPI in Phase 9."""

import asyncio

from backend.services.github_service import fetch_profile, fetch_all_repos, fetch_readme
from backend.services.jd_analyzer import analyze_jd
from backend.services.matcher import match_profile_to_jd
from backend.services.interview_generator import generate_interview_prep


async def post_interview_prep(username: str, jd_text: str) -> dict:
    """POST /api/interview-prep

    Request body: {username, jd_text}
    Returns tailored interview prep material.
    """
    loop = asyncio.get_event_loop()

    # Fetch GitHub data
    profile, repos = await asyncio.gather(
        fetch_profile(username),
        fetch_all_repos(username),
    )
    readme_tasks = {r["name"]: fetch_readme(username, r["name"]) for r in repos[:5]}
    readme_results = await asyncio.gather(*readme_tasks.values())
    readmes = dict(zip(readme_tasks.keys(), readme_results))

    github_data = {"profile": profile, "repos": repos, "readmes": readmes}

    # Analyze JD and match (CPU-bound Claude calls)
    jd_analysis = await loop.run_in_executor(None, analyze_jd, jd_text)
    match_result = await loop.run_in_executor(None, match_profile_to_jd, github_data, jd_analysis)

    # Generate interview prep
    result = await loop.run_in_executor(
        None, generate_interview_prep, github_data, jd_analysis, match_result
    )

    return {
        "username": username,
        "role_category": jd_analysis.get("role_category", "other"),
        "overall_match_pct": match_result.get("overall_match_pct", 0),
        "prep": result,
    }
