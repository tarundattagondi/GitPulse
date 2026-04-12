"""Seed company_benchmarks table in Supabase with the 10 benchmark companies.

Idempotent — uses upsert so running twice won't duplicate rows.
Usage: python -m backend.seed_benchmarks
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.storage import upsert_company_benchmark

SEED_FILE = Path(__file__).resolve().parent / "data" / "company_benchmarks.json"

DEFAULT_BENCHMARKS = {
    "Salesforce": {"avg_repo_count": 12, "avg_star_count": 15, "top_languages": ["Java", "Python", "JavaScript", "TypeScript", "Apex"], "typical_projects": ["CRM integrations", "REST APIs", "Lightning Web Components", "Salesforce Platform tools", "enterprise microservices"], "avg_readme_quality": 11, "avg_years_experience": 1.5},
    "Amazon": {"avg_repo_count": 15, "avg_star_count": 25, "top_languages": ["Java", "Python", "TypeScript", "Go", "C++"], "typical_projects": ["distributed systems", "AWS Lambda functions", "data pipelines", "CLI tools", "infrastructure automation"], "avg_readme_quality": 10, "avg_years_experience": 1.0},
    "Google": {"avg_repo_count": 18, "avg_star_count": 40, "top_languages": ["Python", "C++", "Java", "Go", "TypeScript"], "typical_projects": ["open-source libraries", "algorithm visualizers", "ML models", "Chrome extensions", "competitive programming solutions"], "avg_readme_quality": 13, "avg_years_experience": 1.5},
    "Microsoft": {"avg_repo_count": 14, "avg_star_count": 20, "top_languages": ["C#", "TypeScript", "Python", "Java", "C++"], "typical_projects": ["VS Code extensions", "Azure integrations", ".NET APIs", "developer tools", "full-stack web apps"], "avg_readme_quality": 12, "avg_years_experience": 1.0},
    "Meta": {"avg_repo_count": 16, "avg_star_count": 35, "top_languages": ["Python", "JavaScript", "TypeScript", "C++", "Hack"], "typical_projects": ["React apps", "mobile apps", "graph algorithms", "real-time systems", "ML research implementations"], "avg_readme_quality": 12, "avg_years_experience": 1.5},
    "Stripe": {"avg_repo_count": 14, "avg_star_count": 30, "top_languages": ["Ruby", "Python", "TypeScript", "Go", "Java"], "typical_projects": ["payment integrations", "API wrappers", "developer tools", "fintech prototypes", "full-stack web apps"], "avg_readme_quality": 13, "avg_years_experience": 2.0},
    "Databricks": {"avg_repo_count": 13, "avg_star_count": 20, "top_languages": ["Python", "Scala", "Java", "SQL", "TypeScript"], "typical_projects": ["Spark jobs", "data pipelines", "ML notebooks", "ETL frameworks", "database connectors"], "avg_readme_quality": 11, "avg_years_experience": 1.5},
    "Snowflake": {"avg_repo_count": 11, "avg_star_count": 15, "top_languages": ["Python", "SQL", "Java", "Go", "TypeScript"], "typical_projects": ["data warehousing tools", "SQL analyzers", "ETL pipelines", "cloud-native apps", "CLI utilities"], "avg_readme_quality": 11, "avg_years_experience": 1.5},
    "QTS Data Centers": {"avg_repo_count": 8, "avg_star_count": 5, "top_languages": ["Python", "Bash", "Go", "JavaScript", "Terraform"], "typical_projects": ["infrastructure monitoring", "automation scripts", "network tools", "dashboard apps", "DevOps pipelines"], "avg_readme_quality": 9, "avg_years_experience": 1.0},
    "Berkeley Research Group": {"avg_repo_count": 7, "avg_star_count": 5, "top_languages": ["Python", "R", "SQL", "JavaScript", "Stata"], "typical_projects": ["data analysis notebooks", "statistical models", "web scrapers", "visualization dashboards", "research tools"], "avg_readme_quality": 8, "avg_years_experience": 1.0},
}


def main():
    # Try loading from seed file first
    benchmarks = DEFAULT_BENCHMARKS
    if SEED_FILE.exists():
        try:
            data = json.loads(SEED_FILE.read_text())
            if "companies" in data:
                benchmarks = data["companies"]
                print(f"Loaded {len(benchmarks)} companies from {SEED_FILE}")
        except Exception as e:
            print(f"Could not load seed file, using defaults: {e}")

    for name, data in benchmarks.items():
        upsert_company_benchmark(name, data)
        print(f"  ✓ {name}")

    print(f"\nSeeded {len(benchmarks)} companies to Supabase.")


if __name__ == "__main__":
    main()
