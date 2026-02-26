"""
Statistics computation - metrics and distributions.

This module computes statistical metrics from pull request data,
including both repository-level and user-level statistics.
Uses Python standard library (statistics, datetime) for calculations.
"""

import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

from github_statistics.models import PullRequest


@dataclass
class Distribution:
    """Statistical distribution of numeric values.

    Attributes:
        count: Number of values.
        minimum: Minimum value (0.0 if count is 0).
        maximum: Maximum value (0.0 if count is 0).
        mean: Mean (average) value (0.0 if count is 0).
        median: Median (middle) value (0.0 if count is 0).
    """

    count: int
    minimum: float
    maximum: float
    mean: float
    median: float


@dataclass
class RepositoryStats:
    """Repository-level statistics.

    Attributes:
        open_pr_duration: Duration (days) of open PRs.
        closed_pr_duration: Duration (days) of closed (not merged) PRs.
        merged_pr_duration: Duration (days) of merged PRs.
        time_to_first_review: Time (days) from PR creation to first review.
        commits_per_pr: Number of commits per PR.
        comments_per_100_loc: Number of comments per 100 lines of code.
        re_reviews_per_pr: Number of re-reviews per PR (reviews after first).
        time_between_changes_requested_and_re_request: Time (days) between
            CHANGES_REQUESTED review and next review request.
    """

    open_pr_duration: Distribution
    closed_pr_duration: Distribution
    merged_pr_duration: Distribution
    time_to_first_review: Distribution
    commits_per_pr: Distribution
    comments_per_100_loc: Distribution
    re_reviews_per_pr: Distribution
    time_between_changes_requested_and_re_request: Distribution


@dataclass
class UserStats:
    """User-level statistics.

    Attributes:
        time_to_submit_review: Time (hours) from review request to submission.
        changes_requested_rate: Percentage of reviews requesting changes.
        direct_approval_rate: Percentage of PRs approved directly.
        loc_per_created_pr: Lines of code per created PR (as author).
        comments_per_100_loc_as_reviewer: Comments per 100 LOC as reviewer.
        comments_per_100_loc_as_author: Comments per 100 LOC as PR author.
    """

    time_to_submit_review: Distribution
    changes_requested_rate: float
    direct_approval_rate: float
    loc_per_created_pr: Distribution
    comments_per_100_loc_as_reviewer: Distribution
    comments_per_100_loc_as_author: Distribution


@dataclass
class GroupStats:
    """Group-level statistics."""

    member_count: int
    active_member_count: int
    time_to_submit_review: Distribution
    changes_requested_rate: float
    direct_approval_rate: float
    loc_per_created_pr: Distribution
    comments_per_100_loc_as_reviewer: Distribution
    comments_per_100_loc_as_author: Distribution


@dataclass
class DataProtectionViolation:
    """Single data-protection violation."""

    violation_type: str
    scope: str
    active_count: int
    threshold: int
    message: str


@dataclass
class DataProtectionCheckResult:
    """Result of data-protection threshold checks."""

    passed: bool
    group_active_counts: Dict[str, int]
    repository_scope_active_count: int
    threshold: int
    violations: List[DataProtectionViolation]


def _compute_distribution(values: List[float]) -> Distribution:
    """Compute a distribution from a list of numeric values.

    Args:
        values: List of numeric values.

    Returns:
        Distribution object with statistics.
    """
    if not values:
        return Distribution(
            count=0, minimum=0.0, maximum=0.0, mean=0.0, median=0.0
        )

    return Distribution(
        count=len(values),
        minimum=min(values),
        maximum=max(values),
        mean=statistics.mean(values),
        median=statistics.median(values),
    )


def _days_between(start: datetime, end: datetime) -> float:
    """Calculate days between two datetimes.

    Args:
        start: Start datetime.
        end: End datetime.

    Returns:
        Number of days as a float.
    """
    delta = end - start
    return delta.total_seconds() / 86400.0  # seconds per day


def _hours_between(start: datetime, end: datetime) -> float:
    """Calculate hours between two datetimes.

    Args:
        start: Start datetime.
        end: End datetime.

    Returns:
        Number of hours as a float.
    """
    delta = end - start
    return delta.total_seconds() / 3600.0  # seconds per hour


