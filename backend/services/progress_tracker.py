"""Progress tracking: snapshot scores over time and compute deltas."""

from datetime import datetime, timezone, timedelta
from pathlib import Path

from backend.config import DATA_DIR
from backend.storage import read_json, write_json

PROGRESS_PATH = DATA_DIR / "progress_history.json"


def save_snapshot(
    username: str,
    role_category: str,
    scores: dict,
    metadata: dict | None = None,
) -> dict:
    """Append a scored snapshot to the user's progress history.

    Returns the saved snapshot (with delta_since_last computed).
    """
    history = read_json(PROGRESS_PATH)

    if username not in history:
        history[username] = {"snapshots": []}

    snapshots = history[username]["snapshots"]

    # Find last snapshot for this role_category to compute delta
    previous = None
    for s in reversed(snapshots):
        if s.get("role_category") == role_category:
            previous = s
            break

    overall = scores.get("total_score", 0)
    breakdown = scores.get("breakdown", {})

    category_scores = {}
    for cat, data in breakdown.items():
        if isinstance(data, dict):
            category_scores[cat] = data.get("score", 0)
        else:
            category_scores[cat] = data

    delta = None
    if previous:
        prev_overall = previous.get("overall_score", 0)
        delta = {
            "overall": overall - prev_overall,
            "days_since_last": 0,
            "categories": {},
        }
        prev_ts = previous.get("timestamp", "")
        if prev_ts:
            try:
                prev_dt = datetime.fromisoformat(prev_ts)
                delta["days_since_last"] = (datetime.now(timezone.utc) - prev_dt).days
            except ValueError:
                pass
        prev_cats = previous.get("category_scores", {})
        for cat, score in category_scores.items():
            prev_val = prev_cats.get(cat, 0)
            delta["categories"][cat] = score - prev_val

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role_category": role_category,
        "overall_score": overall,
        "category_scores": category_scores,
        "repo_count": (metadata or {}).get("repo_count", 0),
        "total_stars": (metadata or {}).get("total_stars", 0),
        "delta_since_last": delta,
    }

    snapshots.append(snapshot)
    write_json(PROGRESS_PATH, history)

    return snapshot


def get_progress(
    username: str,
    role_category: str | None = None,
    days: int = 90,
) -> list[dict]:
    """Return filtered snapshots for a user within the given time window."""
    history = read_json(PROGRESS_PATH)
    snapshots = history.get(username, {}).get("snapshots", [])

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    filtered = []
    for s in snapshots:
        ts = s.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
        except ValueError:
            continue

        if dt < cutoff:
            continue
        if role_category and s.get("role_category") != role_category:
            continue
        filtered.append(s)

    return filtered


def compute_deltas(snapshots: list[dict]) -> list[str]:
    """Return human-readable change descriptions between consecutive snapshots."""
    if len(snapshots) < 2:
        return ["Not enough data to compute changes (need at least 2 snapshots)."]

    descriptions = []

    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]

        ts = curr.get("timestamp", "?")
        try:
            dt = datetime.fromisoformat(ts)
            date_str = dt.strftime("%b %d, %Y")
        except ValueError:
            date_str = ts

        prev_score = prev.get("overall_score", 0)
        curr_score = curr.get("overall_score", 0)
        diff = curr_score - prev_score

        if diff > 0:
            direction = f"+{diff}"
            emoji = "↑"
        elif diff < 0:
            direction = str(diff)
            emoji = "↓"
        else:
            direction = "0"
            emoji = "→"

        desc = f"{date_str}: {curr_score}/100 ({emoji} {direction} from {prev_score})"

        # Category-level changes
        cat_changes = []
        prev_cats = prev.get("category_scores", {})
        curr_cats = curr.get("category_scores", {})
        for cat in curr_cats:
            c_diff = curr_cats.get(cat, 0) - prev_cats.get(cat, 0)
            if c_diff != 0:
                sign = f"+{c_diff}" if c_diff > 0 else str(c_diff)
                cat_label = cat.replace("_", " ").title()
                cat_changes.append(f"{cat_label} {sign}")

        if cat_changes:
            desc += f" [{', '.join(cat_changes)}]"

        # Repo/star changes
        prev_repos = prev.get("repo_count", 0)
        curr_repos = curr.get("repo_count", 0)
        prev_stars = prev.get("total_stars", 0)
        curr_stars = curr.get("total_stars", 0)

        meta_changes = []
        if curr_repos != prev_repos:
            meta_changes.append(f"repos: {prev_repos}→{curr_repos}")
        if curr_stars != prev_stars:
            meta_changes.append(f"stars: {prev_stars}→{curr_stars}")
        if meta_changes:
            desc += f" ({', '.join(meta_changes)})"

        descriptions.append(desc)

    return descriptions
