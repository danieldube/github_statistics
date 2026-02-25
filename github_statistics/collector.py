"""
Data collection logic - assembling complete PR objects from the GitHub client.
"""

from datetime import datetime
from typing import List

from github_statistics.models import (
    CommentInfo,
    CommitInfo,
    PullRequest,
    ReadyForReviewEvent,
    ReviewEvent,
    ReviewRequestEvent,
)


def _parse_iso_datetime(dt_string: str) -> datetime:
    """Parse ISO format datetime string to datetime object.

    Args:
        dt_string: ISO format datetime string (e.g., '2026-01-01T10:00:00Z').

    Returns:
        Timezone-aware datetime object (UTC).
    """
    # Replace 'Z' suffix with '+00:00' for proper parsing
    if dt_string.endswith("Z"):
        dt_string = dt_string[:-1] + "+00:00"
    return datetime.fromisoformat(dt_string)


def _assemble_pull_request(
    pr_data: dict, client, owner: str, repo: str
) -> PullRequest:
    """Assemble a complete PullRequest object from API data.

    Args:
        pr_data: Basic PR data from list_pull_requests.
        client: GitHub client instance.
        owner: Repository owner.
        repo: Repository name.

    Returns:
        Complete PullRequest object with all associated data.
    """
    number = pr_data["number"]

    # Parse basic PR information
    title = pr_data["title"]
    author = pr_data["user"]["login"]
    created_at = _parse_iso_datetime(pr_data["created_at"])
    state = pr_data["state"]

    # Fetch PR details to get additions/deletions (not in list response)
    pr_details = client.get_pull_request_details(owner, repo, number)
    additions = pr_details.get("additions", 0)
    deletions = pr_details.get("deletions", 0)

    # Parse optional dates
    closed_at = None
    if pr_data.get("closed_at"):
        closed_at = _parse_iso_datetime(pr_data["closed_at"])

    merged_at = None
    if pr_data.get("merged_at"):
        merged_at = _parse_iso_datetime(pr_data["merged_at"])

    # Fetch commits
    commits_data = client.get_pull_request_commits(owner, repo, number)
    commits = []
    for commit_data in commits_data:
        commit_info = CommitInfo(
            sha=commit_data["sha"],
            author=commit_data["commit"]["author"]["name"],
            committed_at=_parse_iso_datetime(
                commit_data["commit"]["author"]["date"]
            ),
            message=commit_data["commit"]["message"],
        )
        commits.append(commit_info)

    # Fetch comments (both issue comments and review comments)
    comments = []

    # Issue comments (general comments on the PR)
    issue_comments_data = client.get_issue_comments(owner, repo, number)
    for comment_data in issue_comments_data:
        comment_info = CommentInfo(
            author=comment_data["user"]["login"],
            created_at=_parse_iso_datetime(comment_data["created_at"]),
            body=comment_data["body"],
        )
        comments.append(comment_info)

    # Review comments (code-specific comments)
    review_comments_data = client.get_pull_request_review_comments(
        owner, repo, number
    )
    for comment_data in review_comments_data:
        comment_info = CommentInfo(
            author=comment_data["user"]["login"],
            created_at=_parse_iso_datetime(comment_data["created_at"]),
            body=comment_data["body"],
        )
        comments.append(comment_info)

    # Sort comments by created_at
    comments.sort(key=lambda c: c.created_at)

    # Fetch reviews
    reviews_data = client.get_pull_request_reviews(owner, repo, number)
    reviews = []
    for review_data in reviews_data:
        submitted_at_raw = review_data.get("submitted_at")
        if not submitted_at_raw:
            # Skip reviews without submitted_at (e.g. PENDING or draft reviews)
            continue
        review_event = ReviewEvent(
            reviewer=review_data["user"]["login"],
            submitted_at=_parse_iso_datetime(submitted_at_raw),
            state=review_data["state"],
        )
        reviews.append(review_event)

    # Fetch timeline events for review requests and ready-for-review
    timeline_data = client.get_issue_timeline(owner, repo, number)
    review_requests = []
    ready_for_review_at = None

    for event_data in timeline_data:
        event_type = event_data.get("event")

        if (
            event_type == "review_requested"
            and "requested_reviewer" in event_data
        ):
            # Extract requested reviewer
            requested_reviewer = event_data["requested_reviewer"]["login"]
            requested_at = _parse_iso_datetime(event_data["created_at"])
            review_request = ReviewRequestEvent(
                requested_reviewer=requested_reviewer,
                requested_at=requested_at,
            )
            review_requests.append(review_request)

        elif event_type == "ready_for_review":
            # Only take the first/earliest ready_for_review event
            if ready_for_review_at is None:
                ready_at = _parse_iso_datetime(event_data["created_at"])
                ready_for_review_at = ReadyForReviewEvent(ready_at=ready_at)

    # Assemble the complete PullRequest object
    return PullRequest(
        number=number,
        title=title,
        author=author,
        created_at=created_at,
        state=state,
        additions=additions,
        deletions=deletions,
        closed_at=closed_at,
        merged_at=merged_at,
        commits=commits,
        comments=comments,
        reviews=reviews,
        review_requests=review_requests,
        ready_for_review_at=ready_for_review_at,
        repository=f"{owner}/{repo}",
    )


def collect_prs(_config, options, client) -> List[PullRequest]:
    """Collect pull requests from configured repositories.

    Args:
        _config: Configuration object (not currently used, but kept for interface consistency).
        options: Runtime options (filters, date ranges, repositories).
        client: GitHub client instance.

    Returns:
        List of PullRequest objects assembled from all configured repositories.
    """
    all_prs = []

    # Iterate through repositories
    for repo_identifier in options.repositories:
        # Parse owner/repo from identifier
        parts = repo_identifier.split("/")
        if len(parts) != 2:
            # Skip invalid repository identifiers
            continue

        owner, repo = parts

        # Fetch PRs from this repository with date filtering
        pr_list = client.list_pull_requests(
            owner, repo, since=options.since, until=options.until
        )

        # Assemble complete PR objects
        for pr_data in pr_list:
            pr = _assemble_pull_request(pr_data, client, owner, repo)
            all_prs.append(pr)

    return all_prs
