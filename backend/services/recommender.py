import json
import re
import anthropic

from backend.config import CLAUDE_MODEL


def _parse_json_response(text: str) -> dict:
    """Parse JSON from Claude response, handling fences and truncation."""
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Strip fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # First {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        raw = match.group(0)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Try to repair truncated JSON by closing open structures
            repaired = _repair_json(raw)
            try:
                return json.loads(repaired)
            except json.JSONDecodeError:
                pass
    raise ValueError(f"Could not parse JSON from response (length={len(text)})")


def _repair_json(text: str) -> str:
    """Attempt to close truncated JSON."""
    # Count open/close brackets
    open_braces = text.count("{") - text.count("}")
    open_brackets = text.count("[") - text.count("]")
    # Check for unterminated strings
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
    text += "]" * max(0, open_brackets)
    text += "}" * max(0, open_braces)
    return text


def _build_context(github_data: dict, jd_analysis: dict, match_result: dict) -> str:
    repos = github_data.get("repos", [])
    repo_summaries = []
    for r in repos[:10]:
        langs = ", ".join(r.get("languages", {}).keys()) or r.get("language") or "unknown"
        repo_summaries.append(
            f"- {r['name']} ({langs}): {r.get('description') or 'no description'} "
            f"[stars: {r.get('stars', 0)}]"
        )

    readmes = github_data.get("readmes", {})
    repos_with_readme = [name for name, content in readmes.items() if content and len(content) > 50]
    repos_without_readme = [r["name"] for r in repos if r["name"] not in repos_with_readme]

    return (
        f"TARGET ROLE: {jd_analysis.get('role_category', 'other')} — {jd_analysis.get('experience_level', 'unknown')} level\n"
        f"Company industry: {jd_analysis.get('company_industry', 'tech')}\n"
        f"Required skills: {', '.join(jd_analysis.get('required_skills', []))}\n"
        f"Preferred skills: {', '.join(jd_analysis.get('preferred_skills', []))}\n"
        f"Tools: {', '.join(jd_analysis.get('tools', []))}\n\n"
        f"CANDIDATE REPOS:\n" + "\n".join(repo_summaries) + "\n\n"
        f"MATCH RESULT:\n"
        f"- Overall match: {match_result.get('overall_match_pct', 0)}%\n"
        f"- Gaps: {', '.join(match_result.get('gap_items', []))}\n"
        f"- Missing required: {', '.join(match_result.get('category_scores', {}).get('required_skills', {}).get('missing', []))}\n"
        f"- Missing tools: {', '.join(match_result.get('category_scores', {}).get('tools', {}).get('missing', []))}\n"
        f"- Repos needing READMEs: {', '.join(repos_without_readme[:5])}\n"
    )


def _generate_plan_and_actions(client: anthropic.Anthropic, context: str) -> dict:
    """Generate missing projects, 30-day plan, priority actions, interview prep."""
    prompt = (
        "You are a senior career coach for software engineers.\n\n"
        + context +
        "\nReturn ONLY valid JSON:\n"
        "{\n"
        '  "missing_projects": [\n'
        '    {"name": "<name>", "description": "<what to build and why>", "skills_demonstrated": ["<skill>", ...], "estimated_hours": <int>}\n'
        "  ],\n"
        '  "thirty_day_plan": {\n'
        '    "week_1": {"focus": "<theme>", "tasks": ["<specific task>", ...]},\n'
        '    "week_2": {"focus": "<theme>", "tasks": ["<specific task>", ...]},\n'
        '    "week_3": {"focus": "<theme>", "tasks": ["<specific task>", ...]},\n'
        '    "week_4": {"focus": "<theme>", "tasks": ["<specific task>", ...]}\n'
        "  },\n"
        '  "priority_actions": ["<action>", ...],\n'
        '  "interview_prep_topics": [\n'
        '    {"topic": "<topic>", "why": "<reason>", "resources": ["<resource>", ...]}\n'
        "  ]\n"
        "}\n\n"
        "- missing_projects: 2-3 projects filling the SPECIFIC gaps\n"
        "- thirty_day_plan: concrete tasks, not vague advice\n"
        "- priority_actions: top 5 things to do THIS WEEK\n"
        "- interview_prep_topics: 3-5 topics for this role's interviews"
    )

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system="Return ONLY valid JSON. No fences. No commentary. Start with { end with }.",
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse_json_response(message.content[0].text)


