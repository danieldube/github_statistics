"""
Tests for HTTP GitHub client implementation with mocked responses.
"""

import os

import pytest
import responses

from github_statistics.github_client import HttpGitHubClient


@responses.activate
def test_http_client_list_pull_requests():
    """Test that list_pull_requests makes correct API call."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[
            {
                "number": 1,
                "title": "Test PR",
                "state": "open",
                "user": {"login": "testuser"},
                "created_at": "2024-01-01T10:00:00Z",
            }
        ],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    prs = client.list_pull_requests("owner", "repo")

    assert len(prs) == 1
    assert prs[0]["number"] == 1
    assert prs[0]["title"] == "Test PR"

    # Verify the request was made with correct parameters
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url.startswith(
        "https://api.github.com/repos/owner/repo/pulls"
    )


@responses.activate
def test_http_client_uses_token():
    """Test that the client sends the authorization token."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="my-secret-token",
        verify_ssl=True,
    )

    client.list_pull_requests("owner", "repo")

    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.headers["Authorization"]
        == "token my-secret-token"
    )


@responses.activate
def test_http_client_list_prs_with_state_all():
    """Test that list_pull_requests requests all states."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    client.list_pull_requests("owner", "repo")

    # Check that state=all is included
    assert "state=all" in responses.calls[0].request.url


@responses.activate
def test_http_client_pagination():
    """Test that the client handles pagination correctly."""
    # First page with Link header
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[{"number": 1}, {"number": 2}],
        status=200,
        headers={
            "Link": '<https://api.github.com/repos/owner/repo/pulls?page=2>; rel="next"'
        },
    )

    # Second page (no next link)
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[{"number": 3}],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    prs = client.list_pull_requests("owner", "repo")

    # Should have fetched all pages
    assert len(prs) == 3
    assert prs[0]["number"] == 1
    assert prs[1]["number"] == 2
    assert prs[2]["number"] == 3
    assert len(responses.calls) == 2


@responses.activate
def test_http_client_get_pull_request_details():
    """Test fetching PR details."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls/42",
        json={
            "number": 42,
            "title": "Detailed PR",
            "state": "closed",
            "merged_at": "2024-01-15T10:00:00Z",
            "additions": 100,
            "deletions": 20,
        },
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    details = client.get_pull_request_details("owner", "repo", 42)

    assert details["number"] == 42
    assert details["title"] == "Detailed PR"
    assert details["state"] == "closed"
    assert details["additions"] == 100
    assert len(responses.calls) == 1


@responses.activate
def test_http_client_get_pull_request_files():
    """Test fetching PR files."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls/1/files",
        json=[
            {
                "filename": "README.md",
                "additions": 10,
                "deletions": 5,
                "changes": 15,
            }
        ],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    files = client.get_pull_request_files("owner", "repo", 1)

    assert len(files) == 1
    assert files[0]["filename"] == "README.md"
    assert files[0]["additions"] == 10


@responses.activate
def test_http_client_get_pull_request_commits():
    """Test fetching PR commits."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls/1/commits",
        json=[
            {
                "sha": "abc123",
                "commit": {
                    "author": {
                        "name": "alice",
                        "date": "2024-01-01T10:00:00Z",
                    },
                    "message": "Initial commit",
                },
            }
        ],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    commits = client.get_pull_request_commits("owner", "repo", 1)

    assert len(commits) == 1
    assert commits[0]["sha"] == "abc123"


@responses.activate
def test_http_client_get_pull_request_reviews():
    """Test fetching PR reviews."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls/1/reviews",
        json=[
            {
                "user": {"login": "reviewer1"},
                "state": "APPROVED",
                "submitted_at": "2024-01-02T10:00:00Z",
            }
        ],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    reviews = client.get_pull_request_reviews("owner", "repo", 1)

    assert len(reviews) == 1
    assert reviews[0]["user"]["login"] == "reviewer1"
    assert reviews[0]["state"] == "APPROVED"


@responses.activate
def test_http_client_get_review_comments():
    """Test fetching PR review comments."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls/1/comments",
        json=[
            {
                "user": {"login": "reviewer1"},
                "body": "Please fix this",
                "created_at": "2024-01-02T10:00:00Z",
            }
        ],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    comments = client.get_pull_request_review_comments("owner", "repo", 1)

    assert len(comments) == 1
    assert comments[0]["body"] == "Please fix this"