def _is_in_period(
    dt: datetime, since: Optional[datetime], until: Optional[datetime]
) -> bool:
    """Check whether a datetime is in the inclusive [since, until] period."""
    if since and dt < since:
        return False
    return not (until and dt > until)


def get_active_users_in_period(
    pull_requests: List[PullRequest],
    since: Optional[datetime],
    until: Optional[datetime],
    repositories: Optional[List[str]] = None,
) -> Set[str]:
    """Return users with at least one commit in the selected period."""
    repo_filter = set(repositories) if repositories else None
    active_users: Set[str] = set()
    for pr in pull_requests:
        if repo_filter is not None and pr.repository not in repo_filter:
            continue
        for commit in pr.commits:
            if _is_in_period(commit.committed_at, since, until):
                active_users.add(commit.author)
    return active_users


def compute_active_group_counts(
    user_groups: Dict[str, List[str]], active_users: Set[str]
) -> Dict[str, int]:
    """Compute active-member counts per configured group."""
    counts: Dict[str, int] = {}
    for group_name, members in user_groups.items():
        member_set = set(members)
        counts[group_name] = len(member_set.intersection(active_users))
    return counts


def evaluate_data_protection_thresholds(
    pull_requests: List[PullRequest],
    user_groups: Dict[str, List[str]],
    repositories: List[str],
    since: Optional[datetime],
    until: Optional[datetime],
    threshold: int = 5,
) -> DataProtectionCheckResult:
    """Evaluate group and repository active-member thresholds."""
    active_users = get_active_users_in_period(
        pull_requests=pull_requests,
        since=since,
        until=until,
        repositories=repositories,
    )
    group_counts = compute_active_group_counts(user_groups, active_users)

    violations: List[DataProtectionViolation] = []
    for group_name, count in group_counts.items():
        if count < threshold:
            violations.append(
                DataProtectionViolation(
                    violation_type="group",
                    scope=group_name,
                    active_count=count,
                    threshold=threshold,
                    message=(
                        f"Group '{group_name}' has {count} active members, "
                        f"minimum required is {threshold}"
                    ),
                )
            )

    repo_scope_active_count = len(active_users)
    if repo_scope_active_count < threshold:
        violations.append(
            DataProtectionViolation(
                violation_type="repository_scope",
                scope="run_scope",
                active_count=repo_scope_active_count,
                threshold=threshold,
                message=(
                    f"Repository scope has {repo_scope_active_count} active "
                    f"members, minimum required is {threshold}"
                ),
            )
        )

    return DataProtectionCheckResult(
        passed=len(violations) == 0,
        group_active_counts=group_counts,
        repository_scope_active_count=repo_scope_active_count,
        threshold=threshold,
        violations=violations,
    )


