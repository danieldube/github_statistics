"""GitHub API client abstraction."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class GitHubClient(ABC):
    """Abstract base class for GitHub API clients.

    This defines the interface that all GitHub client implementations
    must follow. Implementations may fetch data from real GitHub APIs
    or provide fake/mock data for testing.
    """

    @abstractmethod
    def list_pull_requests(
        self,
        owner: str,
        repo: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """List pull requests for a repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            since: Only return PRs created after this date (UTC).
            until: Only return PRs created before this date (UTC).

        Returns:
            List of pull request dictionaries.
        """
        pass

    @abstractmethod
    def get_pull_request_details(
        self, owner: str, repo: str, number: int
    ) -> Dict[str, Any]:
        """Get detailed information about a specific pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.

        Returns:
            Dictionary with PR details.
        """
        pass

    @abstractmethod
    def get_pull_request_files(
        self, owner: str, repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get list of files changed in a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.

        Returns:
            List of file dictionaries with changes.
        """
        pass

    @abstractmethod
    def get_pull_request_commits(
        self, owner: str, repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get list of commits in a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.

        Returns:
            List of commit dictionaries.
        """
        pass

    @abstractmethod
    def get_pull_request_reviews(
        self, owner: str, repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get list of reviews for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.

        Returns:
            List of review dictionaries.
        """
        pass

    @abstractmethod
    def get_pull_request_review_comments(
        self, owner: str, repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get review comments (code comments) for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request number.

        Returns:
            List of review comment dictionaries.
        """
        pass

    @abstractmethod
    def get_issue_comments(
        self, owner: str, repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get issue comments (general comments) for a pull request.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request/issue number.

        Returns:
            List of issue comment dictionaries.
        """
        pass

    @abstractmethod
    def get_issue_timeline(
        self, owner: str, repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get timeline events for a pull request/issue.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Pull request/issue number.

        Returns:
            List of timeline event dictionaries.
        """
        pass


class FakeGitHubClient(GitHubClient):
    """Fake GitHub client for testing.

    This implementation doesn't make real HTTP calls but instead
    returns pre-configured or synthetic data for testing purposes.
    """

    def __init__(
        self,
        pull_requests: Optional[List[Dict[str, Any]]] = None,
        commits: Optional[Dict[int, List[Dict[str, Any]]]] = None,
        files: Optional[Dict[int, List[Dict[str, Any]]]] = None,
        reviews: Optional[Dict[int, List[Dict[str, Any]]]] = None,
        review_comments: Optional[Dict[int, List[Dict[str, Any]]]] = None,
        issue_comments: Optional[Dict[int, List[Dict[str, Any]]]] = None,
        timeline_events: Optional[Dict[int, List[Dict[str, Any]]]] = None,
    ):
        """Initialize fake client with optional test data.

        Args:
            pull_requests: List of PR dicts to return.
            commits: Dict mapping PR number to list of commit dicts.
            files: Dict mapping PR number to list of file dicts.
            reviews: Dict mapping PR number to list of review dicts.
            review_comments: Dict mapping PR number to review comments.
            issue_comments: Dict mapping PR number to issue comments.
            timeline_events: Dict mapping PR number to timeline events.
        """
        self.pull_requests = pull_requests or []
        self.commits = commits or {}
        self.files = files or {}
        self.reviews = reviews or {}
        self.review_comments = review_comments or {}
        self.issue_comments = issue_comments or {}
        self.timeline_events = timeline_events or {}

    def list_pull_requests(
        self,
        _owner: str,
        _repo: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """List pull requests with optional date filtering."""
        prs = self.pull_requests

        # Apply date filtering if requested
        if since or until:
            filtered_prs = []
            for pr in prs:
                # Parse the created_at timestamp
                created_at_str = pr.get("created_at", "")
                if created_at_str:
                    # Parse ISO format datetime
                    created_at = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )

                    # Check since filter
                    if since and created_at < since:
                        continue

                    # Check until filter
                    if until and created_at > until:
                        continue

                    filtered_prs.append(pr)
            return filtered_prs

        return prs

    def get_pull_request_details(
        self, _owner: str, _repo: str, number: int
    ) -> Dict[str, Any]:
        """Get details for a specific PR."""
        # Find PR by number
        for pr in self.pull_requests:
            if pr.get("number") == number:
                return pr

        # Return empty dict if not found
        return {}

    def get_pull_request_files(
        self, _owner: str, _repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get files for a specific PR."""
        return self.files.get(number, [])

    def get_pull_request_commits(
        self, _owner: str, _repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get commits for a specific PR."""
        return self.commits.get(number, [])

    def get_pull_request_reviews(
        self, _owner: str, _repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get reviews for a specific PR."""
        return self.reviews.get(number, [])

    def get_pull_request_review_comments(
        self, _owner: str, _repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get review comments for a specific PR."""
        return self.review_comments.get(number, [])

    def get_issue_comments(
        self, _owner: str, _repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get issue comments for a specific PR."""
        return self.issue_comments.get(number, [])

    def get_issue_timeline(
        self, _owner: str, _repo: str, number: int
    ) -> List[Dict[str, Any]]:
        """Get timeline events for a specific PR."""
        return self.timeline_events.get(number, [])