@responses.activate
def test_http_client_get_issue_comments():
    """Test fetching issue comments."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/issues/1/comments",
        json=[
            {
                "user": {"login": "commenter"},
                "body": "Looks good!",
                "created_at": "2024-01-03T10:00:00Z",
            }
        ],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    comments = client.get_issue_comments("owner", "repo", 1)

    assert len(comments) == 1
    assert comments[0]["body"] == "Looks good!"


@responses.activate
def test_http_client_get_timeline():
    """Test fetching issue timeline with correct media type."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/issues/1/timeline",
        json=[
            {
                "event": "review_requested",
                "created_at": "2024-01-01T10:00:00Z",
            }
        ],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    timeline = client.get_issue_timeline("owner", "repo", 1)

    assert len(timeline) == 1
    assert timeline[0]["event"] == "review_requested"

    # Verify correct Accept header for timeline
    assert len(responses.calls) == 1
    accept_header = responses.calls[0].request.headers.get("Accept", "")
    assert "application/vnd.github.mockingbird-preview+json" in accept_header


@responses.activate
def test_http_client_custom_base_url():
    """Test that custom base URLs are used correctly."""
    responses.add(
        responses.GET,
        "https://github.enterprise.com/api/v3/repos/owner/repo/pulls",
        json=[],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://github.enterprise.com/api/v3",
        token="test-token",
        verify_ssl=True,
    )

    client.list_pull_requests("owner", "repo")

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url.startswith(
        "https://github.enterprise.com/api/v3"
    )


@responses.activate
def test_http_client_error_404():
    """Test that 404 errors are handled appropriately."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls/999",
        json={"message": "Not Found"},
        status=404,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    with pytest.raises(Exception) as exc_info:
        client.get_pull_request_details("owner", "repo", 999)

    # Should raise an exception with meaningful error
    assert "404" in str(exc_info.value) or "Not Found" in str(exc_info.value)


@responses.activate
def test_http_client_error_403_rate_limit():
    """Test that 403 rate limit errors are handled."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json={"message": "API rate limit exceeded"},
        status=403,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    with pytest.raises(Exception) as exc_info:
        client.list_pull_requests("owner", "repo")

    # Should raise an exception with rate limit info
    assert (
        "403" in str(exc_info.value)
        or "rate limit" in str(exc_info.value).lower()
    )


