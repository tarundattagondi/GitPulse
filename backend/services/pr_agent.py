"""Autonomous PR agent for README improvements.

Hard safety rules:
1. ONLY touches README.md — no other files, ever.
2. NEVER force-pushes.
3. NEVER pushes to the default branch directly — always a feature branch.
4. NEVER opens a PR on a repo the token doesn't own.
5. Always creates a feature branch: gitpulse/readme-improvement-{timestamp}.
6. Logs every attempt to backend/data/pr_log.json.
"""

import difflib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from github import Auth, Github, GithubException

from backend.config import DATA_DIR
from backend.storage import read_json, write_json

PR_LOG_PATH = DATA_DIR / "pr_log.json"
ALLOWED_FILE = "README.md"


def _log_attempt(action: str, username: str, repo_name: str, status: str, details: dict | None = None):
    """Append an entry to the PR log."""
    log = read_json(PR_LOG_PATH)
    if "entries" not in log:
        log["entries"] = []
    log["entries"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "username": username,
        "repo": repo_name,
        "status": status,
        "details": details or {},
    })
    write_json(PR_LOG_PATH, log)


def _verify_ownership(gh: Github, username: str, repo_name: str):
    """Verify the authenticated user owns the target repo. Raises on violation."""
    authed_user = gh.get_user()
    authed_login = authed_user.login

    try:
        repo = gh.get_repo(f"{username}/{repo_name}")
    except GithubException as e:
        raise PermissionError(f"Cannot access repo {username}/{repo_name}: {e.data.get('message', str(e))}")

    # Owner check: repo owner must match authenticated user
    if repo.owner.login.lower() != authed_login.lower():
        raise PermissionError(
            f"Safety violation: authenticated as '{authed_login}' but repo is owned by '{repo.owner.login}'. "
            f"GitPulse will only open PRs on repos you own."
        )

    # Fork check: don't PR on forks either
    if repo.fork:
        raise PermissionError(
            f"Safety violation: {username}/{repo_name} is a fork. "
            f"GitPulse will only open PRs on your own (non-fork) repositories."
        )

    return repo


def preview_pr(username: str, repo_name: str, token: str) -> dict:
    """Preview a README improvement without any GitHub writes.

    Returns {current_readme, suggested_readme, diff_summary}.
    """
    _log_attempt("preview", username, repo_name, "started")

    try:
        gh = Github(auth=Auth.Token(token))
        repo = _verify_ownership(gh, username, repo_name)

        # Fetch current README
        try:
            readme_file = repo.get_contents(ALLOWED_FILE)
            current_readme = readme_file.decoded_content.decode("utf-8")
        except GithubException:
            current_readme = ""

        # Generate improved README via recommender
        import anthropic
        from backend.config import CLAUDE_MODEL

        client = anthropic.Anthropic()

        # Get repo metadata for context
        languages = repo.get_languages()
        topics = repo.get_topics()
        description = repo.description or "No description"

        prompt = (
            f"Rewrite this README.md to be publication-ready and professional.\n\n"
            f"Repository: {repo.full_name}\n"
            f"Description: {description}\n"
            f"Languages: {', '.join(languages.keys())}\n"
            f"Topics: {', '.join(topics)}\n"
            f"Stars: {repo.stargazers_count}\n\n"
            f"Current README:\n```\n{current_readme[:3000]}\n```\n\n"
            f"Write a COMPLETE, improved README.md. Include:\n"
            f"- Project title and badges placeholders\n"
            f"- Clear project description\n"
            f"- Features list\n"
            f"- Tech stack\n"
            f"- Installation instructions with code blocks\n"
            f"- Usage examples with code blocks\n"
            f"- Project structure (if inferable)\n"
            f"- Contributing section\n"
            f"- License section\n\n"
            f"Return ONLY the markdown content. No JSON wrapping. No code fences around the whole thing."
        )

        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=3000,
            system="You are a technical writer. Return only raw markdown content for a README.md file.",
            messages=[{"role": "user", "content": prompt}],
        )
        suggested_readme = message.content[0].text

        # Generate diff summary
        diff_lines = list(difflib.unified_diff(
            current_readme.splitlines(keepends=True),
            suggested_readme.splitlines(keepends=True),
            fromfile="README.md (current)",
            tofile="README.md (suggested)",
            lineterm="",
        ))
        diff_summary = "\n".join(diff_lines[:100])  # cap for display

        additions = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        deletions = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))

        _log_attempt("preview", username, repo_name, "success", {
            "current_length": len(current_readme),
            "suggested_length": len(suggested_readme),
            "additions": additions,
            "deletions": deletions,
        })

        return {
            "current_readme": current_readme,
            "suggested_readme": suggested_readme,
            "diff_summary": diff_summary,
            "stats": {"additions": additions, "deletions": deletions},
        }

    except PermissionError as e:
        _log_attempt("preview", username, repo_name, "blocked", {"reason": str(e)})
        raise
    except Exception as e:
        _log_attempt("preview", username, repo_name, "failed", {"error": str(e)})
        raise


def open_readme_pr(
    username: str,
    repo_name: str,
    new_readme_content: str,
    token: str,
) -> dict:
    """Open a PR with an improved README.md.

    Safety: only README.md, feature branch only, owner-verified, never force-push.
    Returns {pr_url, pr_number, branch_name}.
    """
    _log_attempt("open_pr", username, repo_name, "started")

    try:
        gh = Github(auth=Auth.Token(token))
        repo = _verify_ownership(gh, username, repo_name)
        default_branch = repo.default_branch

        # Create feature branch name with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        branch_name = f"gitpulse/readme-improvement-{timestamp}"

        # Get default branch SHA
        default_ref = repo.get_git_ref(f"heads/{default_branch}")
        base_sha = default_ref.object.sha

        # Create the feature branch
        repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_sha,
        )

        # Check if README exists on the branch
        try:
            existing = repo.get_contents(ALLOWED_FILE, ref=branch_name)
            # Update existing README
            repo.update_file(
                path=ALLOWED_FILE,
                message="docs: improve README via GitPulse",
                content=new_readme_content,
                sha=existing.sha,
                branch=branch_name,
            )
        except GithubException:
            # Create new README
            repo.create_file(
                path=ALLOWED_FILE,
                message="docs: improve README via GitPulse",
                content=new_readme_content,
                branch=branch_name,
            )

        # Open PR
        pr = repo.create_pull(
            title="docs: improve README via GitPulse",
            body=(
                "## README Improvement\n\n"
                "This PR updates the project README with:\n"
                "- Clearer project description\n"
                "- Professional formatting and structure\n"
                "- Installation and usage instructions\n"
                "- Contributing guidelines\n\n"
                "---\n"
                "*Generated by [GitPulse](https://github.com/tarundattagondi/GitPulse) — "
                "an autonomous GitHub career agent.*"
            ),
            head=branch_name,
            base=default_branch,
        )

        result = {
            "pr_url": pr.html_url,
            "pr_number": pr.number,
            "branch_name": branch_name,
        }

        _log_attempt("open_pr", username, repo_name, "success", result)
        return result

    except PermissionError as e:
        _log_attempt("open_pr", username, repo_name, "blocked", {"reason": str(e)})
        raise
    except GithubException as e:
        _log_attempt("open_pr", username, repo_name, "failed", {"error": str(e.data)})
        raise
    except Exception as e:
        _log_attempt("open_pr", username, repo_name, "failed", {"error": str(e)})
        raise
