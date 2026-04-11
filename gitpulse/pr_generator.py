import base64
import json
import time
import requests
import anthropic
from gitpulse import config


def _github_put(url, data):
    resp = requests.put(url, headers=config.github_headers(), json=data)
    resp.raise_for_status()
    return resp.json()


def _github_post(url, data):
    resp = requests.post(url, headers=config.github_headers(), json=data)
    resp.raise_for_status()
    return resp.json()


def _github_patch(url, data):
    resp = requests.patch(url, headers=config.github_headers(), json=data)
    resp.raise_for_status()
    return resp.json()


def generate_readme(profile, repo):
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        system="You are a technical writer. Generate a professional README.md. Return ONLY the markdown content, no wrapping fences.",
        messages=[{
            "role": "user",
            "content": (
                f"Generate a README.md for this GitHub repo:\n"
                f"- Name: {repo['name']}\n"
                f"- Description: {repo.get('description') or 'No description'}\n"
                f"- Language: {repo.get('language') or 'Unknown'}\n"
                f"- Stars: {repo.get('stars', 0)}\n"
                f"- Topics: {', '.join(repo.get('topics', []))}\n\n"
                f"Include: Overview, Features, Installation, Usage, Contributing, License sections."
            ),
        }],
    )
    return message.content[0].text


def generate_profile_readme(profile):
    client = anthropic.Anthropic()
    user = profile["user"]
    summary = profile["summary"]
    languages = list(profile["languages"].keys())[:8]
    top_repos = profile["top_repos"][:5]

    repos_text = "\n".join(
        f"- {r['name']}: {r.get('description') or 'No description'} (⭐ {r['stars']})"
        for r in top_repos
    )

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        system="You are a technical writer. Generate a GitHub profile README.md. Return ONLY the markdown content.",
        messages=[{
            "role": "user",
            "content": (
                f"Generate a GitHub profile README for:\n"
                f"- Name: {user.get('name') or user['login']}\n"
                f"- Bio: {user.get('bio') or 'Software developer'}\n"
                f"- Location: {user.get('location') or 'Not specified'}\n"
                f"- Languages: {', '.join(languages)}\n"
                f"- Total stars: {summary['total_stars']}\n"
                f"- Total repos: {summary['repo_count']}\n"
                f"- Top projects:\n{repos_text}\n\n"
                f"Make it visually appealing with language badges, stats, and a clean layout."
            ),
        }],
    )
    return message.content[0].text


def suggest_improvements(profile, score):
    improvements = []
    repos = profile.get("repos", [])

    # Check for repos without descriptions
    no_desc = [r for r in repos if not r.get("description")]
    if no_desc:
        for repo in no_desc[:3]:
            improvements.append({
                "priority": 1,
                "type": "add_description",
                "repo": repo["name"],
                "description": f"Add a description to '{repo['name']}'",
                "can_automate": True,
            })

    # Check for repos without topics
    no_topics = [r for r in repos if not r.get("topics")]
    if no_topics:
        for repo in no_topics[:3]:
            improvements.append({
                "priority": 2,
                "type": "add_topics",
                "repo": repo["name"],
                "description": f"Add topics/tags to '{repo['name']}'",
                "can_automate": True,
            })

    # Check if profile README exists
    username = profile["user"]["login"]
    try:
        resp = requests.get(
            f"{config.GITHUB_API_BASE}/repos/{username}/{username}/contents/README.md",
            headers=config.github_headers(),
        )
        if resp.status_code == 404:
            improvements.append({
                "priority": 1,
                "type": "create_profile_readme",
                "repo": username,
                "description": "Create a GitHub profile README",
                "can_automate": True,
            })
    except Exception:
        pass

    # Add recommendations from score
    if score and score.get("recommendations"):
        for i, rec in enumerate(score["recommendations"][:3]):
            improvements.append({
                "priority": 3,
                "type": "recommendation",
                "repo": None,
                "description": rec,
                "can_automate": False,
            })

    improvements.sort(key=lambda x: x["priority"])
    return improvements


