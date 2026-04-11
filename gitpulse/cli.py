import argparse
import sys
from gitpulse import config, __version__
from gitpulse.utils import print_table, print_score_bar, format_number


def cmd_analyze(args):
    from gitpulse.github_analyzer import analyze_profile

    profile = analyze_profile(args.username)
    user = profile["user"]
    summary = profile["summary"]

    print(f"\n{'=' * 60}")
    print(f"  GitHub Profile: {user.get('name') or user['login']}")
    print(f"  {user['html_url']}")
    print(f"{'=' * 60}")
    print(f"  Bio:       {user.get('bio') or 'N/A'}")
    print(f"  Location:  {user.get('location') or 'N/A'}")
    print(f"  Company:   {user.get('company') or 'N/A'}")
    print(f"  Repos:     {summary['repo_count']}")
    print(f"  Stars:     {format_number(summary['total_stars'])}")
    print(f"  Forks:     {format_number(summary['total_forks'])}")
    print(f"  Followers: {format_number(user['followers'])}")
    print(f"  Account:   {summary['account_age_days']} days old")

    if summary["primary_languages"]:
        print(f"\n  Top Languages: {', '.join(summary['primary_languages'])}")

    if profile["top_repos"]:
        print(f"\n  Top Repositories:")
        for r in profile["top_repos"]:
            lang = r.get("language") or "?"
            print(f"    ⭐ {r['stars']}  {r['name']} ({lang}) - {r.get('description') or 'No description'}")

    if profile["contributions"]:
        print(f"\n  Recent Activity (last 90 days):")
        for event, count in sorted(profile["contributions"].items(), key=lambda x: x[1], reverse=True):
            print(f"    {event}: {count}")

    print()
    return profile


def cmd_scan(args):
    from gitpulse.job_scanner import scan_jobs

    keywords = args.keywords.split(",") if args.keywords else None
    profile = None

    if args.username:
        from gitpulse.github_analyzer import analyze_profile
        profile = analyze_profile(args.username)

    jobs = scan_jobs(profile=profile, keywords=keywords)

    if not jobs:
        print("\n  No jobs found. Try different keywords.")
        return

    print(f"\n{'=' * 60}")
    print(f"  Found {len(jobs)} Job/Internship Listings")
    print(f"{'=' * 60}\n")

    for i, job in enumerate(jobs[:20], 1):
        print(f"  {i}. {job.get('company', 'Unknown')} - {job.get('role', 'N/A')}")
        if job.get("location"):
            print(f"     Location: {job['location']}")
        if job.get("url"):
            print(f"     Link: {job['url']}")
        print(f"     Source: {job.get('source', 'unknown')}")
        print()

    return jobs


def cmd_score(args):
    from gitpulse.github_analyzer import analyze_profile
    from gitpulse.scorer import score_profile

    profile = analyze_profile(args.username)
    score = score_profile(profile, args.job_description)

    print(f"\n{'=' * 60}")
    print(f"  Profile Score for {args.username}")
    print(f"{'=' * 60}\n")

    print_score_bar("Overall", score.get("overall_score", 0))
    print()

    breakdown = score.get("breakdown", {})
    for key, value in breakdown.items():
        label = key.replace("_", " ").title()
        print_score_bar(label, value)

    if score.get("strengths"):
        print(f"\n  Strengths:")
        for s in score["strengths"]:
            print(f"    ✓ {s}")

    if score.get("weaknesses"):
        print(f"\n  Areas for Improvement:")
        for w in score["weaknesses"]:
            print(f"    ✗ {w}")

    if score.get("recommendations"):
        print(f"\n  Recommendations:")
        for r in score["recommendations"]:
            print(f"    → {r}")

    if score.get("job_fit_score") is not None:
        print(f"\n  Job Fit:")
        print_score_bar("Job Match", score["job_fit_score"])
        if score.get("job_fit_analysis"):
            print(f"    {score['job_fit_analysis']}")

    print()
    return score


