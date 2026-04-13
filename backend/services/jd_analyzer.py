import json
import re
import anthropic

from backend.config import CLAUDE_MODEL

ROLE_CATEGORIES = [
    "data_engineering", "devops", "cloud", "frontend", "backend",
    "fullstack", "ml", "security", "mobile", "other",
]

JD_SCHEMA = """{
  "required_skills": ["<string>", ...],
  "preferred_skills": ["<string>", ...],
  "tools": ["<string>", ...],
  "domain_keywords": ["<string>", ...],
  "experience_level": "<string: intern/junior/mid/senior/staff>",
  "company_industry": "<string>",
  "soft_skills": ["<string>", ...],
  "role_category": "<one of: data_engineering, devops, cloud, frontend, backend, fullstack, ml, security, mobile, other>"
}"""

SYSTEM_PROMPT = (
    "You are a job description parser. Extract structured data from the job description. "
    "Return ONLY valid JSON matching this exact schema, no markdown fences, no commentary:\n"
    f"{JD_SCHEMA}\n\n"
    "Rules:\n"
    "- required_skills: explicitly stated as required or must-have\n"
    "- preferred_skills: nice-to-have, bonus, or preferred\n"
    "- tools: specific software, frameworks, platforms, services mentioned\n"
    "- domain_keywords: industry/domain terms (e.g. 'CRM', 'cloud computing', 'e-commerce')\n"
    "- experience_level: infer from title, years, or context\n"
    "- company_industry: the company's primary industry\n"
    "- soft_skills: communication, teamwork, leadership, etc.\n"
    f"- role_category: exactly one of {ROLE_CATEGORIES}"
)

RETRY_SYSTEM_PROMPT = (
    "You previously failed to return valid JSON. This time you MUST return ONLY raw JSON. "
    "No markdown. No code fences. No explanation. No text before or after the JSON object. "
    "Start your response with { and end with }.\n\n"
    f"Schema:\n{JD_SCHEMA}"
)


def _parse_json(text: str) -> dict:
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
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("No valid JSON found", text, 0)


def _validate_jd_result(result: dict) -> dict:
    required_keys = [
        "required_skills", "preferred_skills", "tools", "domain_keywords",
        "experience_level", "company_industry", "soft_skills", "role_category",
    ]
    for key in required_keys:
        if key not in result:
            result[key] = [] if key not in ("experience_level", "company_industry", "role_category") else ""
    # Normalize role_category
    if result.get("role_category") not in ROLE_CATEGORIES:
        result["role_category"] = "other"
    # Ensure lists are lists
    for key in ["required_skills", "preferred_skills", "tools", "domain_keywords", "soft_skills"]:
        if not isinstance(result.get(key), list):
            result[key] = []
    return result


def analyze_jd(jd_text: str) -> dict | None:
    """Analyze a job description and return structured data. Retries twice on parse failure.
    Returns None if jd_text is too short to be meaningful."""
    if not jd_text or len(jd_text.strip()) < 50:
        return None
    client = anthropic.Anthropic()
    last_error = None

    for attempt in range(3):
        system = SYSTEM_PROMPT if attempt == 0 else RETRY_SYSTEM_PROMPT
        user_content = f"Job Description:\n\n{jd_text}"
        if attempt > 0:
            user_content += f"\n\nPrevious attempt failed with: {last_error}. Return ONLY valid JSON."

        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            raw = message.content[0].text
            result = _parse_json(raw)
            return _validate_jd_result(result)
        except (json.JSONDecodeError, Exception) as e:
            last_error = str(e)
            if attempt == 2:
                raise ValueError(f"Failed to parse JD after 3 attempts. Last error: {last_error}")

    raise ValueError("Failed to parse JD")
