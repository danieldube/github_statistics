"""Data models for pull requests, reviews, commits, comments, and events."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class CommitInfo:
    """Information about a commit in a pull request.

    Attributes:
        sha: The commit SHA hash.
        author: The commit author username.
        committed_at: When the commit was made (UTC).
        message: The commit message.
    """

    sha: str
    author: str
    committed_at: datetime
    message: str


@dataclass
class CommentInfo:
    """Information about a comment on a pull request.

    Attributes:
        author: The comment author username.
        created_at: When the comment was created (UTC).
        body: The comment text.
    """

    author: str
    created_at: datetime
    body: str


@dataclass
class ReviewEvent:
    """A review event on a pull request.

    Attributes:
        reviewer: The reviewer username.
        submitted_at: When the review was submitted (UTC).
        state: The review state (APPROVED, CHANGES_REQUESTED, etc.).
    """

    reviewer: str
    submitted_at: datetime
    state: str


@dataclass
class ReviewRequestEvent:
    """A review request event on a pull request.

    Attributes:
        requested_reviewer: The username of the requested reviewer.
        requested_at: When the review was requested (UTC).
    """

    requested_reviewer: str
    requested_at: datetime


@dataclass
class ReadyForReviewEvent:
    """Event indicating a PR transitioned to ready-for-review state.

    Attributes:
        ready_at: When the PR became ready for review (UTC).
    """

    ready_at: datetime


@dataclass
class PullRequest:
    """A GitHub pull request with all associated data.

    All timestamps are assumed to be UTC datetime objects.

    Attributes:
        number: The PR number.
        title: The PR title.
        author: The PR author username.
        created_at: When the PR was created (UTC).
        state: The PR state (open, closed, merged).
        additions: Number of lines added.
        deletions: Number of lines deleted.
        closed_at: When the PR was closed (UTC), if applicable.
        merged_at: When the PR was merged (UTC), if applicable.
        commits: List of commits in this PR.
        comments: List of comments on this PR.
        reviews: List of review events on this PR.
        review_requests: List of review request events.
        ready_for_review_at: Ready-for-review event, if applicable.
        repository: Repository identifier in owner/repo format.
    """

    number: int
    title: str
    author: str
    created_at: datetime
    state: str
    additions: int
    deletions: int
    closed_at: Optional[datetime] = None
    merged_at: Optional[datetime] = None
    commits: List[CommitInfo] = field(default_factory=list)
    comments: List[CommentInfo] = field(default_factory=list)
    reviews: List[ReviewEvent] = field(default_factory=list)
    review_requests: List[ReviewRequestEvent] = field(default_factory=list)
    ready_for_review_at: Optional[ReadyForReviewEvent] = None
    repository: str = ""
