"""Tri-source matching: cross-reference GitHub, resume, and JD."""

import json
import re

import anthropic

from backend.config import CLAUDE_MODEL


def _build_github_summary(github_data: dict) -> str:
    """Summarize GitHub data for the prompt."""
    repos = github_data.get("repos", [])
    all_langs = {}
    for r in repos:
        for lang, b in r.get("languages", {}).items():
            all_langs[lang] = all_langs.get(lang, 0) + b
    top_langs = sorted(all_langs.items(), key=lambda x: x[1], reverse=True)[:10]

    topics = set()
    for r in repos:
        topics.update(r.get("topics", []))

    repo_lines = []
    for r in repos[:10]:
        desc = r.get("description") or "no description"
        lang = r.get("language") or "unknown"
        repo_lines.append(f"  - {r['name']} ({lang}): {desc} [stars: {r.get('stars', 0)}]")

    return (
        f"Languages: {', '.join(l[0] for l in top_langs)}\n"
        f"Topics: {', '.join(sorted(topics))}\n"
        f"Repos ({len(repos)}):\n" + "\n".join(repo_lines)
    )


def _build_resume_summary(resume_data: dict) -> str:
    """Summarize resume data for the prompt."""
    skills = ", ".join(resume_data.get("skills", [])[:20])
    projects = []
    for p in resume_data.get("projects", []):
        tech = ", ".join(p.get("tech", []))
        projects.append(f"  - {p.get('name', '?')} ({tech}): {'; '.join(p.get('bullets', [])[:2])}")
    experience = []
    for e in resume_data.get("experience", []):
        experience.append(f"  - {e.get('role', '?')} at {e.get('company', '?')} ({e.get('duration', '?')})")

    return (
        f"Skills: {skills}\n"
        f"Projects:\n" + "\n".join(projects[:5]) + "\n"
        f"Experience:\n" + "\n".join(experience[:5])
    )


def _build_jd_summary(jd_analysis: dict) -> str:
    """Summarize JD analysis for the prompt."""
    return (
        f"Role: {jd_analysis.get('role_category', 'other')} ({jd_analysis.get('experience_level', 'unknown')})\n"
        f"Required: {', '.join(jd_analysis.get('required_skills', []))}\n"
        f"Preferred: {', '.join(jd_analysis.get('preferred_skills', []))}\n"
        f"Tools: {', '.join(jd_analysis.get('tools', []))}\n"
        f"Domain: {', '.join(jd_analysis.get('domain_keywords', []))}"
    )


def tri_source_match(
    github_data: dict,
    resume_data: dict,
    jd_analysis: dict,
) -> dict:
    """Cross-reference GitHub profile, resume, and JD analysis.

    Returns:
      - resume_says_github_doesnt_prove: skills/experience claimed on resume but not evidenced on GitHub
      - github_shows_resume_doesnt_mention: projects/skills visible on GitHub but missing from resume
      - both_missing_for_jd: JD requirements neither resume nor GitHub covers
      - resume_rewrite_suggestions: specific resume improvements
      - github_project_suggestions: projects to build to fill gaps
    """
    client = anthropic.Anthropic()

    github_summary = _build_github_summary(github_data)
    resume_summary = _build_resume_summary(resume_data)
    jd_summary = _build_jd_summary(jd_analysis)

    prompt = (
        "You are a career strategist performing a tri-source analysis across a candidate's "
        "GitHub profile, resume, and target job description.\n\n"
        f"=== GITHUB PROFILE ===\n{github_summary}\n\n"
        f"=== RESUME ===\n{resume_summary}\n\n"
        f"=== JOB DESCRIPTION ===\n{jd_summary}\n\n"
        "Perform a thorough cross-reference and return ONLY valid JSON:\n"
        "{\n"
        '  "resume_says_github_doesnt_prove": [\n'
        '    {"claim": "<what resume says>", "evidence_missing": "<what GitHub lacks>", "fix": "<how to add proof>"}\n'
        "  ],\n"
        '  "github_shows_resume_doesnt_mention": [\n'
        '    {"github_evidence": "<what GitHub shows>", "resume_gap": "<what resume is missing>", "suggestion": "<how to add to resume>"}\n'
        "  ],\n"
        '  "both_missing_for_jd": [\n'
        '    {"requirement": "<JD requirement>", "importance": "<critical/important/nice-to-have>", "action": "<what to do>"}\n'
        "  ],\n"
        '  "resume_rewrite_suggestions": [\n'
        '    {"section": "<resume section>", "current": "<what it says now>", "suggested": "<improved version>", "reason": "<why>"}\n'
        "  ],\n"
        '  "github_project_suggestions": [\n'
        '    {"project_name": "<name>", "description": "<what to build>", "skills_demonstrated": ["<skill>", ...], "estimated_hours": <int>}\n'
        "  ]\n"
        "}\n\n"
        "Be specific. Reference actual repo names, actual resume bullets, and actual JD requirements."
    )

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system="Return ONLY valid JSON. No fences. No commentary. Start with { end with }.",
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text
    match_obj = re.search(r"\{.*\}", text, re.DOTALL)
    raw = match_obj.group(0) if match_obj else text

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = json.loads(_repair_json(raw))

    # Ensure all keys
    for key in [
        "resume_says_github_doesnt_prove",
        "github_shows_resume_doesnt_mention",
        "both_missing_for_jd",
        "resume_rewrite_suggestions",
        "github_project_suggestions",
    ]:
        if key not in result:
            result[key] = []

    return result


def _repair_json(text: str) -> str:
    """Close truncated JSON structures."""
    in_string = False
    escaped = False
    for ch in text:
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == '"':
            in_string = not in_string
    if in_string:
        text += '"'
    open_brackets = text.count("[") - text.count("]")
    open_braces = text.count("{") - text.count("}")
    text += "]" * max(0, open_brackets)
    text += "}" * max(0, open_braces)
    return text
