import json
import anthropic

from backend.config import CLAUDE_MODEL


def _extract_profile_skills(github_data: dict) -> dict:
    """Extract all skills/technologies from GitHub profile data."""
    # Languages from repos
    all_languages = {}
    for repo in github_data.get("repos", []):
        for lang, byte_count in repo.get("languages", {}).items():
            all_languages[lang] = all_languages.get(lang, 0) + byte_count
    sorted_langs = sorted(all_languages.items(), key=lambda x: x[1], reverse=True)

    # Topics from repos
    all_topics = set()
    for repo in github_data.get("repos", []):
        all_topics.update(repo.get("topics", []))

    # Repo names + descriptions as signal
    repo_descriptions = []
    for repo in github_data.get("repos", []):
        desc = repo.get("description") or ""
        repo_descriptions.append(f"{repo['name']}: {desc}")

    return {
        "languages": [l[0] for l in sorted_langs],
        "language_bytes": dict(sorted_langs),
        "topics": sorted(all_topics),
        "repo_descriptions": repo_descriptions,
    }


def match_profile_to_jd(github_data: dict, jd_analysis: dict) -> dict:
    """Match a GitHub profile against an analyzed JD using Claude for semantic matching."""
    profile_skills = _extract_profile_skills(github_data)
    client = anthropic.Anthropic()

    prompt = (
        "You are a technical recruiter matching a candidate's GitHub profile against a job description.\n\n"
        "Candidate's GitHub profile:\n"
        f"- Languages: {', '.join(profile_skills['languages'][:10])}\n"
        f"- Topics/technologies: {', '.join(profile_skills['topics'][:15])}\n"
        f"- Projects:\n"
        + "\n".join(f"  • {d}" for d in profile_skills["repo_descriptions"][:10])
        + "\n\nJob requirements:\n"
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

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1500,
        system="You are a precise technical recruiter. Return ONLY valid JSON, no fences, no commentary.",
        messages=[{"role": "user", "content": prompt}],
    )

    import re
    text = message.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        result = json.loads(match.group(0))
    else:
        result = json.loads(text)

    return result
