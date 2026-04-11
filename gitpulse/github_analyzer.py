import requests
from datetime import datetime, timezone
from gitpulse import config


def _get(url, params=None):
    resp = requests.get(url, headers=config.github_headers(), params=params)
    remaining = resp.headers.get("X-RateLimit-Remaining")
    if remaining and int(remaining) < 10:
        print(f"  ⚠ GitHub API rate limit low: {remaining} requests remaining")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def fetch_user(username):
    data = _get(f"{config.GITHUB_API_BASE}/users/{username}")
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


def fetch_repos(username, max_repos=30):
    data = _get(
        f"{config.GITHUB_API_BASE}/users/{username}/repos",
        params={"sort": "updated", "per_page": max_repos, "type": "owner"},
    )
    if not data:
        return []
    repos = []
    for r in data:
        if r.get("fork"):
            continue
        repos.append({
            "name": r["name"],
            "description": r.get("description"),
            "language": r.get("language"),
            "stars": r["stargazers_count"],
            "forks": r["forks_count"],
            "updated_at": r["updated_at"],
            "topics": r.get("topics", []),
            "html_url": r["html_url"],
            "has_readme": True,  # checked later if needed
            "size": r.get("size", 0),
        })
    return repos


def fetch_languages(username, repos):
    languages = {}
    for repo in repos[:20]:  # cap to avoid rate limit
        data = _get(f"{config.GITHUB_API_BASE}/repos/{username}/{repo['name']}/languages")
        if data:
            for lang, bytes_count in data.items():
                languages[lang] = languages.get(lang, 0) + bytes_count
    return dict(sorted(languages.items(), key=lambda x: x[1], reverse=True))


def fetch_contribution_stats(username):
    data = _get(
        f"{config.GITHUB_API_BASE}/users/{username}/events/public",
        params={"per_page": 100},
    )
    if not data:
        return {}
    now = datetime.now(timezone.utc)
    counts = {}
    for event in data:
        created = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        days_ago = (now - created).days
        if days_ago <= 90:
            event_type = event["type"]
            counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def analyze_profile(username):
    print(f"\n📊 Analyzing GitHub profile: {username}")
    user = fetch_user(username)
    print(f"  ✓ User info loaded: {user.get('name') or username}")

    repos = fetch_repos(username)
    print(f"  ✓ Found {len(repos)} repos (excluding forks)")

    languages = fetch_languages(username, repos)
    print(f"  ✓ Detected {len(languages)} languages")

    contributions = fetch_contribution_stats(username)
    print(f"  ✓ Loaded recent activity ({sum(contributions.values())} events in last 90 days)")

    top_repos = sorted(repos, key=lambda r: r["stars"], reverse=True)[:5]
    total_stars = sum(r["stars"] for r in repos)
    total_forks = sum(r["forks"] for r in repos)
    primary_languages = list(languages.keys())[:5]

    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    account_age = (datetime.now(timezone.utc) - created).days

    return {
        "user": user,
        "repos": repos,
        "languages": languages,
        "contributions": contributions,
        "top_repos": top_repos,
        "summary": {
            "total_stars": total_stars,
            "total_forks": total_forks,
            "primary_languages": primary_languages,
            "repo_count": len(repos),
            "account_age_days": account_age,
        },
    }
