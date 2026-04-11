import unittest
from backend.services.scorer import (
    score_readme_quality,
    score_activity_level,
    score_profile_completeness,
    W_README_QUALITY,
    W_ACTIVITY_LEVEL,
    W_PROFILE_COMPLETENESS,
)


class TestScorerEmptyProfile(unittest.TestCase):
    """Empty profile should score 0 on completeness."""

    def test_empty_profile(self):
        result = score_profile_completeness({})
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["max"], W_PROFILE_COMPLETENESS)
        self.assertFalse(any(result["checks"].values()))


class TestScorerNoRepos(unittest.TestCase):
    """No READMEs should score 0 on readme quality."""

    def test_no_readmes(self):
        result = score_readme_quality({})
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["max"], W_README_QUALITY)

    def test_all_none_readmes(self):
        result = score_readme_quality({"repo1": None, "repo2": None})
        self.assertEqual(result["score"], 0)


class TestScorerNoActivity(unittest.TestCase):
    """Zero commits should score 0 on activity."""

    def test_zero_commits(self):
        result = score_activity_level(0)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["commits_90d"], 0)

    def test_negative_commits(self):
        result = score_activity_level(-5)
        self.assertEqual(result["score"], 0)


class TestScorerPerfectProfile(unittest.TestCase):
    """A fully filled profile should score max on completeness."""

    def test_perfect_profile(self):
        profile = {
            "name": "Jane Doe",
            "bio": "Full-stack developer",
            "location": "San Francisco",
            "company": "Acme Corp",
            "blog": "https://jane.dev",
            "avatar_url": "https://example.com/avatar.png",
        }
        result = score_profile_completeness(profile)
        self.assertEqual(result["score"], W_PROFILE_COMPLETENESS)
        self.assertTrue(all(result["checks"].values()))

    def test_perfect_readme(self):
        readme = (
            "# My Project\n\n"
            "[![Build](https://img.shields.io/badge/build-passing-green)]\n\n"
            "## Installation\n\n"
            "```bash\npip install myproject\n```\n\n"
            "## Usage\n\n"
            "```python\nimport myproject\nmyproject.run()\n```\n\n"
            "## Getting Started\n\nThis is a longer description that definitely "
            "exceeds two hundred characters to pass the length check. " * 3
        )
        result = score_readme_quality({"myproject": readme})
        self.assertEqual(result["score"], W_README_QUALITY)

    def test_high_activity(self):
        result = score_activity_level(1024)
        self.assertEqual(result["score"], W_ACTIVITY_LEVEL)


class TestScorerPartialProfile(unittest.TestCase):
    """Partial data should yield partial scores."""

    def test_partial_completeness(self):
        profile = {"name": "Jane", "bio": "Dev", "location": None, "company": None, "avatar_url": "x"}
        result = score_profile_completeness(profile)
        # name(2) + bio(2) + avatar(2) = 6
        self.assertEqual(result["score"], 6)

    def test_partial_readme(self):
        readme = "# Title\n\nShort README."
        result = score_readme_quality({"repo": readme})
        # has_readme(3) + has_headings(2) = 5 (too short, no code, no install, no badges, no usage)
        self.assertEqual(result["score"], 5)

    def test_moderate_activity(self):
        result = score_activity_level(31)
        self.assertEqual(result["score"], 5)  # log2(32) = 5

    def test_low_activity(self):
        result = score_activity_level(1)
        self.assertEqual(result["score"], 1)  # log2(2) = 1
