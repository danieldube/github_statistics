"""End-to-end tests for CLI orchestration."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from github_statistics.cli import main


def test_cli_end_to_end_creates_report(capsys):
    """Test that CLI creates a Markdown report file."""
    # Create a temporary config file
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "test_config.yaml")
        output_path = os.path.join(tmpdir, "test_config_statistics.md")

        # Write test config
        with open(config_path, "w") as f:
            f.write(
                """
github:
  base_url: https://api.github.com
  api_token: inline-token
  verify_ssl: true

repositories:
  - org/repo1

users:
  - alice
"""
            )

        # Mock the HttpGitHubClient
        with patch(
            "github_statistics.github_client.HttpGitHubClient"
        ) as mock_client_class:
            # Create mock client instance
            mock_client = MagicMock()
            mock_client_class.from_token_or_env.return_value = mock_client

            # Mock list_pull_requests to return test data
            mock_client.list_pull_requests.return_value = [
                {
                    "number": 1,
                    "title": "Test PR",
                    "user": {"login": "alice"},
                    "state": "closed",
                    "created_at": "2026-01-01T10:00:00Z",
                    "closed_at": "2026-01-05T10:00:00Z",
                    "merged_at": "2026-01-05T10:00:00Z",
                }
            ]

            # Mock get_pull_request_details to return additions/deletions
            mock_client.get_pull_request_details.return_value = {
                "number": 1,
                "additions": 10,
                "deletions": 5,
            }

            # Mock other client methods
            mock_client.get_pull_request_commits.return_value = [
                {
                    "sha": "abc123",
                    "commit": {
                        "author": {
                            "name": "alice",
                            "date": "2026-01-02T10:00:00Z",
                        },
                        "message": "Test commit",
                    },
                }
            ]
            mock_client.get_pull_request_reviews.return_value = []
            mock_client.get_pull_request_review_comments.return_value = []
            mock_client.get_issue_comments.return_value = []
            mock_client.get_issue_timeline.return_value = []

            # Run main
            with patch("sys.argv", ["github_statistics", config_path]):
                exit_code = main()

        # Capture output to help with debugging
        captured = capsys.readouterr()
        if exit_code != 0:
            print(f"STDOUT: {captured.out}")
            print(f"STDERR: {captured.err}")

        # Verify exit code
        assert exit_code == 0, f"CLI should exit with code 0, got {exit_code}"

        # Verify output file was created
        assert os.path.exists(
            output_path
        ), f"Output file should exist at {output_path}"

        # Verify file contents
        with open(output_path) as f:
            content = f.read()

        # Check for expected sections
        assert "# GitHub Statistics Report" in content
        assert "## Metadata" in content
        assert "## Repositories" in content
        assert "## Users" in content
        assert "org/repo1" in content
        assert "alice" in content


def test_cli_end_to_end_with_custom_output():
    """Test that CLI respects custom output path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yaml")
        custom_output = os.path.join(tmpdir, "custom_report.md")

        # Write test config
        with open(config_path, "w") as f:
            f.write(
                """
github:
  base_url: https://api.github.com
  api_token: inline-token

repositories:
  - org/repo1

users: []
"""
            )

        # Mock the HttpGitHubClient
        with patch(
            "github_statistics.github_client.HttpGitHubClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.from_token_or_env.return_value = mock_client

            # Mock minimal PR data
            mock_client.list_pull_requests.return_value = []

            argv = [
                "github_statistics",
                config_path,
                "--output",
                custom_output,
            ]
            with patch("sys.argv", argv):
                exit_code = main()

        assert exit_code == 0
        assert os.path.exists(custom_output)


def test_cli_end_to_end_with_date_filters():
    """Test that CLI applies date filters correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yaml")
        output_path = os.path.join(tmpdir, "config_statistics.md")

        # Write test config
        with open(config_path, "w") as f:
            f.write(
                """
github:
  base_url: https://api.github.com
  api_token: inline-token

repositories:
  - org/repo1

users: []
"""
            )

        # Mock the HttpGitHubClient
        with patch(
            "github_statistics.github_client.HttpGitHubClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.from_token_or_env.return_value = mock_client
            mock_client.list_pull_requests.return_value = []

            argv = [
                "github_statistics",
                config_path,
                "--since",
                "2026-01-01",
                "--until",
                "2026-02-01",
            ]
            with patch("sys.argv", argv):
                exit_code = main()

        assert exit_code == 0
        assert os.path.exists(output_path)

        # Verify date filters in report
        with open(output_path) as f:
            content = f.read()

        assert "2026-01-01" in content
        assert "2026-02-01" in content


def test_cli_end_to_end_with_statistics():
    """Test that CLI generates statistics correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yaml")
        output_path = os.path.join(tmpdir, "config_statistics.md")

        # Write test config
        with open(config_path, "w") as f:
            f.write(
                """
github:
  base_url: https://api.github.com
  api_token: inline-token

repositories:
  - org/repo1

users:
  - alice
  - bob
"""
            )

        # Mock the HttpGitHubClient
        with patch(
            "github_statistics.github_client.HttpGitHubClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.from_token_or_env.return_value = mock_client

            # Mock PR data with reviews
            mock_client.list_pull_requests.return_value = [
                {
                    "number": 1,
                    "title": "Test PR 1",
                    "user": {"login": "alice"},
                    "state": "closed",
                    "created_at": "2026-01-01T10:00:00Z",
                    "closed_at": "2026-01-03T10:00:00Z",
                    "merged_at": "2026-01-03T10:00:00Z",
                },
                {
                    "number": 2,
                    "title": "Test PR 2",
                    "user": {"login": "bob"},
                    "state": "open",
                    "created_at": "2026-01-05T10:00:00Z",
                    "closed_at": None,
                    "merged_at": None,
                },
            ]

            # Mock get_pull_request_details to return additions/deletions
            def mock_details(owner, repo, number):
                details = {
                    1: {"number": 1, "additions": 50, "deletions": 25},
                    2: {"number": 2, "additions": 30, "deletions": 15},
                }
                return details.get(number, {})

            mock_client.get_pull_request_details.side_effect = mock_details

            mock_client.get_pull_request_commits.return_value = [
                {
                    "sha": "abc123",
                    "commit": {
                        "author": {
                            "name": "alice",
                            "date": "2026-01-02T10:00:00Z",
                        },
                        "message": "Test commit",
                    },
                }
            ]
            mock_client.get_pull_request_reviews.return_value = [
                {
                    "user": {"login": "bob"},
                    "submitted_at": "2026-01-02T14:00:00Z",
                    "state": "APPROVED",
                }
            ]
            mock_client.get_pull_request_review_comments.return_value = []
            mock_client.get_issue_comments.return_value = []
            mock_client.get_issue_timeline.return_value = []

            with patch("sys.argv", ["github_statistics", config_path]):
                exit_code = main()

        assert exit_code == 0
        assert os.path.exists(output_path)

        # Verify statistics in report
        with open(output_path) as f:
            content = f.read()

        # Check for repository stats
        assert "Duration merged pull requests" in content
        assert "Duration open pull requests" in content

        # Check for user stats
        assert "alice" in content
        assert "bob" in content


def test_cli_end_to_end_missing_token():
    """Test that CLI fails gracefully when token is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "config.yaml")

        # Write test config
        with open(config_path, "w") as f:
            f.write(
                """
github:
  base_url: https://api.github.com
  token_env: MISSING_TOKEN

repositories:
  - org/repo1

users: []
"""
            )

        # Ensure the token env var doesn't exist and run main
        with patch.dict(os.environ, {}, clear=True), patch(
            "sys.argv", ["github_statistics", config_path]
        ):
            exit_code = main()

        # Should exit with error
        assert exit_code != 0