def classify_commits_requested_vs_unrequested(
    pr: PullRequest,
) -> Tuple[int, int]:
    """Classify commits after ready-for-review as requested or unrequested.

    This is a heuristic metric that attempts to distinguish between:
    - Requested commits: Made in response to CHANGES_REQUESTED reviews
    - Unrequested commits: Made without being associated with review feedback

    The classification follows this state machine:
    1. Only commits after ready_for_review_at are considered
    2. Only commits by the PR author are counted
    3. A CHANGES_REQUESTED review opens a "requested cycle"
    4. A requested cycle is closed by:
       - A subsequent review request for the same reviewer
       - An APPROVED review from the same reviewer
    5. Commits during an open cycle are "requested"
    6. Commits outside any cycle are "unrequested"

    Limitations:
    - If ready_for_review_at is None, returns (0, 0)
    - Assumes review state transitions follow GitHub conventions
    - Cannot distinguish between fixing requested changes vs unrelated work
      during an open cycle

    Args:
        pr: PullRequest object with commits, reviews, and events.

    Returns:
        Tuple of (requested_commits, unrequested_commits) counts.
    """
    # Cannot classify without ready-for-review event
    if pr.ready_for_review_at is None:
        return (0, 0)

    ready_time = pr.ready_for_review_at.ready_at

    # Filter commits: only by PR author and after ready-for-review
    relevant_commits = [
        c
        for c in pr.commits
        if c.author == pr.author and c.committed_at > ready_time
    ]

    if not relevant_commits:
        return (0, 0)

    # Sort commits by time
    sorted_commits = sorted(relevant_commits, key=lambda c: c.committed_at)

    # Track CHANGES_REQUESTED cycles
    # A cycle is (reviewer, start_time, end_time or None if open)
    requested_cycles = []

    # Build cycles from reviews
    for review in pr.reviews:
        if review.state == "CHANGES_REQUESTED":
            reviewer = review.reviewer
            start_time = review.submitted_at

            # Find when this cycle closes
            end_time = None

            # Check for subsequent review request to same reviewer
            later_requests = [
                rr
                for rr in pr.review_requests
                if rr.requested_reviewer == reviewer
                and rr.requested_at > start_time
            ]
            if later_requests:
                earliest_request = min(
                    later_requests, key=lambda r: r.requested_at
                )
                end_time = earliest_request.requested_at

            # Check for subsequent APPROVED review from same reviewer
            later_approvals = [
                r
                for r in pr.reviews
                if r.reviewer == reviewer
                and r.submitted_at > start_time
                and r.state == "APPROVED"
            ]
            if later_approvals:
                earliest_approval = min(
                    later_approvals, key=lambda r: r.submitted_at
                )
                # Use earliest of review request or approval
                if (
                    end_time is None
                    or earliest_approval.submitted_at < end_time
                ):
                    end_time = earliest_approval.submitted_at

            requested_cycles.append((reviewer, start_time, end_time))

    # Classify each commit
    requested_count = 0
    unrequested_count = 0

    for commit in sorted_commits:
        # Check if commit falls within any requested cycle
        is_requested = False
        for _, start_time, end_time in requested_cycles:
            if commit.committed_at > start_time and (
                end_time is None or commit.committed_at < end_time
            ):
                is_requested = True
                break

        if is_requested:
            requested_count += 1
        else:
            unrequested_count += 1

    return (requested_count, unrequested_count)


def compute_repository_stats(
    pull_requests: List[PullRequest],
    until: Optional[datetime] = None,
) -> RepositoryStats:
    """Compute repository-level statistics from pull requests.

    Args:
        pull_requests: List of PullRequest objects.
        until: Optional end time for duration calculations (default: now).

    Returns:
        RepositoryStats object with computed metrics.
    """
    if until is None:
        until = datetime.now(timezone.utc)

    # Duration metrics
    open_durations = []
    closed_durations = []
    merged_durations = []

    for pr in pull_requests:
        if pr.state == "open":
            open_durations.append(_days_between(pr.created_at, until))
        elif pr.merged_at:
            merged_durations.append(_days_between(pr.created_at, pr.merged_at))
        elif pr.closed_at:
            closed_durations.append(_days_between(pr.created_at, pr.closed_at))

    # Time to first review
    time_to_first_review_values = []
    for pr in pull_requests:
        if pr.reviews:
            first_review = min(pr.reviews, key=lambda r: r.submitted_at)
            time_to_first_review_values.append(
                _days_between(pr.created_at, first_review.submitted_at)
            )

    # Commits per PR
    commits_per_pr_values = [float(len(pr.commits)) for pr in pull_requests]

    # Comments per 100 LOC
    comments_per_100_loc_values = []
    for pr in pull_requests:
        total_loc = pr.additions + pr.deletions
        if total_loc > 0:
            comments_per_100_loc = (len(pr.comments) / total_loc) * 100.0
            comments_per_100_loc_values.append(comments_per_100_loc)

    # Re-reviews per PR
    re_reviews_values = []
    for pr in pull_requests:
        # Count reviews by each reviewer
        reviewer_counts: Dict[str, int] = {}
        for review in pr.reviews:
            reviewer_counts[review.reviewer] = (
                reviewer_counts.get(review.reviewer, 0) + 1
            )
        # Count re-reviews (reviews after the first)
        re_reviews = sum(
            count - 1 for count in reviewer_counts.values() if count > 1
        )
        if re_reviews > 0:
            re_reviews_values.append(float(re_reviews))

    # Time between CHANGES_REQUESTED and re-request
    changes_to_rerequest_values = []
    for pr in pull_requests:
        # Find CHANGES_REQUESTED reviews
        changes_requested_reviews = [
            r for r in pr.reviews if r.state == "CHANGES_REQUESTED"
        ]

        for changes_review in changes_requested_reviews:
            # Find next review request after this CHANGES_REQUESTED
            later_requests = [
                rr
                for rr in pr.review_requests
                if rr.requested_at > changes_review.submitted_at
                and rr.requested_reviewer == changes_review.reviewer
            ]

            if later_requests:
                next_request = min(
                    later_requests, key=lambda r: r.requested_at
                )
                time_diff = _days_between(
                    changes_review.submitted_at, next_request.requested_at
                )
                changes_to_rerequest_values.append(time_diff)

    return RepositoryStats(
        open_pr_duration=_compute_distribution(open_durations),
        closed_pr_duration=_compute_distribution(closed_durations),
        merged_pr_duration=_compute_distribution(merged_durations),
        time_to_first_review=_compute_distribution(
            time_to_first_review_values
        ),
        commits_per_pr=_compute_distribution(commits_per_pr_values),
        comments_per_100_loc=_compute_distribution(
            comments_per_100_loc_values
        ),
        re_reviews_per_pr=_compute_distribution(re_reviews_values),
        time_between_changes_requested_and_re_request=_compute_distribution(
            changes_to_rerequest_values
        ),
    )


