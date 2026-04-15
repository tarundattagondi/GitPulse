"""Semantic profile-to-JD matcher with README-aware skill attribution."""

import json
import re

import anthropic

from backend.config import CLAUDE_MODEL


def _extract_profile_skills(github_data: dict) -> dict:
    """Extract all skills/technologies from GitHub profile data including README content."""
    all_languages = {}
    for repo in github_data.get("repos", []):
        for lang, byte_count in repo.get("languages", {}).items():
            all_languages[lang] = all_languages.get(lang, 0) + byte_count
    sorted_langs = sorted(all_languages.items(), key=lambda x: x[1], reverse=True)

    all_topics = set()
    for repo in github_data.get("repos", []):
        all_topics.update(repo.get("topics", []))

    # Build rich per-repo summaries including README excerpts
    repo_summaries = []
    for repo in github_data.get("repos", [])[:10]:
        desc = repo.get("description") or ""
        langs = ", ".join(repo.get("languages", {}).keys()) or repo.get("language") or "unknown"
        topics = ", ".join(repo.get("topics", [])) or "none"
        readme = repo.get("readme_excerpt") or ""
        # Also check readmes dict if available
        if not readme:
            readmes = github_data.get("readmes", {})
            readme = (readmes.get(repo["name"]) or "")[:2000]

        summary = (
            f"Repo: {repo['name']}\n"
            f"  Description: {desc}\n"
            f"  Languages: {langs}\n"
            f"  Topics: {topics}\n"
            f"  Stars: {repo.get('stars', 0)}"
        )
        if readme:
            summary += f"\n  README excerpt: {readme[:1500]}"
        repo_summaries.append(summary)

    return {
        "languages": [l[0] for l in sorted_langs],
        "language_bytes": dict(sorted_langs),
        "topics": sorted(all_topics),
        "repo_summaries": repo_summaries,
    }


def _find_demonstrated_skills(github_data: dict, required_skills: list[str]) -> set:
    """Check which required skills appear in any repo's README or description."""
    demonstrated = set()
    for repo in github_data.get("repos", []):
        searchable = " ".join([
            repo.get("description") or "",
            repo.get("readme_excerpt") or "",
            " ".join(repo.get("topics", [])),
            " ".join(repo.get("languages", {}).keys()),
        ]).lower()
        # Also check readmes dict
        readmes = github_data.get("readmes", {})
        readme_content = (readmes.get(repo["name"]) or "").lower()
        searchable += " " + readme_content

        for skill in required_skills:
            if skill.lower() in searchable:
                demonstrated.add(skill)
    return demonstrated


def match_profile_to_jd(github_data: dict, jd_analysis: dict) -> dict:
    """Match a GitHub profile against an analyzed JD using Claude for semantic matching.
    Includes README content for accurate framework/library detection."""
    profile_skills = _extract_profile_skills(github_data)
    client = anthropic.Anthropic()

    repos_text = "\n\n".join(profile_skills["repo_summaries"][:8])

    prompt = (
        "You are a technical recruiter matching a candidate's GitHub profile against a job description.\n\n"
        "Candidate's GitHub profile:\n"
        f"Languages: {', '.join(profile_skills['languages'][:10])}\n"
        f"Topics/technologies: {', '.join(profile_skills['topics'][:15])}\n\n"
        f"Projects (with README excerpts):\n{repos_text}\n\n"
        f"Job requirements:\n"
        f"- Required skills: {', '.join(jd_analysis.get('required_skills', []))}\n"
        f"- Preferred skills: {', '.join(jd_analysis.get('preferred_skills', []))}\n"
        f"- Tools: {', '.join(jd_analysis.get('tools', []))}\n"
        f"- Domain: {', '.join(jd_analysis.get('domain_keywords', []))}\n"
        f"- Role category: {jd_analysis.get('role_category', 'other')}\n"
        f"- Experience level: {jd_analysis.get('experience_level', 'unknown')}\n\n"
        "Return ONLY valid JSON with this schema:\n"
        "{\n"
        '  "overall_match_pct": <int 0-100>,\n'
        '  "category_scores": {\n'
        '    "required_skills": {"score": <int 0-100>, "found": ["<skill>", ...], "missing": ["<skill>", ...]},\n'
        '    "preferred_skills": {"score": <int 0-100>, "found": ["<skill>", ...], "missing": ["<skill>", ...]},\n'
        '    "tools": {"score": <int 0-100>, "found": ["<tool>", ...], "missing": ["<tool>", ...]},\n'
        '    "domain_knowledge": {"score": <int 0-100>, "found": ["<keyword>", ...], "missing": ["<keyword>", ...]}\n'
        "  },\n"
        '  "most_relevant_repos": ["<repo_name>", ...],\n'
        '  "gap_items": ["<specific gap>", ...],\n'
        '  "strengths_for_role": ["<strength>", ...]\n'
        "}"
    )

    system_prompt = (
        "You are a precise technical recruiter. Return ONLY valid JSON, no fences, no commentary.\n\n"
        "Skill attribution rules:\n"
        "- A skill is 'found/demonstrated' if it appears in repo languages, topics, descriptions, "
        "OR README content (tech stack sections, badges, import statements, framework mentions).\n"
        "- If a README says 'Built with FastAPI' or shows FastAPI in a tech stack list, count FastAPI as demonstrated.\n"
        "- Be generous: evidence in any single repo counts for the whole profile.\n"
        "- Only mark a skill as 'missing' if there is zero evidence across all repos, descriptions, and READMEs.\n"
        "- gap_items should only list skills with genuinely no evidence anywhere."
    )

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=3000,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        result = json.loads(match.group(0))
    else:
        result = json.loads(text)

    # Post-process: remove demonstrated skills from gap_items
    all_required = jd_analysis.get("required_skills", []) + jd_analysis.get("preferred_skills", []) + jd_analysis.get("tools", [])
    demonstrated = _find_demonstrated_skills(github_data, all_required)
    if result.get("gap_items"):
        result["gap_items"] = [
            g for g in result["gap_items"]
            if not any(d.lower() in g.lower() for d in demonstrated)
        ]

    return result
