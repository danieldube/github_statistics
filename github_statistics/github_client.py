"""GitHub API client abstraction."""

import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


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


class HttpGitHubClient(GitHubClient):
    """HTTP-based GitHub client that makes real API calls.

    This implementation uses the requests library to interact with
    GitHub's REST API. All network calls can be mocked in tests using
    libraries like responses or requests-mock.
    """

    def __init__(self, base_url: str, token: str, verify_ssl: bool = True):
        """Initialize HTTP GitHub client.

        Args:
            base_url: GitHub API base URL (e.g., https://api.github.com
                     or https://github.enterprise.com/api/v3).
            token: GitHub personal access token or OAuth token.
            verify_ssl: Whether to verify SSL certificates (default: True).
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }
        )

    @classmethod
    def from_env(
        cls, base_url: str, token_env: str, verify_ssl: bool = True
    ) -> "HttpGitHubClient":
        """Create client with token from environment variable.

        Args:
            base_url: GitHub API base URL.
            token_env: Name of environment variable containing the token.
            verify_ssl: Whether to verify SSL certificates.

        Returns:
            HttpGitHubClient instance.

        Raises:
            ValueError: If the environment variable is not set.
        """
        token = os.environ.get(token_env)
        if not token:
            raise ValueError(
                f"Environment variable '{token_env}' is not set. "
                f"Please set it to your GitHub token."
            )
        return cls(base_url=base_url, token=token, verify_ssl=verify_ssl)

    def _get_paginated(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all pages of a paginated endpoint.

        Args:
            url: Initial URL to fetch.
            headers: Optional additional headers.

        Returns:
            Combined list of all items from all pages.

        Raises:
            requests.HTTPError: If the request fails.
        """
        results = []
        current_url: Optional[str] = url

        while current_url:
            response = self.session.get(
                current_url, headers=headers, verify=self.verify_ssl
            )
            response.raise_for_status()

            data = response.json()
            if isinstance(data, list):
                results.extend(data)
            else:
                # Single object response
                return [data]

            # Check for next page in Link header
            link_header = response.headers.get("Link", "")
            current_url = self._parse_next_link(link_header)

        return results

    def _parse_next_link(self, link_header: str) -> Optional[str]:
        """Parse the 'next' URL from a Link header.

        Args:
            link_header: Value of the Link header.

        Returns:
            URL of the next page, or None if there is no next page.
        """
        if not link_header:
            return None

        # Link header format: <url>; rel="next", <url>; rel="last"
        links = link_header.split(",")
        for link in links:
            match = re.match(r'<([^>]+)>;\s*rel="next"', link.strip())
            if match:
                return match.group(1)

        return None

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
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls?state=all&per_page=100"
        prs = self._get_paginated(url)

        # Apply client-side date filtering if needed
        if since or until:
            filtered_prs = []
            for pr in prs:
                created_at_str = pr.get("created_at", "")
                if created_at_str:
                    created_at = datetime.fromisoformat(
                        created_at_str.replace("Z", "+00:00")
                    )

                    if since and created_at < since:
                        continue

                    if until and created_at > until:
                        continue

                    filtered_prs.append(pr)
            return filtered_prs

        return prs

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
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}"
        response = self.session.get(url, verify=self.verify_ssl)
        response.raise_for_status()
        result: Dict[str, Any] = response.json()
        return result

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
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}/files?per_page=100"
        return self._get_paginated(url)

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
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}/commits?per_page=100"
        return self._get_paginated(url)

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
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}/reviews?per_page=100"
        return self._get_paginated(url)

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
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{number}/comments?per_page=100"
        return self._get_paginated(url)

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
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{number}/comments?per_page=100"
        return self._get_paginated(url)

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
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{number}/timeline?per_page=100"

        # Timeline requires a special media type accept header
        headers = {"Accept": "application/vnd.github.mockingbird-preview+json"}

        return self._get_paginated(url, headers=headers)
