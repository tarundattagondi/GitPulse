"""Phase 8 test: interview prep generator."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import validate
from backend.routes.interview_prep import post_interview_prep

SALESFORCE_JD = """
Salesforce — Software Engineer Intern, Summer 2026
Location: San Francisco, CA (Hybrid)

Required:
- B.S. or M.S. in Computer Science
- Strong proficiency in Java or Python
- SQL and relational databases (PostgreSQL, MySQL)
- RESTful API design
- Git and CI/CD pipelines
- Data structures and algorithms

Preferred:
- Cloud platforms (AWS, GCP, Azure)
- Docker, Kubernetes
- React or modern frontend frameworks
- Distributed systems concepts
- Open-source contributions
- Agile/Scrum methodologies

Soft skills:
- Strong communication
- Team collaboration
- Problem-solving
- Adaptability

Tech Stack: Java, Python, JavaScript, Spring Boot, React, PostgreSQL, Redis, Kafka, AWS, Docker, Kubernetes
"""


async def test_full_pipeline():
    """Run full interview prep pipeline."""
    username = "tarundattagondi"

    print(f"\n  → Generating interview prep for {username}...")
    result = await post_interview_prep(username, SALESFORCE_JD)

    assert result["username"] == username
    assert "prep" in result
    prep = result["prep"]

    print(f"\n  Role: {result['role_category']} | Match: {result['overall_match_pct']}%")

    # Technical questions
    tech = prep.get("technical_questions", [])
    assert len(tech) >= 3, f"Expected 3+ technical questions, got {len(tech)}"
    print(f"\n  Technical Questions ({len(tech)}):")
    for i, q in enumerate(tech, 1):
        print(f"    {i}. {q['question']}")
        print(f"       Skill: {q.get('skill_tested', '?')}")
        print(f"       Why: {q.get('why_asked', '?')[:80]}")

    # Behavioral questions
    behav = prep.get("behavioral_questions", [])
    assert len(behav) >= 2, f"Expected 2+ behavioral questions, got {len(behav)}"
    print(f"\n  Behavioral Questions ({len(behav)}):")
    for i, q in enumerate(behav, 1):
        print(f"    {i}. {q['question']}")
        print(f"       Skill: {q.get('skill_tested', '?')}")

    # Coding challenges
    coding = prep.get("coding_challenges", [])
    assert len(coding) >= 2, f"Expected 2+ coding challenges, got {len(coding)}"
    print(f"\n  Coding Challenges ({len(coding)}):")
    for i, c in enumerate(coding, 1):
        topics = ", ".join(c.get("topics", []))
        print(f"    {i}. [{c.get('difficulty', '?')}] {c['problem'][:80]}")
        print(f"       Topics: {topics}")
        print(f"       Hint: {c.get('hint', '?')[:80]}")

    # Gap coverage
    gaps = prep.get("gap_coverage_questions", [])
    assert len(gaps) >= 1, f"Expected 1+ gap questions, got {len(gaps)}"
    print(f"\n  Gap Coverage Questions ({len(gaps)}):")
    for i, g in enumerate(gaps, 1):
        print(f"    {i}. {g['question']}")
        print(f"       Gap: {g.get('gap', '?')}")
        print(f"       Prepare: {g.get('how_to_prepare', '?')[:80]}")

    print(f"\n  ✓ All sections generated successfully")
    return result


if __name__ == "__main__":
    validate()

    print(f"{'=' * 60}")
    print(f"  Phase 8 — Interview Prep Generator Test")
    print(f"{'=' * 60}")

    asyncio.run(test_full_pipeline())

    print(f"\n{'=' * 60}")
    print(f"  Phase 8 — All tests passed ✓")
    print(f"{'=' * 60}\n")
