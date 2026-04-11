"""Phase 3 Integration Test: SimplifyJobs scanner with parsing, filtering, and live fetch."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.services.job_board_scanner import (
    fetch_simplify_jobs,
    filter_jobs,
    _parse_html_table,
    JobListing,
)


# ── Unit test: HTML table parsing ──────────────────────────────────
def test_parse_html_table():
    sample = """
<table>
<thead><tr><th>Company</th><th>Role</th><th>Location</th><th>Application</th><th>Age</th></tr></thead>
<tbody>
<tr>
<td><strong><a href="https://simplify.jobs/c/Acme">Acme Corp</a></strong></td>
<td>Software Engineer Intern</td>
<td>NYC</td>
<td><div align="center"><a href="https://example.com/apply?utm_source=Simplify&ref=Simplify"><img src="x" alt="Apply"></a></div></td>
<td>2d</td>
</tr>
<tr>
<td>↳</td>
<td>Backend Engineer Intern</td>
<td>SF</td>
<td><div align="center"><a href="https://example.com/apply2"><img src="x" alt="Apply"></a></div></td>
<td>3d</td>
</tr>
<tr>
<td>🔒 <strong><a href="https://simplify.jobs/c/ClosedCo">ClosedCo</a></strong></td>
<td>ML Intern</td>
<td>Remote</td>
<td>🔒</td>
<td>10d</td>
</tr>
<tr>
<td>🛂 <strong><a href="https://simplify.jobs/c/NoVisa">NoVisa Inc</a></strong></td>
<td>Data Intern</td>
<td>Austin, TX</td>
<td><div align="center"><a href="https://example.com/apply3"><img src="x" alt="Apply"></a></div></td>
<td>1d</td>
</tr>
<tr>
<td><strong><a href="https://simplify.jobs/c/Multi">MultiLoc</a></strong></td>
<td>DevOps Intern</td>
<td><details><summary><strong>3 locations</strong></summary>Boston, MA<br>Seattle, WA<br>Austin, TX</details></td>
<td><div align="center"><a href="https://example.com/apply4"><img src="x" alt="Apply"></a></div></td>
<td>0d</td>
</tr>
</tbody>
</table>
"""
    jobs = _parse_html_table(sample)

    assert len(jobs) == 5, f"Expected 5 jobs, got {len(jobs)}"

    # First job
    assert jobs[0].company == "Acme Corp"
    assert jobs[0].role == "Software Engineer Intern"
    assert jobs[0].location == "NYC"
    assert not jobs[0].is_closed
    assert jobs[0].sponsors_visa

    # Sub-listing inherits company
    assert jobs[1].company == "Acme Corp"
    assert jobs[1].role == "Backend Engineer Intern"
    assert jobs[1].location == "SF"

    # Closed job
    assert jobs[2].company == "ClosedCo"
    assert jobs[2].is_closed

    # No visa sponsorship
    assert jobs[3].company == "NoVisa Inc"
    assert not jobs[3].sponsors_visa

    # Multi-location
    assert "Boston, MA" in jobs[4].location
    assert "Seattle, WA" in jobs[4].location

    print("  ✓ HTML table parsing: all assertions passed")


def test_filter_jobs():
    jobs = [
        JobListing("Acme", "Software Engineer Intern", "NYC", "", "2026-04-01", False, True),
        JobListing("Beta", "ML Intern", "SF", "", "2026-04-01", False, True),
        JobListing("Gamma", "Software Intern", "Austin, TX", "", "2026-04-01", True, True),
        JobListing("Delta", "Backend Engineer Intern", "NYC", "", "2026-04-01", False, False),
    ]

    # Exclude closed
    open_jobs = filter_jobs(jobs, exclude_closed=True)
    assert len(open_jobs) == 3
    assert all(not j.is_closed for j in open_jobs)

    # Role filter
    swe = filter_jobs(jobs, role_keywords=["software"], exclude_closed=False)
    assert len(swe) == 2

    # Location filter
    nyc = filter_jobs(jobs, location_keywords=["NYC"], exclude_closed=False)
    assert len(nyc) == 2

    # Combined
    nyc_swe = filter_jobs(jobs, role_keywords=["software"], location_keywords=["NYC"])
    assert len(nyc_swe) == 1
    assert nyc_swe[0].company == "Acme"

    print("  ✓ Filter jobs: all assertions passed")


async def test_live_fetch():
    print("\n  → Fetching SimplifyJobs listings (live)...")
    jobs = await fetch_simplify_jobs(force_refresh=True)
    print(f"  ✓ Fetched {len(jobs)} total listings")

    # Basic sanity
    assert len(jobs) > 100, f"Expected 100+ jobs, got {len(jobs)}"

    open_jobs = filter_jobs(jobs, exclude_closed=True)
    print(f"  ✓ {len(open_jobs)} open listings")

    swe_jobs = filter_jobs(jobs, role_keywords=["software", "engineer", "developer"], exclude_closed=True)
    print(f"  ✓ {len(swe_jobs)} SWE-related open listings")

    # Show sample
    print(f"\n  Sample listings (first 10 SWE):")
    for j in swe_jobs[:10]:
        visa = "✓" if j.sponsors_visa else "🛂"
        print(f"    {visa} {j.company:<30} {j.role:<40} {j.location[:30]:<30} {j.posted_date}")

    # Stats
    companies = set(j.company for j in open_jobs)
    print(f"\n  Stats:")
    print(f"    Unique companies: {len(companies)}")
    print(f"    Visa sponsors: {sum(1 for j in open_jobs if j.sponsors_visa)}")
    print(f"    No visa: {sum(1 for j in open_jobs if not j.sponsors_visa)}")

    return jobs


if __name__ == "__main__":
    print(f"{'=' * 60}")
    print(f"  Phase 3 — SimplifyJobs Scanner Tests")
    print(f"{'=' * 60}\n")

    # Unit tests
    test_parse_html_table()
    test_filter_jobs()

    # Live test
    asyncio.run(test_live_fetch())

    print(f"\n{'=' * 60}")
    print(f"  Phase 3 — All tests passed ✓")
    print(f"{'=' * 60}\n")