def _collect_user_data(pull_requests: List[PullRequest]) -> Dict[str, Dict]:
    """Collect per-user raw values used to derive user and group stats."""
    user_data: Dict[str, Dict] = {}

    def _init_user(username: str) -> None:
        """Initialize user data structure."""
        if username not in user_data:
            user_data[username] = {
                "review_times": [],
                "prs_reviewed": 0,
                "prs_with_changes_requested": 0,
                "direct_approval_count": 0,
                "loc_values": [],
                "comments_as_reviewer": [],
                "comments_as_author": [],
            }

    # Process each PR
    for pr in pull_requests:
        # Initialize author
        _init_user(pr.author)

        # LOC per created PR (for author)
        total_loc = pr.additions + pr.deletions
        user_data[pr.author]["loc_values"].append(float(total_loc))

        # Comments as author
        if total_loc > 0:
            author_comments = [c for c in pr.comments if c.author == pr.author]
            if author_comments:
                comments_per_100 = (len(author_comments) / total_loc) * 100.0
                user_data[pr.author]["comments_as_author"].append(
                    comments_per_100
                )

        # Process review timing
        for review_request in pr.review_requests:
            reviewer = review_request.requested_reviewer
            _init_user(reviewer)

            # Find review submitted after this request
            matching_reviews = [
                r
                for r in pr.reviews
                if r.reviewer == reviewer
                and r.submitted_at > review_request.requested_at
            ]

            if matching_reviews:
                # Find the first review after this request
                next_review = min(
                    matching_reviews, key=lambda r: r.submitted_at
                )
                hours = _hours_between(
                    review_request.requested_at, next_review.submitted_at
                )
                user_data[reviewer]["review_times"].append(hours)

        # Direct approval rate (APPROVED without prior CHANGES_REQUESTED)
        # Group reviews by reviewer for this PR
        pr_reviewer_reviews: Dict[str, List] = {}
        for review in pr.reviews:
            if review.reviewer not in pr_reviewer_reviews:
                pr_reviewer_reviews[review.reviewer] = []
            pr_reviewer_reviews[review.reviewer].append(review)

        for reviewer, reviews in pr_reviewer_reviews.items():
            _init_user(reviewer)

            # Count this PR as reviewed
            user_data[reviewer]["prs_reviewed"] += 1

            # Sort by submission time
            sorted_reviews = sorted(reviews, key=lambda r: r.submitted_at)

            # Check if first review is APPROVED
            if sorted_reviews[0].state == "APPROVED":
                user_data[reviewer]["direct_approval_count"] += 1

            # Check if any review is CHANGES_REQUESTED
            if any(r.state == "CHANGES_REQUESTED" for r in reviews):
                user_data[reviewer]["prs_with_changes_requested"] += 1

        # Comments per 100 LOC as reviewer
        if total_loc > 0:
            # Group comments by author
            comment_authors = {c.author for c in pr.comments}
            for commenter in comment_authors:
                if commenter != pr.author:  # Exclude PR author
                    _init_user(commenter)
                    commenter_comments = [
                        c for c in pr.comments if c.author == commenter
                    ]
                    comments_per_100 = (
                        len(commenter_comments) / total_loc
                    ) * 100.0
                    user_data[commenter]["comments_as_reviewer"].append(
                        comments_per_100
                    )

    return user_data


