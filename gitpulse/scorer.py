import json
import anthropic
from gitpulse import config
from gitpulse.utils import parse_json_response, truncate

SYSTEM_PROMPT = """You are a senior technical recruiter evaluating GitHub profiles.
Analyze the provided GitHub profile data and score it. Return ONLY valid JSON with this exact structure:
{
  "overall_score": <int 0-100>,
  "breakdown": {
    "code_quality": <int 0-100>,
    "project_diversity": <int 0-100>,
    "activity_level": <int 0-100>,
    "documentation": <int 0-100>,
    "community_engagement": <int 0-100>
  },
  "strengths": ["<strength1>", "<strength2>", ...],
  "weaknesses": ["<weakness1>", "<weakness2>", ...],
  "recommendations": ["<rec1>", "<rec2>", ...],
  "job_fit_score": <int 0-100 or null>,
  "job_fit_analysis": "<string or null>"
}

Be specific and actionable in your recommendations. Base scores on real signals:
- Code quality: language diversity, project size, use of best practices
- Project diversity: variety of project types, domains, technologies
- Activity level: recent commits, events, contribution frequency
- Documentation: READMEs, descriptions, wikis
- Community engagement: stars received, forks, followers, contributions to others' projects"""


def score_profile(profile, job_description=None):
    print("\n🤖 Scoring profile with Claude AI...")
    client = anthropic.Anthropic()

    profile_text = json.dumps({
        "user": profile["user"],
        "summary": profile["summary"],
        "top_repos": profile["top_repos"][:5],
        "languages": dict(list(profile["languages"].items())[:10]),
        "contributions": profile["contributions"],
    }, indent=2)

    user_message = f"GitHub Profile Data:\n{profile_text}"
    if job_description:
        user_message += f"\n\nJob Description to evaluate fit against:\n{truncate(job_description, 1000)}"

    try:
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        result = parse_json_response(message.content[0].text)
        print("  ✓ Scoring complete")
        return result
    except anthropic.APIError as e:
        print(f"  ✗ Claude API error: {e}")
        raise
    except Exception as e:
        print(f"  ✗ Scoring failed: {e}")
        raise


def score_against_jobs(profile, jobs):
    print(f"\n📋 Scoring profile against {len(jobs)} jobs...")
    scored = []
    for i, job in enumerate(jobs[:10]):  # cap at 10
        desc = f"{job.get('role', '')} at {job.get('company', '')}"
        if job.get("location"):
            desc += f" ({job['location']})"
        try:
            score = score_profile(profile, desc)
            job_with_score = {**job, "fit_score": score.get("job_fit_score", 0), "analysis": score.get("job_fit_analysis", "")}
            scored.append(job_with_score)
            print(f"  [{i+1}/{min(len(jobs), 10)}] {job['company']}: {job_with_score['fit_score']}/100")
        except Exception:
            continue
    return sorted(scored, key=lambda x: x.get("fit_score", 0), reverse=True)
