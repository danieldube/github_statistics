"""Tests for data-protection policy enforcement."""

import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import yaml

from github_statistics.cli import main
from github_statistics.models import CommitInfo, PullRequest
from github_statistics.stats import (
    compute_active_group_counts,
    evaluate_data_protection_thresholds,
    get_active_users_in_period,
)


def _make_pr_with_commits(repo: str, commit_authors_dates):
    commits = [
        CommitInfo(
            sha="sha-%s" % idx,
            author=author,
            committed_at=committed_at,
            message="m",
        )
        for idx, (author, committed_at) in enumerate(commit_authors_dates)
    ]
    return PullRequest(
        number=1,
        title="t",
        author="author",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=1,
        deletions=1,
        commits=commits,
        repository=repo,
    )


def test_active_user_with_commit_in_period_is_active():
    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    until = datetime(2026, 1, 31, tzinfo=timezone.utc)
    pr = _make_pr_with_commits(
        "org/repo",
        [
            ("alice", datetime(2026, 1, 10, tzinfo=timezone.utc)),
            ("bob", datetime(2025, 12, 31, tzinfo=timezone.utc)),
        ],
    )

    active_users = get_active_users_in_period([pr], since=since, until=until)

    assert "alice" in active_users
    assert "bob" not in active_users


def test_active_user_boundary_timestamps_are_inclusive():
    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    until = datetime(2026, 1, 31, tzinfo=timezone.utc)
    pr = _make_pr_with_commits(
        "org/repo",
        [
            ("alice", since),
            ("bob", until),
        ],
    )

    active_users = get_active_users_in_period([pr], since=since, until=until)

    assert active_users == {"alice", "bob"}


def test_compute_active_group_counts():
    active_users = {"alice", "bob", "carol"}
    groups = {
        "team_alpha": ["alice", "bob", "dave", "erin", "frank"],
        "team_beta": ["carol", "gina", "hugo", "ivan", "jane"],
    }

    counts = compute_active_group_counts(groups, active_users)

    assert counts["team_alpha"] == 2
    assert counts["team_beta"] == 1


def test_threshold_enforcement_fails_when_group_or_repo_below_threshold():
    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    until = datetime(2026, 1, 31, tzinfo=timezone.utc)
    pr = _make_pr_with_commits(
        "org/repo1",
        [
            ("alice", datetime(2026, 1, 10, tzinfo=timezone.utc)),
            ("bob", datetime(2026, 1, 11, tzinfo=timezone.utc)),
            ("carol", datetime(2026, 1, 12, tzinfo=timezone.utc)),
        ],
    )
    groups = {
        "team_alpha": ["alice", "bob", "carol", "dave", "erin"],
    }

    result = evaluate_data_protection_thresholds(
        pull_requests=[pr],
        user_groups=groups,
        repositories=["org/repo1"],
        since=since,
        until=until,
    )

    assert result.passed is False
    assert len(result.violations) == 2


def test_threshold_enforcement_passes_when_all_thresholds_met():
    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    until = datetime(2026, 1, 31, tzinfo=timezone.utc)
    authors = [
        ("alice", datetime(2026, 1, 10, tzinfo=timezone.utc)),
        ("bob", datetime(2026, 1, 11, tzinfo=timezone.utc)),
        ("carol", datetime(2026, 1, 12, tzinfo=timezone.utc)),
        ("dave", datetime(2026, 1, 13, tzinfo=timezone.utc)),
        ("erin", datetime(2026, 1, 14, tzinfo=timezone.utc)),
    ]
    pr = _make_pr_with_commits("org/repo1", authors)
    groups = {"team_alpha": ["alice", "bob", "carol", "dave", "erin"]}

    result = evaluate_data_protection_thresholds(
        pull_requests=[pr],
        user_groups=groups,
        repositories=["org/repo1"],
        since=since,
        until=until,
    )

    assert result.passed is True
    assert result.violations == []


def test_cli_violation_without_override_fails(tmp_path, monkeypatch, capsys):
    config_data = {
        "github": {"base_url": "https://api.github.com", "api_token": "t"},
        "repositories": ["org/repo1"],
        "user_groups": {
            "team_alpha": ["alice", "bob", "carol", "dave", "erin"]
        },
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setattr(sys, "argv", ["github_statistics", str(config_file)])

    with patch(
        "github_statistics.github_client.HttpGitHubClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_pull_requests.return_value = []
        exit_code = main()

    assert exit_code != 0
    captured = capsys.readouterr()
    assert "data protection" in captured.err.lower()


def test_cli_violation_with_override_but_not_confirmed_fails(
    tmp_path, monkeypatch
):
    config_data = {
        "github": {"base_url": "https://api.github.com", "api_token": "t"},
        "repositories": ["org/repo1"],
        "user_groups": {
            "team_alpha": ["alice", "bob", "carol", "dave", "erin"]
        },
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "github_statistics",
            str(config_file),
            "--overwrite-data-protection",
        ],
    )

    with (
        patch("builtins.input", return_value="n"),
        patch(
            "github_statistics.github_client.HttpGitHubClient"
        ) as mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_pull_requests.return_value = []
        exit_code = main()

    assert exit_code != 0


def test_cli_violation_with_override_and_confirmed_y_proceeds(
    tmp_path, monkeypatch, capsys
):
    config_data = {
        "github": {"base_url": "https://api.github.com", "api_token": "t"},
        "repositories": ["org/repo1"],
        "user_groups": {
            "team_alpha": ["alice", "bob", "carol", "dave", "erin"]
        },
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "github_statistics",
            str(config_file),
            "--overwrite-data-protection",
        ],
    )

    with (
        patch("builtins.input", return_value="y"),
        patch(
            "github_statistics.github_client.HttpGitHubClient"
        ) as mock_client_class,
    ):
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_pull_requests.return_value = []
        exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "disclaimer" in captured.out.lower()
