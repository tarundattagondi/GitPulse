import base64
import re
import anthropic
from gitpulse import config


INTERNSHIP_REPOS = [
    "SimplifyJobs/Summer2026-Internships",
    "SimplifyJobs/New-Grad-Positions",
]


def _parse_markdown_table(text):
    jobs = []
    lines = text.split("\n")
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        # Skip header/separator rows
        if all(c.replace("-", "").replace(":", "").strip() == "" for c in cells):
            continue
        if cells[0].lower() in ("company", "name", "---"):
            continue
        # Extract link if present
        link_match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", cells[0])
        company = link_match.group(1) if link_match else cells[0]
        url_match = re.search(r"\(([^)]+)\)", line)
        url = url_match.group(1) if url_match else ""

        jobs.append({
            "company": company.strip(),
            "role": cells[1].strip() if len(cells) > 1 else "",
            "location": cells[2].strip() if len(cells) > 2 else "",
            "url": url,
            "source": "github-repo",
        })
    return jobs


def scan_github_repos(keywords=None):
    import requests

    jobs = []
    for repo in INTERNSHIP_REPOS:
        try:
            resp = requests.get(
                f"{config.GITHUB_API_BASE}/repos/{repo}/readme",
                headers=config.github_headers(),
            )
            if resp.status_code != 200:
                continue
            content = base64.b64decode(resp.json()["content"]).decode("utf-8")
            parsed = _parse_markdown_table(content)
            jobs.extend(parsed[:50])  # cap per repo
        except Exception as e:
            print(f"  ⚠ Could not fetch {repo}: {e}")
    if keywords:
        kw_lower = [k.lower() for k in keywords]
        jobs = [
            j for j in jobs
            if any(k in j["company"].lower() or k in j["role"].lower() for k in kw_lower)
        ]
    return jobs


def search_with_claude(profile_summary):
    try:
        client = anthropic.Anthropic()
        languages = ", ".join(profile_summary.get("primary_languages", []))
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            system="You are a career advisor for software engineers. Return only valid JSON.",
            messages=[{
                "role": "user",
                "content": (
                    f"A developer skilled in {languages} with "
                    f"{profile_summary.get('repo_count', 0)} projects and "
                    f"{profile_summary.get('total_stars', 0)} total GitHub stars is looking "
                    f"for internships/jobs. Suggest 5 specific companies and roles they should "
                    f"apply to. Return as a JSON array with objects having keys: "
                    f"company, role, location, url (use company careers page), source."
                ),
            }],
        )
        from gitpulse.utils import parse_json_response
        result = parse_json_response(message.content[0].text)
        if isinstance(result, list):
            for r in result:
                r["source"] = "ai-recommendation"
            return result
        return []
    except Exception as e:
        print(f"  ⚠ Claude job search failed: {e}")
        return []


def scan_jobs(profile=None, keywords=None):
    print("\n🔍 Scanning for jobs/internships...")
    results = []

    repo_jobs = scan_github_repos(keywords)
    print(f"  ✓ Found {len(repo_jobs)} listings from curated repos")
    results.extend(repo_jobs)

    if profile and profile.get("summary"):
        ai_jobs = search_with_claude(profile["summary"])
        print(f"  ✓ Got {len(ai_jobs)} AI-powered recommendations")
        results.extend(ai_jobs)

    return results