def open_pr(username, repo, file_path, content, title, body):
    branch = f"gitpulse/{file_path.replace('/', '-').replace('.', '-')}-{int(time.time())}"

    # Get default branch SHA
    resp = requests.get(
        f"{config.GITHUB_API_BASE}/repos/{username}/{repo}/git/ref/heads/main",
        headers=config.github_headers(),
    )
    if resp.status_code == 404:
        resp = requests.get(
            f"{config.GITHUB_API_BASE}/repos/{username}/{repo}/git/ref/heads/master",
            headers=config.github_headers(),
        )
    resp.raise_for_status()
    sha = resp.json()["object"]["sha"]
    base_branch = "main" if "main" in resp.url else "master"

    # Create branch
    _github_post(
        f"{config.GITHUB_API_BASE}/repos/{username}/{repo}/git/refs",
        {"ref": f"refs/heads/{branch}", "sha": sha},
    )

    # Create/update file
    encoded = base64.b64encode(content.encode()).decode()
    _github_put(
        f"{config.GITHUB_API_BASE}/repos/{username}/{repo}/contents/{file_path}",
        {
            "message": f"Add {file_path} via GitPulse",
            "content": encoded,
            "branch": branch,
        },
    )

    # Open PR
    pr = _github_post(
        f"{config.GITHUB_API_BASE}/repos/{username}/{repo}/pulls",
        {
            "title": title,
            "body": body + "\n\n---\n*Generated by [GitPulse](https://github.com/tarundattagondi/GitPulse)*",
            "head": branch,
            "base": base_branch,
        },
    )
    return pr["html_url"]


def execute_improvements(username, profile, improvements, auto_pr=False):
    results = []
    automatable = [imp for imp in improvements if imp["can_automate"]]

    if not automatable:
        print("  No automatable improvements found.")
        return results

    for imp in automatable:
        try:
            if imp["type"] == "add_description" and imp["repo"]:
                client = anthropic.Anthropic()
                msg = client.messages.create(
                    model=config.CLAUDE_MODEL,
                    max_tokens=100,
                    messages=[{
                        "role": "user",
                        "content": f"Write a one-line GitHub repo description for a project called '{imp['repo']}' written in {profile['languages']}. Return ONLY the description text, nothing else.",
                    }],
                )
                desc = msg.content[0].text.strip().strip('"')
                if auto_pr:
                    _github_patch(
                        f"{config.GITHUB_API_BASE}/repos/{username}/{imp['repo']}",
                        {"description": desc},
                    )
                    results.append({"type": "add_description", "repo": imp["repo"], "status": "applied", "value": desc})
                    print(f"  ✓ Added description to {imp['repo']}: {desc}")
                else:
                    results.append({"type": "add_description", "repo": imp["repo"], "status": "suggested", "value": desc})
                    print(f"  → Suggested description for {imp['repo']}: {desc}")

            elif imp["type"] == "create_profile_readme":
                readme_content = generate_profile_readme(profile)
                if auto_pr:
                    # Check if the profile repo exists, create if not
                    resp = requests.get(
                        f"{config.GITHUB_API_BASE}/repos/{username}/{username}",
                        headers=config.github_headers(),
                    )
                    if resp.status_code == 404:
                        _github_post(
                            f"{config.GITHUB_API_BASE}/user/repos",
                            {"name": username, "description": "My GitHub profile", "auto_init": True},
                        )
                        time.sleep(2)
                    pr_url = open_pr(
                        username, username, "README.md", readme_content,
                        "Add profile README via GitPulse",
                        "This PR adds a professional GitHub profile README with your stats, top projects, and language badges.",
                    )
                    results.append({"type": "create_profile_readme", "status": "pr_opened", "url": pr_url})
                    print(f"  ✓ Opened PR for profile README: {pr_url}")
                else:
                    results.append({"type": "create_profile_readme", "status": "suggested", "preview": readme_content[:200]})
                    print(f"  → Generated profile README (use --auto-pr to create a PR)")

            elif imp["type"] == "add_topics" and imp["repo"]:
                client = anthropic.Anthropic()
                repo_data = next((r for r in profile["repos"] if r["name"] == imp["repo"]), None)
                lang = repo_data.get("language", "unknown") if repo_data else "unknown"
                msg = client.messages.create(
                    model=config.CLAUDE_MODEL,
                    max_tokens=100,
                    messages=[{
                        "role": "user",
                        "content": f"Suggest 3-5 GitHub topics for a {lang} repo called '{imp['repo']}'. Return ONLY a JSON array of lowercase topic strings.",
                    }],
                )
                from gitpulse.utils import parse_json_response
                topics = parse_json_response(msg.content[0].text)
                if auto_pr:
                    requests.put(
                        f"{config.GITHUB_API_BASE}/repos/{username}/{imp['repo']}/topics",
                        headers={**config.github_headers(), "Accept": "application/vnd.github.mercy-preview+json"},
                        json={"names": topics},
                    )
                    results.append({"type": "add_topics", "repo": imp["repo"], "status": "applied", "topics": topics})
                    print(f"  ✓ Added topics to {imp['repo']}: {', '.join(topics)}")
                else:
                    results.append({"type": "add_topics", "repo": imp["repo"], "status": "suggested", "topics": topics})
                    print(f"  → Suggested topics for {imp['repo']}: {', '.join(topics)}")

        except Exception as e:
            print(f"  ✗ Failed to process {imp['type']} for {imp.get('repo', 'profile')}: {e}")
            results.append({"type": imp["type"], "repo": imp.get("repo"), "status": "failed", "error": str(e)})

    return results
