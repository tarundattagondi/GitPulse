"""Company-specific cohort benchmarking: compare a user's GitHub profile against
typical intern/new-grad profiles at target companies."""

import math

from backend.storage import get_company_benchmark, list_company_names


def _percentile(user_val: float, cohort_avg: float) -> int:
    if cohort_avg <= 0:
        return 50
    ratio = user_val / cohort_avg
    percentile = 100 / (1 + math.exp(-1.5 * (ratio - 1)))
    return max(1, min(99, int(round(percentile))))


def _language_overlap(user_langs: list[str], company_langs: list[str]) -> dict:
    user_set = {l.lower() for l in user_langs}
    company_set = {l.lower() for l in company_langs}
    matched = user_set & company_set
    missing = company_set - user_set
    extra = user_set - company_set
    overlap_pct = int(100 * len(matched) / len(company_set)) if company_set else 0
    return {
        "matched": sorted(matched),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "overlap_pct": overlap_pct,
    }


def _project_relevance(user_repos: list[dict], typical_projects: list[str]) -> dict:
    user_text = " ".join(
        f"{r.get('name', '')} {r.get('description', '')} {' '.join(r.get('topics', []))}"
        for r in user_repos
    ).lower()

    covered = []
    not_covered = []
    for proj_type in typical_projects:
        keywords = proj_type.lower().split()
        if any(kw in user_text for kw in keywords):
            covered.append(proj_type)
        else:
            not_covered.append(proj_type)

    coverage_pct = int(100 * len(covered) / len(typical_projects)) if typical_projects else 0
    return {
        "covered": covered,
        "not_covered": not_covered,
        "coverage_pct": coverage_pct,
    }


def list_companies() -> list[str]:
    return list_company_names()


def benchmark_user_against_company(github_data: dict, company_name: str) -> dict:
    company = get_company_benchmark(company_name)

    if not company:
        available = ", ".join(list_company_names())
        raise ValueError(f"Company '{company_name}' not found. Available: {available}")

    company_key = company["company_name"]
    repos = github_data.get("repos", [])

    user_repo_count = len(repos)
    user_star_count = sum(r.get("stars", 0) for r in repos)

    all_langs = {}
    for r in repos:
        for lang, b in r.get("languages", {}).items():
            all_langs[lang] = all_langs.get(lang, 0) + b
    user_langs = [l for l, _ in sorted(all_langs.items(), key=lambda x: x[1], reverse=True)]

    readmes = github_data.get("readmes", {})
    readme_scores = []
    for content in readmes.values():
        if not content:
            readme_scores.append(0)
            continue
        score = 3
        if len(content) > 200: score += 2
        if any(line.strip().startswith("#") for line in content.split("\n")): score += 2
        if "```" in content: score += 2
        if any(kw in content.lower() for kw in ["install", "setup", "getting started"]): score += 2
        if any(marker in content for marker in ["![", "[![", "<img", "badge"]): score += 2
        if any(kw in content.lower() for kw in ["usage", "example", "how to use"]): score += 2
        readme_scores.append(min(score, 15))
    user_readme_quality = max(readme_scores) if readme_scores else 0

    top_languages = company.get("top_languages", [])
    typical_projects = company.get("typical_projects", [])

    dimensions = {
        "repo_count": {
            "user": user_repo_count,
            "cohort_avg": company.get("avg_repo_count", 10),
            "percentile": _percentile(user_repo_count, company.get("avg_repo_count", 10)),
            "verdict": "",
        },
        "star_count": {
            "user": user_star_count,
            "cohort_avg": company.get("avg_star_count", 10),
            "percentile": _percentile(user_star_count, company.get("avg_star_count", 10)),
            "verdict": "",
        },
        "language_match": {
            "user_languages": user_langs[:10],
            "company_languages": top_languages,
            **_language_overlap(user_langs, top_languages),
            "percentile": 0,
        },
        "project_relevance": {
            "typical_projects": typical_projects,
            **_project_relevance(repos, typical_projects),
            "percentile": 0,
        },
        "readme_quality": {
            "user": user_readme_quality,
            "cohort_avg": company.get("avg_readme_quality", 10),
            "percentile": _percentile(user_readme_quality, company.get("avg_readme_quality", 10)),
            "verdict": "",
        },
    }

    dimensions["language_match"]["percentile"] = min(99, max(1, dimensions["language_match"]["overlap_pct"]))
    dimensions["project_relevance"]["percentile"] = min(99, max(1, dimensions["project_relevance"]["coverage_pct"]))

    for key in ["repo_count", "star_count", "readme_quality"]:
        p = dimensions[key]["percentile"]
        if p >= 75:
            dimensions[key]["verdict"] = "Above cohort average"
        elif p >= 40:
            dimensions[key]["verdict"] = "On par with cohort"
        else:
            dimensions[key]["verdict"] = "Below cohort average"

    weights = {"repo_count": 0.15, "star_count": 0.15, "language_match": 0.30, "project_relevance": 0.25, "readme_quality": 0.15}
    overall_percentile = max(1, min(99, int(round(sum(dimensions[dim]["percentile"] * w for dim, w in weights.items())))))

    if overall_percentile >= 75:
        overall_verdict = f"Strong candidate for {company_key}"
    elif overall_percentile >= 50:
        overall_verdict = f"Competitive candidate for {company_key}"
    elif overall_percentile >= 30:
        overall_verdict = f"Developing candidate for {company_key} — focus on gaps"
    else:
        overall_verdict = f"Significant gaps for {company_key} — see recommendations"

    return {
        "company": company_key,
        "overall_percentile": overall_percentile,
        "overall_verdict": overall_verdict,
        "dimensions": dimensions,
    }
