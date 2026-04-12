"""Route handler for company benchmarking endpoint.
Plain async function — will be wired to FastAPI in Phase 9."""

import asyncio

from backend.services.github_service import fetch_profile, fetch_all_repos, fetch_readme
from backend.services.company_benchmarks import benchmark_user_against_company, list_companies


async def get_benchmark(username: str, company: str) -> dict:
    """GET /api/benchmark/{username}/{company}

    Compare a user's GitHub profile against a company's intern cohort.
    """
    profile, repos = await asyncio.gather(
        fetch_profile(username),
        fetch_all_repos(username),
    )

    # Fetch READMEs for top repos
    readme_tasks = {r["name"]: fetch_readme(username, r["name"]) for r in repos[:5]}
    readme_results = await asyncio.gather(*readme_tasks.values())
    readmes = dict(zip(readme_tasks.keys(), readme_results))

    github_data = {"profile": profile, "repos": repos, "readmes": readmes}

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, benchmark_user_against_company, github_data, company
    )

    return result


async def get_available_companies() -> dict:
    """GET /api/benchmark/companies — list available companies."""
    return {"companies": list_companies()}
