import unittest
from unittest.mock import patch, MagicMock
from gitpulse.github_analyzer import fetch_user, fetch_repos


class TestGitHubAnalyzer(unittest.TestCase):

    @patch("gitpulse.github_analyzer.requests.get")
    def test_fetch_user(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.json.return_value = {
            "login": "testuser",
            "name": "Test User",
            "bio": "A developer",
            "location": "NYC",
            "company": None,
            "blog": "",
            "public_repos": 10,
            "followers": 50,
            "following": 20,
            "created_at": "2020-01-01T00:00:00Z",
            "avatar_url": "https://example.com/avatar.png",
            "html_url": "https://github.com/testuser",
        }
        mock_get.return_value = mock_resp

        user = fetch_user("testuser")
        self.assertEqual(user["login"], "testuser")
        self.assertEqual(user["followers"], 50)

    @patch("gitpulse.github_analyzer.requests.get")
    def test_fetch_user_not_found(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.headers = {}
        mock_resp.json.return_value = None
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError):
            fetch_user("nonexistent")

    @patch("gitpulse.github_analyzer.requests.get")
    def test_fetch_repos_excludes_forks(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {}
        mock_resp.json.return_value = [
            {
                "name": "my-project",
                "description": "A project",
                "language": "Python",
                "stargazers_count": 5,
                "forks_count": 1,
                "updated_at": "2024-01-01T00:00:00Z",
                "topics": ["python"],
                "html_url": "https://github.com/testuser/my-project",
                "fork": False,
                "size": 100,
            },
            {
                "name": "forked-repo",
                "description": "A fork",
                "language": "JavaScript",
                "stargazers_count": 100,
                "forks_count": 50,
                "updated_at": "2024-01-01T00:00:00Z",
                "topics": [],
                "html_url": "https://github.com/testuser/forked-repo",
                "fork": True,
                "size": 200,
            },
        ]
        mock_get.return_value = mock_resp

        repos = fetch_repos("testuser")
        self.assertEqual(len(repos), 1)
        self.assertEqual(repos[0]["name"], "my-project")


if __name__ == "__main__":
    unittest.main()