def _generate_readme_rewrites(client: anthropic.Anthropic, context: str, github_data: dict) -> list[dict]:
    """Generate full publication-ready README rewrites as separate calls to avoid truncation."""
    readmes = github_data.get("readmes", {})
    repos = github_data.get("repos", [])

    # Find repos that most need README improvement
    candidates = []
    for r in repos:
        readme = readmes.get(r["name"])
        if readme is None or len(readme) < 100:
            candidates.append(r)
    # Also include repos with short READMEs
    if len(candidates) < 3:
        for r in repos:
            readme = readmes.get(r["name"])
            if readme and len(readme) < 500 and r not in candidates:
                candidates.append(r)
    candidates = candidates[:4]

    if not candidates:
        return []

    rewrites = []

    # Generate ONE full README for the weakest repo (first candidate)
    first = candidates[0]
    langs = ", ".join(first.get("languages", {}).keys()) or first.get("language") or "unknown"
    desc = first.get("description") or "no description provided"
    existing_readme = readmes.get(first["name"]) or "none"

    prompt = (
        f"Write a FULL, publication-ready README.md for this GitHub repository.\n\n"
        f"Repo: {first['name']}\n"
        f"Description: {desc}\n"
        f"Languages: {langs}\n"
        f"Stars: {first.get('stars', 0)}\n"
        f"Topics: {', '.join(first.get('topics', []))}\n"
        f"Existing README: {existing_readme[:200] if existing_readme != 'none' else 'none'}\n\n"
        f"The README must include ALL of these sections:\n"
        f"1. Title with badges placeholder\n"
        f"2. One-paragraph project description\n"
        f"3. Features list\n"
        f"4. Tech Stack\n"
        f"5. Installation (step-by-step with code blocks)\n"
        f"6. Usage (with code examples)\n"
        f"7. Contributing\n"
        f"8. License\n\n"
        f"Return ONLY valid JSON: {{\"repo\": \"{first['name']}\", \"readme_content\": \"<full markdown>\"}}\n"
        f"IMPORTANT: Escape all newlines as \\n, all quotes as \\\" inside the JSON string."
    )

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=3000,
            system="Return ONLY valid JSON. Escape newlines as \\n in strings. No markdown fences around the JSON.",
            messages=[{"role": "user", "content": prompt}],
        )
        result = _parse_json_response(message.content[0].text)
        if result.get("readme_content"):
            rewrites.append(result)
    except Exception as e:
        print(f"  ⚠ Full README generation failed for {first['name']}: {e}")

    # For remaining candidates, generate short improvement notes only (no full README)
    for repo in candidates[1:]:
        langs = ", ".join(repo.get("languages", {}).keys()) or repo.get("language") or "unknown"
        desc = repo.get("description") or "no description"
        existing = readmes.get(repo["name"]) or "none"
        rewrites.append({
            "repo": repo["name"],
            "readme_content": None,
            "note": f"Needs improvement: {repo['name']} ({langs}) — "
                    f"{'missing README entirely' if existing == 'none' else f'current README is only {len(existing)} chars'}. "
                    f"Add project description, install instructions, and usage examples.",
        })

    return rewrites


def generate_recommendations(
    github_data: dict,
    jd_analysis: dict,
    match_result: dict,
) -> dict:
    """Generate actionable recommendations split across focused Claude calls."""
    client = anthropic.Anthropic()
    context = _build_context(github_data, jd_analysis, match_result)

    # Call 1: plan, projects, actions, interview prep
    plan_result = _generate_plan_and_actions(client, context)

    # Call 2: README rewrites (one per repo to avoid truncation)
    readme_rewrites = _generate_readme_rewrites(client, context, github_data)

    result = {
        "missing_projects": plan_result.get("missing_projects", []),
        "readme_rewrites": readme_rewrites,
        "thirty_day_plan": plan_result.get("thirty_day_plan", {}),
        "priority_actions": plan_result.get("priority_actions", []),
        "interview_prep_topics": plan_result.get("interview_prep_topics", []),
    }
    return result
