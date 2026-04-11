"""Phase 4 dry-run test: create a throwaway repo, preview + open PR, verify safety."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from github import Auth, Github, GithubException
from backend.config import GITHUB_TOKEN, validate
from backend.services.pr_agent import preview_pr, open_readme_pr, _verify_ownership, PR_LOG_PATH
from backend.storage import read_json


TEST_REPO_NAME = "gitpulse-pr-test"


def setup_test_repo(gh: Github, username: str) -> None:
    """Create the test repo if it doesn't exist."""
    try:
        repo = gh.get_repo(f"{username}/{TEST_REPO_NAME}")
        print(f"  ✓ Test repo exists: {repo.html_url}")
    except GithubException:
        print(f"  → Creating test repo: {username}/{TEST_REPO_NAME}")
        user = gh.get_user()
        repo = user.create_repo(
            TEST_REPO_NAME,
            description="Throwaway repo for GitPulse PR agent testing",
            auto_init=True,
        )
        time.sleep(3)  # wait for GitHub to initialize
        print(f"  ✓ Created: {repo.html_url}")


def test_safety_ownership():
    """Verify ownership check rejects foreign repos."""
    gh = Github(auth=Auth.Token(GITHUB_TOKEN))
    print("\n  [Safety] Testing ownership verification...")

    # Should succeed on own repo
    authed_user = gh.get_user().login
    try:
        _verify_ownership(gh, authed_user, TEST_REPO_NAME)
        print(f"  ✓ Own repo accepted: {authed_user}/{TEST_REPO_NAME}")
    except PermissionError as e:
        print(f"  ✗ Own repo rejected (unexpected): {e}")
        raise

    # Should reject a repo we don't own
    try:
        _verify_ownership(gh, "torvalds", "linux")
        print("  ✗ Foreign repo accepted (SAFETY VIOLATION!)")
        raise AssertionError("Should have rejected foreign repo")
    except PermissionError:
        print("  ✓ Foreign repo correctly rejected")


def test_preview():
    """Test preview_pr — no writes to GitHub."""
    gh = Github(auth=Auth.Token(GITHUB_TOKEN))
    username = gh.get_user().login

    print(f"\n  [Preview] Generating README preview for {username}/{TEST_REPO_NAME}...")
    result = preview_pr(username, TEST_REPO_NAME, GITHUB_TOKEN)

    assert "current_readme" in result
    assert "suggested_readme" in result
    assert "diff_summary" in result
    assert "stats" in result

    print(f"  ✓ Current README: {len(result['current_readme'])} chars")
    print(f"  ✓ Suggested README: {len(result['suggested_readme'])} chars")
    print(f"  ✓ Diff: +{result['stats']['additions']} -{result['stats']['deletions']} lines")
    print(f"  ✓ Preview generated — NO writes to GitHub")

    return result


def test_open_pr(suggested_readme: str):
    """Test open_readme_pr — creates branch + PR on test repo."""
    gh = Github(auth=Auth.Token(GITHUB_TOKEN))
    username = gh.get_user().login

    print(f"\n  [Open PR] Creating PR on {username}/{TEST_REPO_NAME}...")
    result = open_readme_pr(username, TEST_REPO_NAME, suggested_readme, GITHUB_TOKEN)

    assert "pr_url" in result
    assert "pr_number" in result
    assert "branch_name" in result
    assert result["branch_name"].startswith("gitpulse/readme-improvement-")

    print(f"  ✓ PR opened: {result['pr_url']}")
    print(f"  ✓ PR number: #{result['pr_number']}")
    print(f"  ✓ Branch: {result['branch_name']}")

    # Verify the PR is targeting the right branch
    repo = gh.get_repo(f"{username}/{TEST_REPO_NAME}")
    pr = repo.get_pull(result["pr_number"])
    assert pr.base.ref == repo.default_branch, "PR must target default branch"
    assert pr.head.ref == result["branch_name"], "PR must come from feature branch"
    print(f"  ✓ PR targets {pr.base.ref} from {pr.head.ref}")

    # Verify only README.md was changed
    files = list(pr.get_files())
    assert len(files) == 1, f"Expected 1 file changed, got {len(files)}"
    assert files[0].filename == "README.md", f"Expected README.md, got {files[0].filename}"
    print(f"  ✓ Only README.md was changed (safety verified)")

    return result


def test_pr_log():
    """Verify all attempts were logged."""
    print(f"\n  [Log] Checking PR log...")
    log = read_json(PR_LOG_PATH)
    entries = log.get("entries", [])
    assert len(entries) >= 2, f"Expected at least 2 log entries, got {len(entries)}"

    actions = [e["action"] for e in entries]
    assert "preview" in actions, "Missing preview log entry"
    assert "open_pr" in actions, "Missing open_pr log entry"

    for entry in entries[-4:]:
        print(f"    {entry['timestamp']} | {entry['action']} | {entry['repo']} | {entry['status']}")

    print(f"  ✓ {len(entries)} total log entries")


if __name__ == "__main__":
    validate()

    print(f"{'=' * 60}")
    print(f"  Phase 4 — PR Agent Dry-Run Test")
    print(f"{'=' * 60}")

    gh = Github(auth=Auth.Token(GITHUB_TOKEN))
    username = gh.get_user().login
    print(f"\n  Authenticated as: {username}")

    # Setup
    setup_test_repo(gh, username)

    # Safety tests
    test_safety_ownership()

    # Preview (no writes)
    preview_result = test_preview()

    # Open PR (creates branch + PR)
    pr_result = test_open_pr(preview_result["suggested_readme"])

    # Verify logging
    test_pr_log()

    print(f"\n{'=' * 60}")
    print(f"  Phase 4 — All tests passed ✓")
    print(f"  PR: {pr_result['pr_url']}")
    print(f"  Test repo left intact for inspection.")
    print(f"{'=' * 60}\n")
