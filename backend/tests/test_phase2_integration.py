"""Phase 2 Integration Test: full pipeline on tarundattagondi vs Salesforce SWE Intern JD."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import validate
from backend.services.github_service import (
    fetch_profile,
    fetch_all_repos,
    fetch_readme,
    fetch_pinned_repos,
    fetch_recent_commits,
)
from backend.services.jd_analyzer import analyze_jd
from backend.services.matcher import match_profile_to_jd
from backend.services.recommender import generate_recommendations
from backend.services.scorer import score_profile_full
from backend.storage import write_json

SALESFORCE_SWE_INTERN_JD = """
Salesforce — Software Engineer Intern, Summer 2026

Location: San Francisco, CA (Hybrid)
Team: Platform Engineering

About the Role:
Join Salesforce's Platform Engineering team as a Summer 2026 Software Engineer Intern.
You'll work on building and scaling the infrastructure that powers the world's #1 CRM platform,
serving over 150,000 customers globally. This is a 12-week paid internship with potential
for full-time conversion.

What You'll Do:
- Design, develop, and test features for Salesforce's core platform services
- Build RESTful APIs and microservices that handle millions of requests per day
- Write clean, well-tested code with comprehensive unit and integration tests
- Participate in code reviews, architecture discussions, and agile ceremonies
- Collaborate with cross-functional teams including product, design, and QA
- Contribute to internal tools and developer experience improvements

Required Qualifications:
- Currently pursuing a B.S. or M.S. in Computer Science, Software Engineering, or related field
- Expected graduation between December 2026 and June 2027
- Strong proficiency in Java or Python
- Solid understanding of data structures and algorithms
- Experience with SQL and relational databases (PostgreSQL, MySQL)
- Familiarity with version control (Git) and CI/CD pipelines
- Understanding of RESTful API design principles
- Strong problem-solving and analytical skills

Preferred Qualifications:
- Experience with cloud platforms (AWS, GCP, or Azure)
- Knowledge of containerization (Docker, Kubernetes)
- Familiarity with distributed systems concepts
- Experience with JavaScript/TypeScript and modern frontend frameworks (React, Vue)
- Contributions to open-source projects
- Experience with Agile/Scrum development methodologies
- Previous internship experience in software engineering

Tech Stack:
- Languages: Java, Python, JavaScript/TypeScript
- Frameworks: Spring Boot, React, Lightning Web Components
- Databases: PostgreSQL, Redis, Apache Kafka
- Infrastructure: AWS, Docker, Kubernetes, Jenkins, GitHub Actions
- Tools: Git, JIRA, Confluence, Splunk, Datadog

Compensation:
- Competitive hourly rate ($55-65/hr depending on location)
- Housing stipend for non-local candidates
- Mentorship program and intern cohort events

