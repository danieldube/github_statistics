"""Tests for the collector module using FakeGitHubClient."""

from datetime import datetime, timezone

from github_statistics.cli import RunOptions
from github_statistics.collector import collect_prs
from github_statistics.config import Config
from github_statistics.github_client import FakeGitHubClient


def test_collect_prs_basic_pr():
    """Test collecting a single PR with basic information."""
    # Setup fake client with one PR
    pr_data = {
        "number": 1,
        "title": "Add feature X",
        "user": {"login": "alice"},
        "created_at": "2026-01-01T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 100,
        "deletions": 20,
    }

    client = FakeGitHubClient(pull_requests=[pr_data])

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=["alice"],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["owner/repo"],
        users=["alice"],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    pr = prs[0]
    assert pr.number == 1
    assert pr.title == "Add feature X"
    assert pr.author == "alice"
    assert pr.state == "open"
    assert pr.additions == 100
    assert pr.deletions == 20
    assert pr.created_at == datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert pr.closed_at is None
    assert pr.merged_at is None


def test_collect_prs_with_commits():
    """Test collecting a PR with commits."""
    pr_data = {
        "number": 1,
        "title": "Add feature",
        "user": {"login": "bob"},
        "created_at": "2026-01-01T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 50,
        "deletions": 10,
    }

    commit_data = [
        {
            "sha": "abc123",
            "commit": {
                "author": {"name": "bob", "date": "2026-01-01T11:00:00Z"},
                "message": "Initial commit",
            },
        },
        {
            "sha": "def456",
            "commit": {
                "author": {"name": "bob", "date": "2026-01-01T12:00:00Z"},
                "message": "Fix typo",
            },
        },
    ]

    client = FakeGitHubClient(
        pull_requests=[pr_data], commits={1: commit_data}
    )

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    pr = prs[0]
    assert len(pr.commits) == 2
    assert pr.commits[0].sha == "abc123"
    assert pr.commits[0].author == "bob"
    assert pr.commits[0].message == "Initial commit"
    assert pr.commits[1].sha == "def456"
    assert pr.commits[1].message == "Fix typo"


def test_collect_prs_with_comments():
    """Test collecting a PR with both issue and review comments."""
    pr_data = {
        "number": 1,
        "title": "Add feature",
        "user": {"login": "alice"},
        "created_at": "2026-01-01T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 50,
        "deletions": 10,
    }

    issue_comments_data = [
        {
            "user": {"login": "bob"},
            "created_at": "2026-01-01T11:00:00Z",
            "body": "Looks good!",
        },
    ]

    review_comments_data = [
        {
            "user": {"login": "charlie"},
            "created_at": "2026-01-01T12:00:00Z",
            "body": "Consider refactoring this.",
        },
    ]

    client = FakeGitHubClient(
        pull_requests=[pr_data],
        issue_comments={1: issue_comments_data},
        review_comments={1: review_comments_data},
    )

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    pr = prs[0]
    assert len(pr.comments) == 2
    # Comments should be sorted by created_at
    assert pr.comments[0].author == "bob"
    assert pr.comments[0].body == "Looks good!"
    assert pr.comments[1].author == "charlie"
    assert pr.comments[1].body == "Consider refactoring this."


def test_collect_prs_with_reviews():
    """Test collecting a PR with reviews."""
    pr_data = {
        "number": 1,
        "title": "Add feature",
        "user": {"login": "alice"},
        "created_at": "2026-01-01T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 50,
        "deletions": 10,
    }

    reviews_data = [
        {
            "user": {"login": "bob"},
            "submitted_at": "2026-01-01T11:00:00Z",
            "state": "APPROVED",
        },
        {
            "user": {"login": "charlie"},
            "submitted_at": "2026-01-01T12:00:00Z",
            "state": "CHANGES_REQUESTED",
        },
    ]

    client = FakeGitHubClient(
        pull_requests=[pr_data], reviews={1: reviews_data}
    )

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    pr = prs[0]
    assert len(pr.reviews) == 2
    assert pr.reviews[0].reviewer == "bob"
    assert pr.reviews[0].state == "APPROVED"
    assert pr.reviews[1].reviewer == "charlie"
    assert pr.reviews[1].state == "CHANGES_REQUESTED"


