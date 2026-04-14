import asyncio
import base64
from datetime import datetime, timezone

import httpx

from backend.config import (
    GITHUB_API_BASE,
    GITHUB_GRAPHQL_URL,
    github_headers,
    github_graphql_headers,
    GITHUB_TOKEN,
    GITHUB_RATE_LIMIT_AUTHENTICATED,
    GITHUB_RATE_LIMIT_UNAUTHENTICATED,
)


class RateLimitError(Exception):
    def __init__(self, limit: int, remaining: int, reset_at: datetime):
        self.limit = limit
        self.remaining = remaining
        self.reset_at = reset_at
        seconds = max(0, int((reset_at - datetime.now(timezone.utc)).total_seconds()))
        super().__init__(
            f"GitHub API rate limit hit: {remaining}/{limit} remaining. "
            f"Resets in {seconds}s at {reset_at.isoformat()}"
        )


def _check_rate_limit(response: httpx.Response) -> None:
    remaining = response.headers.get("X-RateLimit-Remaining")
    limit = response.headers.get("X-RateLimit-Limit")
    reset_ts = response.headers.get("X-RateLimit-Reset")
    if remaining is not None and int(remaining) == 0:
        reset_at = datetime.fromtimestamp(int(reset_ts), tz=timezone.utc) if reset_ts else datetime.now(timezone.utc)
        raise RateLimitError(
            limit=int(limit) if limit else (GITHUB_RATE_LIMIT_AUTHENTICATED if GITHUB_TOKEN else GITHUB_RATE_LIMIT_UNAUTHENTICATED),
            remaining=0,
            reset_at=reset_at,
        )


async def _get(client: httpx.AsyncClient, url: str, params: dict | None = None) -> dict | list | None:
    resp = await client.get(url, headers=github_headers(), params=params)
    _check_rate_limit(resp)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


async def fetch_profile(username: str) -> dict:
    async with httpx.AsyncClient() as client:
        data = await _get(client, f"{GITHUB_API_BASE}/users/{username}")
    if not data:
        raise ValueError(f"GitHub user '{username}' not found")
    return {
        "login": data["login"],
        "name": data.get("name"),
        "bio": data.get("bio"),
        "location": data.get("location"),
        "company": data.get("company"),
        "blog": data.get("blog"),
        "public_repos": data["public_repos"],
        "followers": data["followers"],
        "following": data["following"],
        "created_at": data["created_at"],
        "avatar_url": data.get("avatar_url"),
        "html_url": data["html_url"],
    }


async def fetch_all_repos(username: str, max_repos: int = 15) -> list[dict]:
    async with httpx.AsyncClient(timeout=20) as client:
        data = await _get(
            client,
            f"{GITHUB_API_BASE}/users/{username}/repos",
            params={"sort": "pushed", "direction": "desc", "per_page": 100, "type": "owner"},
        )
        if not data:
            return []

        repos = []
        for r in data:
            if r.get("fork"):
                continue
            repos.append({
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r.get("description"),
                "language": r.get("language"),
                "stars": r["stargazers_count"],
                "forks": r["forks_count"],
                "updated_at": r["updated_at"],
                "created_at": r["created_at"],
                "topics": r.get("topics", []),
                "html_url": r["html_url"],
                "size": r.get("size", 0),
                "default_branch": r.get("default_branch", "main"),
                "languages": {},
            })
            if len(repos) >= max_repos:
                break

        # Fetch languages per repo in parallel with semaphore
        semaphore = asyncio.Semaphore(10)

        async def _fetch_lang(repo: dict) -> None:
            async with semaphore:
                try:
                    lang_data = await _get(client, f"{GITHUB_API_BASE}/repos/{username}/{repo['name']}/languages")
                    if lang_data:
                        repo["languages"] = lang_data
                except Exception:
                    pass

        await asyncio.gather(*[_fetch_lang(r) for r in repos])

    return repos


async def fetch_readme(username: str, repo_name: str) -> str | None:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/repos/{username}/{repo_name}/readme",
            headers=github_headers(),
        )
        _check_rate_limit(resp)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        content = resp.json().get("content", "")
        try:
            return base64.b64decode(content).decode("utf-8")
        except Exception:
            return None


async def fetch_commit_activity(username: str, repo_name: str) -> list[dict]:
    """Returns weekly commit activity for the last year (52 weeks)."""
    async with httpx.AsyncClient() as client:
        data = await _get(client, f"{GITHUB_API_BASE}/repos/{username}/{repo_name}/stats/commit_activity")
        # This endpoint returns 202 while computing — retry once
        if data is None:
            await asyncio.sleep(2)
            data = await _get(client, f"{GITHUB_API_BASE}/repos/{username}/{repo_name}/stats/commit_activity")
        return data if isinstance(data, list) else []


async def fetch_recent_commits(username: str, repos: list[dict], days: int = 90) -> int:
    """Count commits authored by user across all repos in the last N days.

    Uses GitHub's commit search API for a single accurate count instead
    of looping per-repo (which burned rate limit and had a date bug).
    """
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{GITHUB_API_BASE}/search/commits",
            headers={
                **github_headers(),
                "Accept": "application/vnd.github.cloak-preview+json",
            },
            params={"q": f"author:{username} author-date:>={cutoff}"},
        )
        if resp.status_code != 200:
            return 0
        data = resp.json()
        return data.get("total_count", 0)


# Keep the old per-repo version as fallback
async def fetch_recent_commits_per_repo(username: str, repos: list[dict], days: int = 90) -> int:
    """Fallback: count commits per-repo if search API is unavailable."""
    from datetime import timedelta
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    total = 0
    async with httpx.AsyncClient() as client:
        for repo in repos[:15]:
            data = await _get(
                client,
                f"{GITHUB_API_BASE}/repos/{username}/{repo['name']}/commits",
                params={"author": username, "since": since, "per_page": 100},
            )
            if isinstance(data, list):
                total += len(data)
    return total


PINNED_REPOS_QUERY = """
query($login: String!) {
  user(login: $login) {
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes {
        ... on Repository {
          name
          description
          url
          stargazerCount
          forkCount
          primaryLanguage { name }
          repositoryTopics(first: 10) {
            nodes { topic { name } }
          }
        }
      }
    }
  }
}
"""


async def fetch_pinned_repos(username: str) -> list[dict]:
    if not GITHUB_TOKEN:
        return []  # GraphQL requires auth
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GITHUB_GRAPHQL_URL,
            headers=github_graphql_headers(),
            json={"query": PINNED_REPOS_QUERY, "variables": {"login": username}},
        )
        resp.raise_for_status()
        result = resp.json()

    user = result.get("data", {}).get("user")
    if not user:
        return []

    pinned = []
    for node in user["pinnedItems"]["nodes"]:
        pinned.append({
            "name": node["name"],
            "description": node.get("description"),
            "url": node["url"],
            "stars": node["stargazerCount"],
            "forks": node["forkCount"],
            "language": node["primaryLanguage"]["name"] if node.get("primaryLanguage") else None,
            "topics": [t["topic"]["name"] for t in node.get("repositoryTopics", {}).get("nodes", [])],
        })
    return pinned