@responses.activate
def test_http_client_error_500():
    """Test that 500 server errors are handled."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json={"message": "Internal Server Error"},
        status=500,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    with pytest.raises(Exception) as exc_info:
        client.list_pull_requests("owner", "repo")

    assert "500" in str(exc_info.value)


@responses.activate
def test_http_client_pagination_with_files():
    """Test pagination for file listings (can be large)."""
    # First page
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls/1/files",
        json=[{"filename": f"file{i}.py"} for i in range(30)],
        status=200,
        headers={
            "Link": '<https://api.github.com/repos/owner/repo/pulls/1/files?page=2>; rel="next"'
        },
    )

    # Second page
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls/1/files",
        json=[{"filename": f"file{i}.py"} for i in range(30, 40)],
        status=200,
    )

    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )

    files = client.get_pull_request_files("owner", "repo", 1)

    # Should fetch all files across pages
    assert len(files) == 40
    assert len(responses.calls) == 2


@responses.activate
def test_http_client_from_env_token():
    """Test creating client with token from environment variable."""
    # Set up environment variable
    os.environ["TEST_GITHUB_TOKEN"] = "env-token-123"

    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[],
        status=200,
    )

    try:
        client = HttpGitHubClient.from_env(
            base_url="https://api.github.com",
            token_env="TEST_GITHUB_TOKEN",
            verify_ssl=True,
        )

        client.list_pull_requests("owner", "repo")

        # Verify token from env was used
        assert len(responses.calls) == 1
        assert (
            responses.calls[0].request.headers["Authorization"]
            == "token env-token-123"
        )
    finally:
        # Clean up
        del os.environ["TEST_GITHUB_TOKEN"]


def test_http_client_from_env_missing_token():
    """Test that missing env token raises clear error."""
    with pytest.raises(ValueError) as exc_info:
        HttpGitHubClient.from_env(
            base_url="https://api.github.com",
            token_env="NONEXISTENT_TOKEN_VAR",
            verify_ssl=True,
        )

    assert "NONEXISTENT_TOKEN_VAR" in str(exc_info.value)
    assert "not set" in str(exc_info.value).lower()


@responses.activate
def test_http_client_from_token_or_env_prefers_direct_token():
    """Test direct config token is used when provided."""
    os.environ["TEST_GITHUB_TOKEN"] = "env-token-123"

    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[],
        status=200,
    )

    try:
        client = HttpGitHubClient.from_token_or_env(
            base_url="https://api.github.com",
            api_token="config-token-789",
            token_env="TEST_GITHUB_TOKEN",
            verify_ssl=True,
        )

        client.list_pull_requests("owner", "repo")

        assert len(responses.calls) == 1
        assert (
            responses.calls[0].request.headers["Authorization"]
            == "token config-token-789"
        )
    finally:
        del os.environ["TEST_GITHUB_TOKEN"]


def test_http_client_from_token_or_env_uses_env_fallback():
    """Test env fallback is used when direct config token is missing."""
    os.environ["TEST_GITHUB_TOKEN"] = "env-token-123"

    try:
        client = HttpGitHubClient.from_token_or_env(
            base_url="https://api.github.com",
            api_token=None,
            token_env="TEST_GITHUB_TOKEN",
            verify_ssl=True,
        )

        assert client.token == "env-token-123"
    finally:
        del os.environ["TEST_GITHUB_TOKEN"]


def test_http_client_from_token_or_env_uses_default_env_name():
    """Test fallback uses GITHUB_TOKEN when token_env is not provided."""
    os.environ["GITHUB_TOKEN"] = "default-env-token"

    try:
        client = HttpGitHubClient.from_token_or_env(
            base_url="https://api.github.com",
            api_token=None,
            token_env=None,
            verify_ssl=True,
        )

        assert client.token == "default-env-token"
    finally:
        del os.environ["GITHUB_TOKEN"]


def test_http_client_verify_ssl_false():
    """Test that verify_ssl=False is respected."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[],
        status=200,
    )

    # This mainly tests that the parameter is accepted
    # The actual SSL verification behavior is handled by requests library
    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=False,
    )

    # Should not raise an error
    prs = client.list_pull_requests("owner", "repo")
    assert isinstance(prs, list)


def test_http_client_rejects_invalid_github_com_base_url():
    """Test that client rejects incorrect base_url for public GitHub."""
    with pytest.raises(ValueError) as exc_info:
        HttpGitHubClient(
            base_url="https://github.com/api/v3",
            token="test-token",
            verify_ssl=True,
        )

    assert "Invalid base_url" in str(exc_info.value)
    assert "https://api.github.com" in str(exc_info.value)
    assert "For public GitHub" in str(exc_info.value)


def test_http_client_accepts_correct_base_urls():
    """Test that client accepts valid base URLs."""
    # Public GitHub
    client1 = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
    )
    assert client1.base_url == "https://api.github.com"

    # GitHub Enterprise (correct format)
    client2 = HttpGitHubClient(
        base_url="https://github.mycompany.com/api/v3",
        token="test-token",
        verify_ssl=True,
    )
    assert client2.base_url == "https://github.mycompany.com/api/v3"