def test_collect_prs_with_timeline_events():
    """Test collecting a PR with timeline events."""
    pr_data = {
        "number": 1,
        "title": "Add feature",
        "user": {"login": "alice"},
        "created_at": "2026-01-01T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 50,
        "deletions": 10,
    }

    timeline_data = [
        {
            "event": "review_requested",
            "created_at": "2026-01-01T11:00:00Z",
            "requested_reviewer": {"login": "bob"},
        },
        {
            "event": "ready_for_review",
            "created_at": "2026-01-01T12:00:00Z",
        },
        {
            "event": "review_requested",
            "created_at": "2026-01-01T13:00:00Z",
            "requested_reviewer": {"login": "charlie"},
        },
    ]

    client = FakeGitHubClient(
        pull_requests=[pr_data], timeline_events={1: timeline_data}
    )

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    pr = prs[0]
    assert len(pr.review_requests) == 2
    assert pr.review_requests[0].requested_reviewer == "bob"
    assert pr.review_requests[1].requested_reviewer == "charlie"
    assert pr.ready_for_review_at is not None
    assert pr.ready_for_review_at.ready_at == datetime(
        2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc
    )


def test_collect_prs_complete_aggregation():
    """Test collecting a PR with all types of data."""
    pr_data = {
        "number": 42,
        "title": "Complete Feature",
        "user": {"login": "alice"},
        "created_at": "2026-01-01T10:00:00Z",
        "state": "closed",
        "closed_at": "2026-01-05T10:00:00Z",
        "merged_at": "2026-01-05T10:00:00Z",
        "additions": 200,
        "deletions": 50,
    }

    commits_data = [
        {
            "sha": "abc123",
            "commit": {
                "author": {"name": "alice", "date": "2026-01-01T11:00:00Z"},
                "message": "Initial implementation",
            },
        },
    ]

    issue_comments_data = [
        {
            "user": {"login": "bob"},
            "created_at": "2026-01-02T10:00:00Z",
            "body": "Great work!",
        },
    ]

    reviews_data = [
        {
            "user": {"login": "bob"},
            "submitted_at": "2026-01-03T10:00:00Z",
            "state": "APPROVED",
        },
    ]

    timeline_data = [
        {
            "event": "review_requested",
            "created_at": "2026-01-02T09:00:00Z",
            "requested_reviewer": {"login": "bob"},
        },
        {
            "event": "ready_for_review",
            "created_at": "2026-01-01T12:00:00Z",
        },
    ]

    client = FakeGitHubClient(
        pull_requests=[pr_data],
        commits={42: commits_data},
        issue_comments={42: issue_comments_data},
        reviews={42: reviews_data},
        timeline_events={42: timeline_data},
    )

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    pr = prs[0]
    assert pr.number == 42
    assert pr.title == "Complete Feature"
    assert pr.author == "alice"
    assert pr.state == "closed"
    assert pr.merged_at == datetime(2026, 1, 5, 10, 0, 0, tzinfo=timezone.utc)
    assert len(pr.commits) == 1
    assert len(pr.comments) == 1
    assert len(pr.reviews) == 1
    assert len(pr.review_requests) == 1
    assert pr.ready_for_review_at is not None


