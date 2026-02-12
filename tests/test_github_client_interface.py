"""
Tests for GitHub client interface (no real network calls).
"""

from datetime import datetime, timezone

from github_statistics.github_client import FakeGitHubClient, GitHubClient


def test_fake_client_is_github_client():
    """Test that FakeGitHubClient inherits from GitHubClient."""
    client = FakeGitHubClient()
    assert isinstance(client, GitHubClient)


def test_list_pull_requests_basic():
    """Test list_pull_requests returns a list of PR data."""
    client = FakeGitHubClient()
    prs = client.list_pull_requests("owner", "repo")

    assert isinstance(prs, list)
    # Fake client should return at least some PRs
    assert len(prs) >= 0


def test_list_pull_requests_with_date_filters():
    """Test list_pull_requests accepts since and until parameters."""
    client = FakeGitHubClient()
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    until = datetime(2024, 12, 31, tzinfo=timezone.utc)

    prs = client.list_pull_requests("owner", "repo", since=since, until=until)

    assert isinstance(prs, list)


def test_get_pull_request_details():
    """Test get_pull_request_details returns PR details dict."""
    test_prs = [
        {
            "number": 1,
            "title": "Test PR",
            "state": "open",
            "user": {"login": "testuser"},
            "created_at": "2024-01-01T10:00:00Z",
            "additions": 10,
            "deletions": 5,
        }
    ]
    client = FakeGitHubClient(pull_requests=test_prs)
    details = client.get_pull_request_details("owner", "repo", 1)

    assert isinstance(details, dict)
    # Should have basic PR fields
    assert "number" in details
    assert "title" in details
    assert "state" in details


def test_get_pull_request_files():
    """Test get_pull_request_files returns list of file dicts."""
    client = FakeGitHubClient()
    files = client.get_pull_request_files("owner", "repo", 1)

    assert isinstance(files, list)


def test_get_pull_request_commits():
    """Test get_pull_request_commits returns list of commit dicts."""
    client = FakeGitHubClient()
    commits = client.get_pull_request_commits("owner", "repo", 1)

    assert isinstance(commits, list)


def test_get_pull_request_reviews():
    """Test get_pull_request_reviews returns list of review dicts."""
    client = FakeGitHubClient()
    reviews = client.get_pull_request_reviews("owner", "repo", 1)

    assert isinstance(reviews, list)


def test_get_pull_request_review_comments():
    """Test get_pull_request_review_comments returns list of comments."""
    client = FakeGitHubClient()
    comments = client.get_pull_request_review_comments("owner", "repo", 1)

    assert isinstance(comments, list)


def test_get_issue_comments():
    """Test get_issue_comments returns list of comment dicts."""
    client = FakeGitHubClient()
    comments = client.get_issue_comments("owner", "repo", 1)

    assert isinstance(comments, list)


def test_get_issue_timeline():
    """Test get_issue_timeline returns list of timeline event dicts."""
    client = FakeGitHubClient()
    events = client.get_issue_timeline("owner", "repo", 1)

    assert isinstance(events, list)


def test_fake_client_with_prepopulated_data():
    """Test FakeGitHubClient can be initialized with test data."""
    test_prs = [
        {
            "number": 1,
            "title": "Test PR 1",
            "state": "open",
            "user": {"login": "testuser"},
            "created_at": "2024-01-01T10:00:00Z",
            "additions": 10,
            "deletions": 5,
        },
        {
            "number": 2,
            "title": "Test PR 2",
            "state": "closed",
            "user": {"login": "testuser2"},
            "created_at": "2024-01-02T10:00:00Z",
            "additions": 20,
            "deletions": 10,
        },
    ]

    client = FakeGitHubClient(pull_requests=test_prs)
    prs = client.list_pull_requests("owner", "repo")

    assert len(prs) == 2
    assert prs[0]["number"] == 1
    assert prs[1]["number"] == 2


def test_fake_client_returns_specific_pr_details():
    """Test that get_pull_request_details returns the right PR."""
    test_prs = [
        {
            "number": 1,
            "title": "First PR",
            "state": "open",
            "user": {"login": "dev1"},
            "created_at": "2024-01-01T10:00:00Z",
            "additions": 10,
            "deletions": 5,
        },
        {
            "number": 2,
            "title": "Second PR",
            "state": "closed",
            "user": {"login": "dev2"},
            "created_at": "2024-01-02T10:00:00Z",
            "additions": 20,
            "deletions": 10,
        },
    ]

    client = FakeGitHubClient(pull_requests=test_prs)

    pr1 = client.get_pull_request_details("owner", "repo", 1)
    assert pr1["number"] == 1
    assert pr1["title"] == "First PR"

    pr2 = client.get_pull_request_details("owner", "repo", 2)
    assert pr2["number"] == 2
    assert pr2["title"] == "Second PR"


