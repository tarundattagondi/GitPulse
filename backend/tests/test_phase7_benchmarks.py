"""Phase 7 test: company benchmarking."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.config import validate
from backend.services.company_benchmarks import (
    benchmark_user_against_company,
    list_companies,
    _percentile,
    _language_overlap,
)
from backend.services.github_service import fetch_profile, fetch_all_repos, fetch_readme
from backend.routes.benchmark import get_benchmark


def test_percentile():
    """Test percentile calculation."""
    print("\n  [Unit] Testing percentile function...")
    assert _percentile(10, 10) == 50, "Equal should be ~50"
    assert _percentile(20, 10) > 70, "Double should be >70"
    assert _percentile(5, 10) < 35, "Half should be <35"
    assert _percentile(0, 10) < 20, "Zero should be low"
    assert 1 <= _percentile(0, 0) <= 99, "Zero avg should not crash"
    print("  ✓ Percentile calculations correct")


def test_language_overlap():
    """Test language overlap."""
    print("\n  [Unit] Testing language overlap...")
    result = _language_overlap(
        ["Python", "Java", "Go"],
        ["Python", "Java", "TypeScript", "C++"],
    )
    assert "python" in result["matched"]
    assert "java" in result["matched"]
    assert "typescript" in result["missing"]
    assert "go" in result["extra"]
    assert result["overlap_pct"] == 50
    print(f"  ✓ Matched: {result['matched']}, Missing: {result['missing']}, Extra: {result['extra']}")


def test_list_companies():
    """Verify seed data loads."""
    print("\n  [Unit] Testing company list...")
    companies = list_companies()
    assert len(companies) == 10
    assert "Salesforce" in companies
    assert "Google" in companies
    assert "QTS Data Centers" in companies
    print(f"  ✓ {len(companies)} companies loaded: {', '.join(companies)}")


def test_benchmark_not_found():
    """Unknown company should raise ValueError."""
    print("\n  [Unit] Testing unknown company...")
    try:
        benchmark_user_against_company({"repos": [], "profile": {}, "readmes": {}}, "FakeCompany")
        assert False, "Should have raised"
    except ValueError as e:
        assert "not found" in str(e).lower()
        print(f"  ✓ Correctly rejected: {e}")


async def test_live_benchmarks():
    """Benchmark tarundattagondi against 3 companies."""
    username = "tarundattagondi"

    print(f"\n  [Live] Fetching {username}'s GitHub data...")
    profile, repos = await asyncio.gather(
        fetch_profile(username),
        fetch_all_repos(username),
    )
    readmes = {}
    for r in repos[:5]:
        readmes[r["name"]] = await fetch_readme(username, r["name"])

    github_data = {"profile": profile, "repos": repos, "readmes": readmes}

    for company in ["Salesforce", "Google", "QTS Data Centers"]:
        result = benchmark_user_against_company(github_data, company)

        print(f"\n  ── {result['company']} ──")
        print(f"  Overall: {result['overall_percentile']}th percentile — {result['overall_verdict']}")

        dims = result["dimensions"]
        for dim_name, dim_data in dims.items():
            p = dim_data["percentile"]
            bar_w = 15
            filled = int(p / 100 * bar_w)
            bar = "█" * filled + "░" * (bar_w - filled)

            if dim_name in ("repo_count", "star_count", "readme_quality"):
                print(f"    {dim_name:<22} [{bar}] p{p:>2}  "
                      f"(you: {dim_data['user']}, avg: {dim_data['cohort_avg']}) "
                      f"{dim_data.get('verdict', '')}")
            elif dim_name == "language_match":
                print(f"    {dim_name:<22} [{bar}] p{p:>2}  "
                      f"overlap: {dim_data['overlap_pct']}%  "
                      f"matched: {', '.join(dim_data['matched'])}  "
                      f"missing: {', '.join(dim_data['missing'])}")
            elif dim_name == "project_relevance":
                print(f"    {dim_name:<22} [{bar}] p{p:>2}  "
                      f"coverage: {dim_data['coverage_pct']}%  "
                      f"covered: {', '.join(dim_data['covered'][:3])}  "
                      f"gaps: {', '.join(dim_data['not_covered'][:3])}")


async def test_route():
    """Test route handler."""
    print(f"\n\n  [Route] Testing GET /api/benchmark/tarundattagondi/Salesforce...")
    result = await get_benchmark("tarundattagondi", "Salesforce")
    assert result["company"] == "Salesforce"
    assert 1 <= result["overall_percentile"] <= 99
    assert len(result["dimensions"]) == 5
    print(f"  ✓ {result['overall_percentile']}th percentile — {result['overall_verdict']}")


if __name__ == "__main__":
    validate()

    print(f"{'=' * 60}")
    print(f"  Phase 7 — Company Benchmarking Tests")
    print(f"{'=' * 60}")

    test_percentile()
    test_language_overlap()
    test_list_companies()
    test_benchmark_not_found()

    asyncio.run(test_live_benchmarks())
    asyncio.run(test_route())

    print(f"\n{'=' * 60}")
    print(f"  Phase 7 — All tests passed ✓")
    print(f"{'=' * 60}\n")
