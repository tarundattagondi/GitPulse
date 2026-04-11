"""Route handlers for PR preview and creation endpoints.
These are plain async functions that will be wired to FastAPI in Phase 9.
Token comes in request body, never stored."""

import asyncio

from backend.services.pr_agent import preview_pr, open_readme_pr


async def post_pr_preview(username: str, repo_name: str, token: str) -> dict:
    """POST /api/pr/preview — preview a README improvement without writes.

    Request body: {username, repo_name, token}
    Response: {current_readme, suggested_readme, diff_summary, stats}
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, preview_pr, username, repo_name, token)
    return result


async def post_pr_open(
    username: str,
    repo_name: str,
    new_readme_content: str,
    token: str,
) -> dict:
    """POST /api/pr/open — open a PR with improved README.

    Request body: {username, repo_name, new_readme_content, token}
    Response: {pr_url, pr_number, branch_name}
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, open_readme_pr, username, repo_name, new_readme_content, token
    )
    return result
