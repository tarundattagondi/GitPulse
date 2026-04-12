"""Route handler for tri-source matching endpoint.
Accepts multipart form: github_username, jd_text, resume file upload.
Plain async function — will be wired to FastAPI in Phase 9."""

import asyncio

from backend.services.github_service import fetch_profile, fetch_all_repos, fetch_readme
from backend.services.jd_analyzer import analyze_jd
from backend.services.resume_parser import parse_resume
from backend.services.tri_match import tri_source_match


async def post_tri_match(
    github_username: str,
    jd_text: str,
    resume_bytes: bytes,
    resume_filename: str,
) -> dict:
    """POST /api/tri-match (multipart form)

    Form fields:
      - github_username: str
      - jd_text: str
      - resume: file upload (PDF, DOCX, or TXT)

    Returns tri-source match result.
    """
    loop = asyncio.get_event_loop()

    # Fetch GitHub data
    profile, repos = await asyncio.gather(
        fetch_profile(github_username),
        fetch_all_repos(github_username),
    )
    readme_tasks = {r["name"]: fetch_readme(github_username, r["name"]) for r in repos[:5]}
    readme_results = await asyncio.gather(*readme_tasks.values())
    readmes = dict(zip(readme_tasks.keys(), readme_results))

    github_data = {"profile": profile, "repos": repos, "readmes": readmes}

    # Parse resume (CPU-bound Claude call)
    resume_data = await loop.run_in_executor(None, parse_resume, resume_bytes, resume_filename)

    # Analyze JD
    jd_analysis = await loop.run_in_executor(None, analyze_jd, jd_text)

    # Tri-source match
    result = await loop.run_in_executor(None, tri_source_match, github_data, resume_data, jd_analysis)

    return {
        "github_username": github_username,
        "resume_skills_found": len(resume_data.get("skills", [])),
        "resume_projects_found": len(resume_data.get("projects", [])),
        "jd_role_category": jd_analysis.get("role_category", "other"),
        "match_result": result,
    }