def test_fake_client_date_filtering():
    """Test that date filtering works in list_pull_requests."""
    test_prs = [
        {
            "number": 1,
            "title": "Old PR",
            "state": "closed",
            "user": {"login": "dev1"},
            "created_at": "2023-12-01T10:00:00Z",
            "additions": 10,
            "deletions": 5,
        },
        {
            "number": 2,
            "title": "New PR",
            "state": "open",
            "user": {"login": "dev2"},
            "created_at": "2024-01-15T10:00:00Z",
            "additions": 20,
            "deletions": 10,
        },
    ]

    client = FakeGitHubClient(pull_requests=test_prs)

    # Filter for PRs since 2024-01-01
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    filtered_prs = client.list_pull_requests("owner", "repo", since=since)

    # Should only get PR #2
    assert len(filtered_prs) == 1
    assert filtered_prs[0]["number"] == 2


def test_fake_client_until_filtering():
    """Test that until filtering works in list_pull_requests."""
    test_prs = [
        {
            "number": 1,
            "title": "Early PR",
            "state": "closed",
            "user": {"login": "dev1"},
            "created_at": "2024-01-05T10:00:00Z",
            "additions": 10,
            "deletions": 5,
        },
        {
            "number": 2,
            "title": "Late PR",
            "state": "open",
            "user": {"login": "dev2"},
            "created_at": "2024-02-15T10:00:00Z",
            "additions": 20,
            "deletions": 10,
        },
    ]

    client = FakeGitHubClient(pull_requests=test_prs)

    # Filter for PRs until 2024-01-31
    until = datetime(2024, 1, 31, tzinfo=timezone.utc)
    filtered_prs = client.list_pull_requests("owner", "repo", until=until)

    # Should only get PR #1
    assert len(filtered_prs) == 1
    assert filtered_prs[0]["number"] == 1


def test_fake_client_since_and_until_filtering():
    """Test that both since and until filters work together."""
    test_prs = [
        {
            "number": 1,
            "created_at": "2023-12-15T10:00:00Z",
            "title": "Before range",
            "state": "closed",
            "user": {"login": "dev1"},
            "additions": 10,
            "deletions": 5,
        },
        {
            "number": 2,
            "created_at": "2024-01-15T10:00:00Z",
            "title": "In range",
            "state": "open",
            "user": {"login": "dev2"},
            "additions": 20,
            "deletions": 10,
        },
        {
            "number": 3,
            "created_at": "2024-02-15T10:00:00Z",
            "title": "After range",
            "state": "open",
            "user": {"login": "dev3"},
            "additions": 30,
            "deletions": 15,
        },
    ]

    client = FakeGitHubClient(pull_requests=test_prs)

    # Filter for January 2024
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    until = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
    filtered_prs = client.list_pull_requests(
        "owner", "repo", since=since, until=until
    )

    # Should only get PR #2
    assert len(filtered_prs) == 1
    assert filtered_prs[0]["number"] == 2


def test_fake_client_supports_multiple_repos():
    """Test that FakeGitHubClient can handle different repos."""
    client = FakeGitHubClient()

    # Should work with different owner/repo combinations
    prs1 = client.list_pull_requests("owner1", "repo1")
    prs2 = client.list_pull_requests("owner2", "repo2")

    assert isinstance(prs1, list)
    assert isinstance(prs2, list)


def test_interface_methods_have_proper_signatures():
    """Test that GitHubClient defines expected method signatures."""
    # This tests that the base class has the right methods
    assert hasattr(GitHubClient, "list_pull_requests")
    assert hasattr(GitHubClient, "get_pull_request_details")
    assert hasattr(GitHubClient, "get_pull_request_files")
    assert hasattr(GitHubClient, "get_pull_request_commits")
    assert hasattr(GitHubClient, "get_pull_request_reviews")
    assert hasattr(GitHubClient, "get_pull_request_review_comments")
    assert hasattr(GitHubClient, "get_issue_comments")
    assert hasattr(GitHubClient, "get_issue_timeline")