Salesforce is an Equal Opportunity Employer. We value diversity and are committed to
creating an inclusive environment for all employees.
"""


async def main():
    validate()
    username = "tarundattagondi"

    print(f"\n{'=' * 70}")
    print(f"  Phase 2 Integration Test")
    print(f"  Candidate: {username}")
    print(f"  Target: Salesforce SWE Intern, Summer 2026")
    print(f"{'=' * 70}")

    # ── Step 1: Fetch GitHub data ─────────────────────────────────────
    print("\n[1/6] Fetching GitHub profile...")
    profile = await fetch_profile(username)
    repos = await fetch_all_repos(username)
    print(f"  ✓ Profile loaded — {len(repos)} repos")

    readmes = {}
    for r in repos[:5]:
        readmes[r["name"]] = await fetch_readme(username, r["name"])
    print(f"  ✓ Fetched {sum(1 for v in readmes.values() if v)} READMEs")

    pinned = await fetch_pinned_repos(username)
    commit_count = await fetch_recent_commits(username, repos)
    print(f"  ✓ {commit_count} commits (90d), {len(pinned)} pinned repos")

    github_data = {
        "profile": profile,
        "repos": repos,
        "readmes": readmes,
        "pinned": pinned,
        "commit_count_90d": commit_count,
    }

    # ── Step 2: Analyze JD ────────────────────────────────────────────
    print("\n[2/6] Analyzing Salesforce JD with Claude...")
    jd_analysis = analyze_jd(SALESFORCE_SWE_INTERN_JD)
    print(f"  ✓ Role: {jd_analysis['role_category']} ({jd_analysis['experience_level']})")
    print(f"  ✓ Required skills: {', '.join(jd_analysis['required_skills'][:8])}")
    print(f"  ✓ Tools: {', '.join(jd_analysis['tools'][:8])}")

    # ── Step 3: Score profile ─────────────────────────────────────────
    print("\n[3/6] Scoring profile (5-category)...")
    score = score_profile_full(profile, repos, readmes, commit_count, SALESFORCE_SWE_INTERN_JD)
    print(f"  ✓ Total score: {score['total_score']}/100")
    for cat, data in score["breakdown"].items():
        print(f"    {cat}: {data['score']}/{data['max']}")

    # ── Step 4: Match profile to JD ───────────────────────────────────
    print("\n[4/6] Matching profile against JD...")
    match_result = match_profile_to_jd(github_data, jd_analysis)
    print(f"  ✓ Overall match: {match_result.get('overall_match_pct', '?')}%")

    cat_scores = match_result.get("category_scores", {})
    for cat, data in cat_scores.items():
        found = data.get("found", [])
        missing = data.get("missing", [])
        print(f"    {cat}: {data.get('score', '?')}% — found {len(found)}, missing {len(missing)}")

    if match_result.get("gap_items"):
        print(f"  Gaps: {'; '.join(match_result['gap_items'][:5])}")

    # ── Step 5: Generate recommendations ──────────────────────────────
    print("\n[5/6] Generating recommendations...")
    recs = generate_recommendations(github_data, jd_analysis, match_result)

    if recs.get("missing_projects"):
        print(f"\n  Missing Projects ({len(recs['missing_projects'])}):")
        for p in recs["missing_projects"]:
            print(f"    → {p['name']}: {p['description']} (~{p.get('estimated_hours', '?')}h)")

    if recs.get("readme_rewrites"):
        print(f"\n  README Rewrites ({len(recs['readme_rewrites'])}):")
        for rw in recs["readme_rewrites"]:
            content = rw.get("readme_content", "")
            print(f"    → {rw['repo']}: {len(content)} chars")

    plan = recs.get("thirty_day_plan", {})
    if plan:
        print(f"\n  30-Day Plan:")
        for week, data in plan.items():
            focus = data.get("focus", "?") if isinstance(data, dict) else data
            print(f"    {week}: {focus}")

    if recs.get("priority_actions"):
        print(f"\n  Priority Actions:")
        for a in recs["priority_actions"][:5]:
            print(f"    ★ {a}")

    if recs.get("interview_prep_topics"):
        print(f"\n  Interview Prep:")
        for t in recs["interview_prep_topics"]:
            topic = t.get("topic", t) if isinstance(t, dict) else t
            print(f"    📖 {topic}")

    # ── Step 6: Save output ───────────────────────────────────────────
    print(f"\n[6/6] Saving results...")
    output = {
        "username": username,
        "target_job": "Salesforce SWE Intern Summer 2026",
        "jd_analysis": jd_analysis,
        "score": score,
        "match_result": match_result,
        "recommendations": recs,
    }
    out_path = Path(__file__).resolve().parent.parent.parent / "data" / "phase2_integration_test.json"
    write_json(out_path, output)
    print(f"  ✓ Saved → data/phase2_integration_test.json")

    print(f"\n{'=' * 70}")
    print(f"  Phase 2 Integration Test — COMPLETE")
    print(f"  Score: {score['total_score']}/100 | Match: {match_result.get('overall_match_pct', '?')}%")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())
