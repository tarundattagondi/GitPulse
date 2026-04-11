"""Phase 1 live test: fetch tarundattagondi and print scored summary."""
import asyncio
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import validate
from backend.services.github_service import (
    fetch_profile,
    fetch_all_repos,
    fetch_readme,
    fetch_pinned_repos,
    fetch_recent_commits,
)
from backend.services.scorer import score_profile_full
from backend.storage import write_json


async def main():
    validate()
    username = "tarundattagondi"

    print(f"{'=' * 60}")
    print(f"  GitPulse Phase 1 — Live Test")
    print(f"  Target: {username}")
    print(f"{'=' * 60}\n")

    # 1. Fetch profile
    print("→ Fetching profile...")
    profile = await fetch_profile(username)
    print(f"  Name:      {profile.get('name') or profile['login']}")
    print(f"  Bio:       {profile.get('bio') or 'N/A'}")
    print(f"  Location:  {profile.get('location') or 'N/A'}")
    print(f"  Repos:     {profile['public_repos']}")
    print(f"  Followers: {profile['followers']}")

    # 2. Fetch repos + languages
    print("\n→ Fetching repos (with per-repo languages)...")
    repos = await fetch_all_repos(username)
    print(f"  Found {len(repos)} repos (excluding forks)")
    for r in repos[:5]:
        langs = ", ".join(r["languages"].keys()) if r["languages"] else r.get("language") or "?"
        print(f"    • {r['name']} [{langs}] ⭐{r['stars']}")

    # 3. Aggregate languages
    all_langs = {}
    for r in repos:
        for lang, b in r.get("languages", {}).items():
            all_langs[lang] = all_langs.get(lang, 0) + b
    top_langs = sorted(all_langs.items(), key=lambda x: x[1], reverse=True)[:8]
    print(f"\n→ Top languages across all repos:")
    for lang, bytes_count in top_langs:
        print(f"    {lang}: {bytes_count:,} bytes")

    # 4. Fetch READMEs for top repos
    print("\n→ Fetching READMEs...")
    readmes = {}
    for r in repos[:5]:
        readme = await fetch_readme(username, r["name"])
        readmes[r["name"]] = readme
        status = f"{len(readme)} chars" if readme else "missing"
        print(f"    {r['name']}: {status}")

    # 5. Fetch pinned repos
    print("\n→ Fetching pinned repos (GraphQL)...")
    pinned = await fetch_pinned_repos(username)
    if pinned:
        for p in pinned:
            print(f"    📌 {p['name']} ({p.get('language') or '?'}) ⭐{p['stars']}")
    else:
        print("    (none pinned)")

    # 6. Count recent commits
    print("\n→ Counting commits (last 90 days)...")
    commit_count = await fetch_recent_commits(username, repos)
    print(f"    Total: {commit_count} commits")

    # 7. Run scorer
    print("\n→ Running 5-category scorer (Claude AI for skills + relevance)...")
    score = score_profile_full(profile, repos, readmes, commit_count)

    print(f"\n{'=' * 60}")
    print(f"  SCORE: {score['total_score']}/{score['max_score']}")
    print(f"{'=' * 60}")
    for category, data in score["breakdown"].items():
        label = category.replace("_", " ").title()
        bar_width = 20
        filled = int((data["score"] / data["max"]) * bar_width) if data["max"] > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"  {label:<25} [{bar}] {data['score']}/{data['max']}")
        print(f"    → {data['reasoning']}")
    print()

    # Save output
    output = {
        "username": username,
        "profile": profile,
        "repos_count": len(repos),
        "top_languages": dict(top_langs),
        "pinned_repos": pinned,
        "readmes_fetched": {k: (len(v) if v else 0) for k, v in readmes.items()},
        "commit_count_90d": commit_count,
        "score": score,
    }
    write_json(Path(__file__).resolve().parent.parent / "data" / "phase1_live_test.json", output)
    print(f"  Saved full output → data/phase1_live_test.json\n")


if __name__ == "__main__":
    asyncio.run(main())
