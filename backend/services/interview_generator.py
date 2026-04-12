"""Interview prep generator: tailored questions based on profile gaps and JD."""

import json
import re

import anthropic

from backend.config import CLAUDE_MODEL


SYSTEM_PROMPT = """You are a senior technical interviewer preparing a candidate for a specific role.
Generate interview preparation material tailored to the candidate's profile and gaps.
Return ONLY valid JSON matching this schema:

{
  "technical_questions": [
    {
      "question": "<interview question>",
      "why_asked": "<why this company/role would ask this>",
      "suggested_answer_framework": "<STAR or structured approach to answer>",
      "skill_tested": "<specific skill>"
    }
  ],
  "behavioral_questions": [
    {
      "question": "<behavioral question>",
      "why_asked": "<why relevant to this role>",
      "suggested_answer_framework": "<how to structure the answer>",
      "skill_tested": "<soft skill or competency>"
    }
  ],
  "coding_challenges": [
    {
      "problem": "<problem statement>",
      "difficulty": "<easy/medium/hard>",
      "topics": ["<topic>"],
      "hint": "<approach hint>"
    }
  ],
  "gap_coverage_questions": [
    {
      "question": "<question targeting a specific gap>",
      "gap": "<the gap this addresses>",
      "how_to_prepare": "<concrete steps to prepare>",
      "backup_answer": "<how to answer if you don't have direct experience>"
    }
  ]
}

Rules:
- technical_questions: 5-7 questions covering the role's core technical requirements
- behavioral_questions: 3-5 questions relevant to the company culture and role
- coding_challenges: 3-5 problems at varying difficulty, matching the JD's tech stack
- gap_coverage_questions: 2-4 questions targeting the candidate's SPECIFIC gaps
- Tailor everything to the actual gaps and strengths found in the match result
- Be specific — reference actual technologies, not generic advice"""


def _parse_response(text: str) -> dict:
    """Parse JSON from Claude response with repair fallback."""
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
    # Extract {...}
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        raw = match.group(0)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Repair truncated JSON
            repaired = _repair_json(raw)
            return json.loads(repaired)
    raise ValueError(f"Could not parse JSON from response (length={len(text)})")


def _repair_json(text: str) -> str:
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
    text += "]" * max(0, text.count("[") - text.count("]"))
    text += "}" * max(0, text.count("{") - text.count("}"))
    return text


def generate_interview_prep(
    github_data: dict,
    jd_analysis: dict,
    match_result: dict,
) -> dict:
    """Generate tailored interview prep material.

    Args:
        github_data: profile, repos, readmes from GitHub
        jd_analysis: parsed JD (role_category, required_skills, etc.)
        match_result: output from matcher (category_scores, gap_items, etc.)

    Returns:
        technical_questions, behavioral_questions, coding_challenges, gap_coverage_questions
    """
    client = anthropic.Anthropic()

    # Build context
    repos = github_data.get("repos", [])
    repo_lines = []
    for r in repos[:8]:
        lang = r.get("language") or "unknown"
        desc = r.get("description") or "no description"
        repo_lines.append(f"- {r['name']} ({lang}): {desc}")

    all_langs = {}
    for r in repos:
        for lang, b in r.get("languages", {}).items():
            all_langs[lang] = all_langs.get(lang, 0) + b
    top_langs = [l for l, _ in sorted(all_langs.items(), key=lambda x: x[1], reverse=True)[:8]]

    # Extract match details
    cat_scores = match_result.get("category_scores", {})
    found_skills = []
    missing_skills = []
    for cat_data in cat_scores.values():
        found_skills.extend(cat_data.get("found", []))
        missing_skills.extend(cat_data.get("missing", []))

    gaps = match_result.get("gap_items", [])
    strengths = match_result.get("strengths_for_role", [])
    overall_match = match_result.get("overall_match_pct", 0)

    prompt = (
        f"Prepare interview material for this candidate and role:\n\n"
        f"=== ROLE ===\n"
        f"Category: {jd_analysis.get('role_category', 'other')}\n"
        f"Level: {jd_analysis.get('experience_level', 'unknown')}\n"
        f"Industry: {jd_analysis.get('company_industry', 'tech')}\n"
        f"Required skills: {', '.join(jd_analysis.get('required_skills', []))}\n"
        f"Preferred skills: {', '.join(jd_analysis.get('preferred_skills', []))}\n"
        f"Tools: {', '.join(jd_analysis.get('tools', []))}\n"
        f"Soft skills: {', '.join(jd_analysis.get('soft_skills', []))}\n\n"
        f"=== CANDIDATE ===\n"
        f"Languages: {', '.join(top_langs)}\n"
        f"Projects:\n" + "\n".join(repo_lines) + "\n\n"
        f"=== MATCH RESULT ({overall_match}% overall) ===\n"
        f"Skills found: {', '.join(found_skills[:10])}\n"
        f"Skills missing: {', '.join(missing_skills[:10])}\n"
        f"Gaps: {'; '.join(gaps[:5])}\n"
        f"Strengths: {', '.join(strengths[:5])}\n\n"
        f"Generate interview prep that:\n"
        f"1. Tests the candidate on their ACTUAL projects (reference repo names)\n"
        f"2. Probes the SPECIFIC gaps identified\n"
        f"3. Includes coding problems in the JD's tech stack\n"
        f"4. Prepares behavioral answers using their real project experience"
    )

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    result = _parse_response(message.content[0].text)

    # Ensure all keys exist
    for key in ["technical_questions", "behavioral_questions", "coding_challenges", "gap_coverage_questions"]:
        if key not in result:
            result[key] = []

    return result
