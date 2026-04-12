"""Phase 6 test: resume parsing, tri-source matching."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import validate
from backend.services.resume_parser import parse_resume
from backend.services.tri_match import tri_source_match
from backend.services.github_service import fetch_profile, fetch_all_repos, fetch_readme
from backend.services.jd_analyzer import analyze_jd
from backend.routes.tri_match import post_tri_match

SAMPLE_RESUME = """
TARUN DATTA GONDI
Software Engineer | San Francisco, CA
Email: tarun@example.com | GitHub: github.com/tarundattagondi

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley — Expected May 2027
GPA: 3.7/4.0
Relevant Coursework: Data Structures, Algorithms, Operating Systems, Databases, Machine Learning

SKILLS
Languages: Java, Python, JavaScript, TypeScript, SQL, HTML/CSS
Frameworks: React, Node.js, Spring Boot, Flask, Express.js
Tools: Git, Docker, AWS (EC2, S3, Lambda), PostgreSQL, MongoDB, Redis
Concepts: RESTful APIs, Microservices, CI/CD, Agile/Scrum, TDD

EXPERIENCE
Software Engineering Intern | TechStartup Inc. | Jun 2025 – Aug 2025
- Built RESTful APIs using Spring Boot serving 10K+ daily requests
- Implemented Redis caching layer reducing API response times by 40%
- Wrote 85+ unit tests achieving 92% code coverage with JUnit and Mockito
- Participated in daily standups and bi-weekly sprint planning

Teaching Assistant — CS 61B Data Structures | UC Berkeley | Jan 2025 – May 2025
- Conducted weekly discussion sections for 30+ students
- Graded assignments and held office hours covering BSTs, graphs, sorting algorithms

PROJECTS
CensusMinds — AI Policy Simulator
- Built a full-stack application using Python, JavaScript, and HTML/CSS
- Simulated community reactions to policy proposals using 100 AI personas
- Deployed on Heroku with CI/CD pipeline

CloudGuard — AWS Security Scanner
- Developed automated AWS security scanning tool in Python
- Mapped findings to NIST 800-53 compliance framework
- Generated risk dashboards with severity scoring

CERTIFICATIONS
AWS Cloud Practitioner (2025)
"""

SALESFORCE_JD = """
Salesforce — Software Engineer Intern, Summer 2026
Location: San Francisco, CA (Hybrid)

Required:
- B.S. or M.S. in Computer Science
- Strong proficiency in Java or Python
- SQL and relational databases (PostgreSQL, MySQL)
- RESTful API design
- Git and CI/CD pipelines

Preferred:
- Cloud platforms (AWS, GCP, Azure)
- Docker, Kubernetes
- React or modern frontend frameworks
- Distributed systems concepts
- Open-source contributions

Tech Stack: Java, Python, JavaScript, Spring Boot, React, PostgreSQL, Redis, Kafka, AWS, Docker, Kubernetes
"""


def test_resume_parser():
    """Test resume parsing from text."""
    print("\n  [Unit] Testing resume parser...")
    resume_bytes = SAMPLE_RESUME.encode("utf-8")
    result = parse_resume(resume_bytes, "resume.txt")

    assert len(result["skills"]) > 0, "Expected skills"
    assert len(result["projects"]) > 0, "Expected projects"
    assert len(result["experience"]) > 0, "Expected experience"
    assert len(result["education"]) > 0, "Expected education"

    print(f"  ✓ Skills: {len(result['skills'])} found")
    print(f"    {', '.join(result['skills'][:10])}")
    print(f"  ✓ Projects: {len(result['projects'])} found")
    for p in result["projects"]:
        print(f"    → {p['name']} ({', '.join(p.get('tech', [])[:4])})")
    print(f"  ✓ Experience: {len(result['experience'])} entries")
    for e in result["experience"]:
        print(f"    → {e['role']} at {e['company']}")
    print(f"  ✓ Education: {len(result['education'])} entries")
    print(f"  ✓ Certifications: {result.get('certifications', [])}")

    return result


async def test_tri_source_match():
    """Test full tri-source match pipeline."""
    username = "tarundattagondi"
    print(f"\n  [Live] Running tri-source match for {username}...")

    # Fetch GitHub data
    profile, repos = await asyncio.gather(
        fetch_profile(username),
        fetch_all_repos(username),
    )
    readmes = {}
    for r in repos[:5]:
        readmes[r["name"]] = await fetch_readme(username, r["name"])
    github_data = {"profile": profile, "repos": repos, "readmes": readmes}

    # Parse resume
    resume_data = parse_resume(SAMPLE_RESUME.encode("utf-8"), "resume.txt")

    # Analyze JD
    jd_analysis = analyze_jd(SALESFORCE_JD)
    print(f"  ✓ JD analyzed: {jd_analysis['role_category']}")

    # Tri-source match
    print(f"  → Running tri-source match...")
    result = tri_source_match(github_data, resume_data, jd_analysis)

    # Display results
    section = result.get("resume_says_github_doesnt_prove", [])
    print(f"\n  Resume claims GitHub doesn't prove ({len(section)}):")
    for item in section[:3]:
        print(f"    ⚠ Claim: {item.get('claim', '?')}")
        print(f"      Missing: {item.get('evidence_missing', '?')}")

    section = result.get("github_shows_resume_doesnt_mention", [])
    print(f"\n  GitHub shows but resume doesn't mention ({len(section)}):")
    for item in section[:3]:
        print(f"    📌 GitHub: {item.get('github_evidence', '?')}")
        print(f"      Resume gap: {item.get('resume_gap', '?')}")

    section = result.get("both_missing_for_jd", [])
    print(f"\n  Both missing for JD ({len(section)}):")
    for item in section[:3]:
        print(f"    ❌ {item.get('requirement', '?')} [{item.get('importance', '?')}]")

    section = result.get("resume_rewrite_suggestions", [])
    print(f"\n  Resume rewrite suggestions ({len(section)}):")
    for item in section[:3]:
        print(f"    ✏️  {item.get('section', '?')}: {item.get('reason', '?')}")

    section = result.get("github_project_suggestions", [])
    print(f"\n  GitHub project suggestions ({len(section)}):")
    for item in section[:3]:
        print(f"    🔨 {item.get('project_name', '?')}: {item.get('description', '?')}")

    return result


async def test_route():
    """Test the route handler end-to-end."""
    print(f"\n  [Route] Testing POST /api/tri-match...")
    result = await post_tri_match(
        github_username="tarundattagondi",
        jd_text=SALESFORCE_JD,
        resume_bytes=SAMPLE_RESUME.encode("utf-8"),
        resume_filename="resume.txt",
    )

    assert result["github_username"] == "tarundattagondi"
    assert result["resume_skills_found"] > 0
    assert result["resume_projects_found"] > 0
    assert "match_result" in result

    print(f"  ✓ Route returned successfully")
    print(f"    Skills found: {result['resume_skills_found']}")
    print(f"    Projects found: {result['resume_projects_found']}")
    print(f"    JD category: {result['jd_role_category']}")
    print(f"    Match sections: {len(result['match_result'])} keys")


if __name__ == "__main__":
    validate()

    print(f"{'=' * 60}")
    print(f"  Phase 6 — Tri-Source Matching Tests")
    print(f"{'=' * 60}")

    # Unit test
    test_resume_parser()

    # Live tri-source match
    asyncio.run(test_tri_source_match())

    # Route test
    asyncio.run(test_route())

    print(f"\n{'=' * 60}")
    print(f"  Phase 6 — All tests passed ✓")
    print(f"{'=' * 60}\n")