def test_collect_prs_filters_by_since_date():
    """Test that PRs are filtered by since date."""
    pr1_data = {
        "number": 1,
        "title": "Old PR",
        "user": {"login": "alice"},
        "created_at": "2025-12-01T10:00:00Z",
        "state": "closed",
        "closed_at": "2025-12-02T10:00:00Z",
        "merged_at": None,
        "additions": 10,
        "deletions": 5,
    }

    pr2_data = {
        "number": 2,
        "title": "New PR",
        "user": {"login": "bob"},
        "created_at": "2026-01-15T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 20,
        "deletions": 10,
    }

    client = FakeGitHubClient(pull_requests=[pr1_data, pr2_data])

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    # Filter to only get PRs from 2026-01-01 onwards
    options = RunOptions(
        config=config,
        since=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        until=None,
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    assert prs[0].number == 2
    assert prs[0].title == "New PR"


def test_collect_prs_filters_by_until_date():
    """Test that PRs are filtered by until date."""
    pr1_data = {
        "number": 1,
        "title": "Old PR",
        "user": {"login": "alice"},
        "created_at": "2025-12-01T10:00:00Z",
        "state": "closed",
        "closed_at": "2025-12-02T10:00:00Z",
        "merged_at": None,
        "additions": 10,
        "deletions": 5,
    }

    pr2_data = {
        "number": 2,
        "title": "New PR",
        "user": {"login": "bob"},
        "created_at": "2026-01-15T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 20,
        "deletions": 10,
    }

    client = FakeGitHubClient(pull_requests=[pr1_data, pr2_data])

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    # Filter to only get PRs before 2026-01-01
    options = RunOptions(
        config=config,
        since=None,
        until=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    assert prs[0].number == 1
    assert prs[0].title == "Old PR"


def test_collect_prs_filters_by_since_and_until():
    """Test that PRs are filtered by both since and until dates."""
    pr1_data = {
        "number": 1,
        "title": "Too Old",
        "user": {"login": "alice"},
        "created_at": "2025-11-01T10:00:00Z",
        "state": "closed",
        "closed_at": "2025-11-02T10:00:00Z",
        "merged_at": None,
        "additions": 10,
        "deletions": 5,
    }

    pr2_data = {
        "number": 2,
        "title": "In Range",
        "user": {"login": "bob"},
        "created_at": "2025-12-15T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 20,
        "deletions": 10,
    }

    pr3_data = {
        "number": 3,
        "title": "Too New",
        "user": {"login": "charlie"},
        "created_at": "2026-02-01T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 30,
        "deletions": 15,
    }

    client = FakeGitHubClient(pull_requests=[pr1_data, pr2_data, pr3_data])

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    # Filter to get PRs between 2025-12-01 and 2026-01-31
    options = RunOptions(
        config=config,
        since=datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc),
        until=datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 1
    assert prs[0].number == 2
    assert prs[0].title == "In Range"


def test_collect_prs_from_multiple_repositories():
    """Test collecting PRs from multiple repositories."""
    pr1_data = {
        "number": 1,
        "title": "PR from repo1",
        "user": {"login": "alice"},
        "created_at": "2026-01-01T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 10,
        "deletions": 5,
    }

    pr2_data = {
        "number": 2,
        "title": "PR from repo2",
        "user": {"login": "bob"},
        "created_at": "2026-01-02T10:00:00Z",
        "state": "open",
        "closed_at": None,
        "merged_at": None,
        "additions": 20,
        "deletions": 10,
    }

    # We'll use a client that returns different PRs based on repo
    # For simplicity, we'll just return all PRs for both repos
    client = FakeGitHubClient(pull_requests=[pr1_data, pr2_data])

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo1", "owner/repo2"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["owner/repo1", "owner/repo2"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    # We should get PRs from both repositories
    # In this simple fake client, we'll get the same PRs twice
    assert len(prs) == 4  # 2 repos × 2 PRs each


def test_collect_prs_handles_empty_repository_list():
    """Test that collecting from no repositories returns empty list."""
    client = FakeGitHubClient()

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=[],  # Empty after CLI filtering
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 0


def test_collect_prs_handles_no_prs_in_repository():
    """Test that collecting from a repo with no PRs returns empty list."""
    client = FakeGitHubClient(pull_requests=[])

    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["owner/repo"],
        users=[],
        output="output.md",
        max_workers=1,
    )

    prs = collect_prs(config, options, client)

    assert len(prs) == 0