def compute_user_stats(
    pull_requests: List[PullRequest],
) -> Dict[str, UserStats]:
    """Compute user-level statistics from pull requests."""
    user_data = _collect_user_data(pull_requests)

    result: Dict[str, UserStats] = {}

    for username, data in user_data.items():
        # Calculate rates based on PRs reviewed (not individual reviews)
        prs_reviewed = data["prs_reviewed"]
        if prs_reviewed > 0:
            changes_requested_rate = (
                data["prs_with_changes_requested"] / prs_reviewed
            ) * 100.0
            direct_approval_rate = (
                data["direct_approval_count"] / prs_reviewed
            ) * 100.0
        else:
            changes_requested_rate = 0.0
            direct_approval_rate = 0.0

        result[username] = UserStats(
            time_to_submit_review=_compute_distribution(data["review_times"]),
            changes_requested_rate=changes_requested_rate,
            direct_approval_rate=direct_approval_rate,
            loc_per_created_pr=_compute_distribution(data["loc_values"]),
            comments_per_100_loc_as_reviewer=_compute_distribution(
                data["comments_as_reviewer"]
            ),
            comments_per_100_loc_as_author=_compute_distribution(
                data["comments_as_author"]
            ),
        )

    return result


def compute_group_stats(
    pull_requests: List[PullRequest],
    user_groups: Dict[str, List[str]],
    active_group_counts: Optional[Dict[str, int]] = None,
) -> Dict[str, GroupStats]:
    """Compute group-level statistics by aggregating member-level values."""
    user_data = _collect_user_data(pull_requests)
    group_stats: Dict[str, GroupStats] = {}

    for group_name, members in user_groups.items():
        group_review_times: List[float] = []
        group_loc_values: List[float] = []
        group_comments_as_reviewer: List[float] = []
        group_comments_as_author: List[float] = []
        group_prs_reviewed = 0
        group_prs_with_changes_requested = 0
        group_direct_approval_count = 0

        for member in members:
            member_data = user_data.get(member)
            if not member_data:
                continue
            group_review_times.extend(member_data["review_times"])
            group_loc_values.extend(member_data["loc_values"])
            group_comments_as_reviewer.extend(
                member_data["comments_as_reviewer"]
            )
            group_comments_as_author.extend(member_data["comments_as_author"])
            group_prs_reviewed += member_data["prs_reviewed"]
            group_prs_with_changes_requested += member_data[
                "prs_with_changes_requested"
            ]
            group_direct_approval_count += member_data["direct_approval_count"]

        if group_prs_reviewed > 0:
            changes_requested_rate = (
                group_prs_with_changes_requested / group_prs_reviewed
            ) * 100.0
            direct_approval_rate = (
                group_direct_approval_count / group_prs_reviewed
            ) * 100.0
        else:
            changes_requested_rate = 0.0
            direct_approval_rate = 0.0

        active_member_count = 0
        if active_group_counts is not None:
            active_member_count = active_group_counts.get(group_name, 0)

        group_stats[group_name] = GroupStats(
            member_count=len(members),
            active_member_count=active_member_count,
            time_to_submit_review=_compute_distribution(group_review_times),
            changes_requested_rate=changes_requested_rate,
            direct_approval_rate=direct_approval_rate,
            loc_per_created_pr=_compute_distribution(group_loc_values),
            comments_per_100_loc_as_reviewer=_compute_distribution(
                group_comments_as_reviewer
            ),
            comments_per_100_loc_as_author=_compute_distribution(
                group_comments_as_author
            ),
        )

    return group_stats
