import math
import json
import anthropic

from backend.config import CLAUDE_MODEL


# ── Weight constants ──────────────────────────────────────────────
W_SKILLS_MATCH = 40
W_PROJECT_RELEVANCE = 25
W_README_QUALITY = 15
W_ACTIVITY_LEVEL = 10
W_PROFILE_COMPLETENESS = 10


def _claude_semantic_score(prompt: str, max_score: int) -> tuple[int, str]:
    """Ask Claude to score something semantically. Returns (score, reasoning)."""
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=512,
        system=(
            f"You are a technical recruiter scoring a GitHub profile. "
            f"Return ONLY valid JSON: {{\"score\": <int 0-{max_score}>, \"reasoning\": \"<one sentence>\"}}"
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text
    # Parse JSON, handling code fences
    import re
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        result = json.loads(match.group(0))
        return min(int(result["score"]), max_score), result.get("reasoning", "")
    return 0, "Could not parse response"


def score_skills_match(profile: dict, repos: list[dict], job_description: str | None = None) -> dict:
    """Claude semantic comparison of skills vs market demand. Max 40 points."""
    all_languages = {}
    for repo in repos:
        for lang, bytes_count in repo.get("languages", {}).items():
            all_languages[lang] = all_languages.get(lang, 0) + bytes_count

    top_langs = sorted(all_languages.items(), key=lambda x: x[1], reverse=True)[:10]
    lang_list = ", ".join(f"{l[0]} ({l[1]:,} bytes)" for l in top_langs)
    topics = set()
    for repo in repos:
        topics.update(repo.get("topics", []))
    topic_list = ", ".join(sorted(topics)) if topics else "none"

    target = f"the following job description:\n{job_description}" if job_description else "current software engineering market demand (2024-2025)"

    prompt = (
        f"Score this developer's skills match against {target}.\n\n"
        f"Languages: {lang_list}\n"
        f"Topics/technologies: {topic_list}\n"
        f"Number of repos: {len(repos)}\n\n"
        f"Score 0-{W_SKILLS_MATCH} based on how well these skills align with demand. "
        f"Consider language relevance, breadth vs depth, and modern tech stack adoption."
    )
    score, reasoning = _claude_semantic_score(prompt, W_SKILLS_MATCH)
    return {"score": score, "max": W_SKILLS_MATCH, "reasoning": reasoning}


def score_project_relevance(repos: list[dict], job_description: str | None = None) -> dict:
    """Claude semantic analysis of project quality and relevance. Max 25 points."""
    repo_summaries = []
    for r in repos[:10]:
        desc = r.get("description") or "no description"
        lang = r.get("language") or "unknown"
        topics = ", ".join(r.get("topics", [])) or "none"
        repo_summaries.append(f"- {r['name']} ({lang}): {desc} [topics: {topics}, stars: {r.get('stars', 0)}]")

    repos_text = "\n".join(repo_summaries) if repo_summaries else "No repositories found"
    target = f"this job:\n{job_description}" if job_description else "general software engineering impact"

    prompt = (
        f"Score the relevance and quality of these projects for {target}.\n\n"
        f"Repositories:\n{repos_text}\n\n"
        f"Score 0-{W_PROJECT_RELEVANCE} based on project originality, real-world applicability, "
        f"technical complexity, and variety. Favor projects that solve real problems over toy examples."
    )
    score, reasoning = _claude_semantic_score(prompt, W_PROJECT_RELEVANCE)
    return {"score": score, "max": W_PROJECT_RELEVANCE, "reasoning": reasoning}


def score_readme_quality(readmes: dict[str, str | None]) -> dict:
    """Checklist-based README scoring. Max 15 points.

    Checks across all provided READMEs:
    - Has any README at all (3 pts)
    - Length > 200 chars (2 pts)
    - Has headings (2 pts)
    - Has code blocks (2 pts)
    - Has install/setup instructions (2 pts)
    - Has badges/images (2 pts)
    - Has usage examples (2 pts)
    """
    if not readmes or all(v is None for v in readmes.values()):
        return {"score": 0, "max": W_README_QUALITY, "reasoning": "No READMEs found", "checks": {}}

    valid_readmes = {k: v for k, v in readmes.items() if v}
    if not valid_readmes:
        return {"score": 0, "max": W_README_QUALITY, "reasoning": "All READMEs are empty", "checks": {}}

    # Combine all READMEs for checking
    combined = "\n".join(valid_readmes.values())
    best_readme = max(valid_readmes.values(), key=len)

    checks = {
        "has_readme": (len(valid_readmes) > 0, 3),
        "sufficient_length": (len(best_readme) > 200, 2),
        "has_headings": (any(line.strip().startswith("#") for line in combined.split("\n")), 2),
        "has_code_blocks": ("```" in combined, 2),
        "has_install_instructions": (
            any(kw in combined.lower() for kw in ["install", "setup", "getting started", "pip ", "npm ", "cargo "]),
            2,
        ),
        "has_badges_or_images": (
            any(marker in combined for marker in ["![", "[![", "<img", "badge"]),
            2,
        ),
        "has_usage_examples": (
            any(kw in combined.lower() for kw in ["usage", "example", "how to use", "quick start"]),
            2,
        ),
    }

    score = sum(pts for passed, pts in checks.values() if passed)
    passed_checks = [k for k, (v, _) in checks.items() if v]
    failed_checks = [k for k, (v, _) in checks.items() if not v]

    reasoning = f"Passed: {', '.join(passed_checks)}." if passed_checks else ""
    if failed_checks:
        reasoning += f" Missing: {', '.join(failed_checks)}."

    return {
        "score": min(score, W_README_QUALITY),
        "max": W_README_QUALITY,
        "reasoning": reasoning.strip(),
        "checks": {k: v for k, (v, _) in checks.items()},
    }


def score_activity_level(commit_count_90d: int) -> dict:
    """Log-scaled activity score based on 90-day commit count. Max 10 points.

    Scale: log2(commits+1) mapped to 0-10.
    ~1 commit = 1pt, ~7 commits = 3pt, ~31 commits = 5pt,
    ~127 commits = 7pt, ~511 commits = 9pt, ~1023+ commits = 10pt.
    """
    if commit_count_90d <= 0:
        return {"score": 0, "max": W_ACTIVITY_LEVEL, "reasoning": "No commits in the last 90 days", "commits_90d": 0}

    raw = math.log2(commit_count_90d + 1)
    score = min(int(round(raw)), W_ACTIVITY_LEVEL)

    return {
        "score": score,
        "max": W_ACTIVITY_LEVEL,
        "reasoning": f"{commit_count_90d} commits in 90 days → log₂({commit_count_90d}+1) ≈ {raw:.1f}",
        "commits_90d": commit_count_90d,
    }


def score_profile_completeness(profile: dict) -> dict:
    """Check profile fields. Max 10 points (2 each)."""
    checks = {
        "has_name": bool(profile.get("name")),
        "has_bio": bool(profile.get("bio")),
        "has_location": bool(profile.get("location")),
        "has_company_or_blog": bool(profile.get("company") or profile.get("blog")),
        "has_avatar": bool(profile.get("avatar_url")),
    }
    score = sum(2 for v in checks.values() if v)
    filled = [k for k, v in checks.items() if v]
    missing = [k for k, v in checks.items() if not v]

    reasoning = ""
    if filled:
        reasoning = f"Filled: {', '.join(filled)}."
    if missing:
        reasoning += f" Missing: {', '.join(missing)}."

    return {
        "score": min(score, W_PROFILE_COMPLETENESS),
        "max": W_PROFILE_COMPLETENESS,
        "reasoning": reasoning.strip(),
        "checks": checks,
    }


def score_profile_full(
    profile: dict,
    repos: list[dict],
    readmes: dict[str, str | None],
    commit_count_90d: int,
    job_description: str | None = None,
) -> dict:
    """Run all five scorers and return a complete breakdown."""
    skills = score_skills_match(profile, repos, job_description)
    projects = score_project_relevance(repos, job_description)
    readme = score_readme_quality(readmes)
    activity = score_activity_level(commit_count_90d)
    completeness = score_profile_completeness(profile)

    total = skills["score"] + projects["score"] + readme["score"] + activity["score"] + completeness["score"]

    return {
        "total_score": total,
        "max_score": 100,
        "breakdown": {
            "skills_match": skills,
            "project_relevance": projects,
            "readme_quality": readme,
            "activity_level": activity,
            "profile_completeness": completeness,
        },
    }