def cmd_improve(args):
    from gitpulse.github_analyzer import analyze_profile
    from gitpulse.scorer import score_profile
    from gitpulse.pr_generator import suggest_improvements, execute_improvements

    profile = analyze_profile(args.username)
    score = score_profile(profile)
    improvements = suggest_improvements(profile, score)

    if not improvements:
        print("\n  No improvements suggested — your profile looks great!")
        return

    print(f"\n{'=' * 60}")
    print(f"  Suggested Improvements ({len(improvements)} found)")
    print(f"{'=' * 60}\n")

    for i, imp in enumerate(improvements, 1):
        auto = " [automatable]" if imp["can_automate"] else ""
        repo = f" ({imp['repo']})" if imp.get("repo") else ""
        print(f"  {i}. [{imp['type']}]{repo} {imp['description']}{auto}")

    if args.auto_pr:
        print(f"\n  Executing automatable improvements...")
        results = execute_improvements(args.username, profile, improvements, auto_pr=True)
        print(f"\n  Completed {len(results)} improvements.")
    else:
        print(f"\n  Run with --auto-pr to automatically apply changes.")

    return improvements


def cmd_full(args):
    from gitpulse.github_analyzer import analyze_profile
    from gitpulse.scorer import score_profile
    from gitpulse.job_scanner import scan_jobs
    from gitpulse.pr_generator import suggest_improvements

    print("=" * 60)
    print("  GitPulse - Full Profile Analysis")
    print("=" * 60)

    # 1. Analyze
    profile = analyze_profile(args.username)
    user = profile["user"]
    summary = profile["summary"]

    print(f"\n  Profile: {user.get('name') or user['login']} ({user['html_url']})")
    print(f"  {summary['repo_count']} repos | {format_number(summary['total_stars'])} stars | {', '.join(summary['primary_languages'][:3])}")

    # 2. Score
    score = score_profile(profile)
    print(f"\n  Overall Score: {score.get('overall_score', 'N/A')}/100")
    print_score_bar("Overall", score.get("overall_score", 0))

    # 3. Jobs
    jobs = scan_jobs(profile=profile)
    if jobs:
        print(f"\n  Top Job Matches:")
        for j in jobs[:5]:
            print(f"    • {j.get('company', '?')} - {j.get('role', '?')}")

    # 4. Improvements
    improvements = suggest_improvements(profile, score)
    if improvements:
        print(f"\n  Top Improvements:")
        for imp in improvements[:5]:
            print(f"    → {imp['description']}")

    print(f"\n{'=' * 60}")
    print(f"  Run 'gitpulse improve {args.username} --auto-pr' to apply fixes")
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(
        prog="gitpulse",
        description="GitPulse - Autonomous GitHub Career Agent",
    )
    parser.add_argument("--version", action="version", version=f"gitpulse {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze a GitHub profile")
    p_analyze.add_argument("username", help="GitHub username")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan for jobs/internships")
    p_scan.add_argument("--username", "-u", help="GitHub username for personalized results")
    p_scan.add_argument("--keywords", "-k", help="Comma-separated keywords to filter")

    # score
    p_score = subparsers.add_parser("score", help="Score a GitHub profile")
    p_score.add_argument("username", help="GitHub username")
    p_score.add_argument("--job-description", "-j", help="Job description to score against")

    # improve
    p_improve = subparsers.add_parser("improve", help="Suggest and apply profile improvements")
    p_improve.add_argument("username", help="GitHub username")
    p_improve.add_argument("--auto-pr", action="store_true", help="Automatically open PRs for improvements")

    # full
    p_full = subparsers.add_parser("full", help="Run full analysis pipeline")
    p_full.add_argument("username", help="GitHub username")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config.validate()

    commands = {
        "analyze": cmd_analyze,
        "scan": cmd_scan,
        "score": cmd_score,
        "improve": cmd_improve,
        "full": cmd_full,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
