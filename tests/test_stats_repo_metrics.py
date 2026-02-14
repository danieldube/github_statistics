"""Tests for repository-level statistics computation."""

from datetime import datetime, timedelta, timezone

from github_statistics.models import (
    CommentInfo,
    CommitInfo,
    PullRequest,
    ReviewEvent,
    ReviewRequestEvent,
)
from github_statistics.stats import Distribution, compute_repository_stats


def test_distribution_dataclass():
    """Test that Distribution dataclass can be instantiated."""
    dist = Distribution(
        count=5, minimum=1.0, maximum=10.0, mean=5.5, median=5.0
    )

    assert dist.count == 5
    assert dist.minimum == 1.0
    assert dist.maximum == 10.0
    assert dist.mean == 5.5
    assert dist.median == 5.0


def test_distribution_single_value():
    """Test distribution with a single value."""
    dist = Distribution(
        count=1, minimum=5.0, maximum=5.0, mean=5.0, median=5.0
    )

    assert dist.count == 1
    assert dist.minimum == dist.maximum == dist.mean == dist.median == 5.0


def test_open_pr_duration():
    """Test duration calculation for open PRs."""
    now = datetime(2026, 2, 14, 12, 0, 0, tzinfo=timezone.utc)
    created = datetime(2026, 2, 10, 12, 0, 0, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="Open PR",
        author="alice",
        created_at=created,
        state="open",
        additions=10,
        deletions=5,
    )

    stats = compute_repository_stats([pr], until=now)

    # Should have 4 days duration
    assert stats.open_pr_duration.count == 1
    assert stats.open_pr_duration.minimum == 4.0
    assert stats.open_pr_duration.maximum == 4.0
    assert stats.open_pr_duration.mean == 4.0
    assert stats.open_pr_duration.median == 4.0


def test_closed_pr_duration():
    """Test duration calculation for closed (not merged) PRs."""
    created = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    closed = datetime(2026, 1, 5, 12, 0, 0, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="Closed PR",
        author="bob",
        created_at=created,
        state="closed",
        additions=10,
        deletions=5,
        closed_at=closed,
        merged_at=None,  # Closed but not merged
    )

    stats = compute_repository_stats([pr])

    # Should have 4 days duration
    assert stats.closed_pr_duration.count == 1
    assert stats.closed_pr_duration.minimum == 4.0


def test_merged_pr_duration():
    """Test duration calculation for merged PRs."""
    created = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    merged = datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="Merged PR",
        author="charlie",
        created_at=created,
        state="closed",
        additions=10,
        deletions=5,
        merged_at=merged,
    )

    stats = compute_repository_stats([pr])

    # Should have 7 days duration
    assert stats.merged_pr_duration.count == 1
    assert stats.merged_pr_duration.minimum == 7.0
    assert stats.merged_pr_duration.maximum == 7.0


def test_multiple_prs_duration_distribution():
    """Test duration distribution with multiple PRs."""
    base_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    prs = [
        PullRequest(
            number=i,
            title=f"PR {i}",
            author="alice",
            created_at=base_time,
            state="closed",
            additions=10,
            deletions=5,
            merged_at=base_time + timedelta(days=i),
        )
        for i in [1, 3, 5, 7, 9]
    ]

    stats = compute_repository_stats(prs)

    assert stats.merged_pr_duration.count == 5
    assert stats.merged_pr_duration.minimum == 1.0
    assert stats.merged_pr_duration.maximum == 9.0
    assert stats.merged_pr_duration.mean == 5.0
    assert stats.merged_pr_duration.median == 5.0


def test_time_to_first_review():
    """Test time to first review calculation."""
    created = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    first_review = datetime(2026, 1, 1, 14, 0, 0, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with review",
        author="alice",
        created_at=created,
        state="open",
        additions=10,
        deletions=5,
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=first_review,
                state="APPROVED",
            )
        ],
    )

    stats = compute_repository_stats([pr])

    # 4 hours = 0.167 days (approximately)
    assert stats.time_to_first_review.count == 1
    assert abs(stats.time_to_first_review.minimum - 0.167) < 0.01


def test_pr_without_reviews():
    """Test that PRs without reviews are excluded from review metrics."""
    pr = PullRequest(
        number=1,
        title="No reviews",
        author="alice",
        created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
    )

    stats = compute_repository_stats([pr])

    # Should have no time-to-first-review data
    assert stats.time_to_first_review.count == 0


def test_commits_per_pr():
    """Test commits per PR distribution."""
    prs = [
        PullRequest(
            number=1,
            title="PR 1",
            author="alice",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            state="open",
            additions=10,
            deletions=5,
            commits=[
                CommitInfo(
                    sha=f"sha{i}",
                    author="alice",
                    committed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    message=f"Commit {i}",
                )
                for i in range(3)
            ],
        ),
        PullRequest(
            number=2,
            title="PR 2",
            author="bob",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            state="open",
            additions=20,
            deletions=10,
            commits=[
                CommitInfo(
                    sha=f"sha{i}",
                    author="bob",
                    committed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    message=f"Commit {i}",
                )
                for i in range(5)
            ],
        ),
    ]

    stats = compute_repository_stats(prs)

    assert stats.commits_per_pr.count == 2
    assert stats.commits_per_pr.minimum == 3.0
    assert stats.commits_per_pr.maximum == 5.0
    assert stats.commits_per_pr.mean == 4.0
    assert stats.commits_per_pr.median == 4.0


def test_comments_per_100_loc():
    """Test comments per 100 LOC calculation."""
    pr = PullRequest(
        number=1,
        title="PR with comments",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=80,
        deletions=20,  # Total: 100 LOC
        comments=[
            CommentInfo(
                author="bob",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Comment 1",
            ),
            CommentInfo(
                author="charlie",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Comment 2",
            ),
        ],
    )

    stats = compute_repository_stats([pr])

    # 2 comments per 100 LOC = 2.0
    assert stats.comments_per_100_loc.count == 1
    assert stats.comments_per_100_loc.minimum == 2.0


def test_comments_per_100_loc_zero_loc():
    """Test that PRs with zero LOC are excluded from comments per 100 LOC."""
    pr = PullRequest(
        number=1,
        title="Zero LOC PR",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=0,
        deletions=0,
        comments=[
            CommentInfo(
                author="bob",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Comment",
            )
        ],
    )

    stats = compute_repository_stats([pr])

    # Should be excluded from metric
    assert stats.comments_per_100_loc.count == 0


def test_re_reviews_per_pr():
    """Test re-reviews per PR (multiple reviews by same reviewer)."""
    pr = PullRequest(
        number=1,
        title="PR with re-reviews",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                state="CHANGES_REQUESTED",
            ),
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                state="APPROVED",
            ),
        ],
    )

    stats = compute_repository_stats([pr])

    # Bob reviewed twice, so 1 re-review
    assert stats.re_reviews_per_pr.count == 1
    assert stats.re_reviews_per_pr.minimum == 1.0


def test_time_between_changes_requested_and_re_request():
    """Test time between CHANGES_REQUESTED and next review request."""
    changes_req_time = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    re_request_time = datetime(2026, 1, 3, 14, 0, 0, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with changes requested",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=changes_req_time,
                state="CHANGES_REQUESTED",
            ),
        ],
        review_requests=[
            ReviewRequestEvent(
                requested_reviewer="bob",
                requested_at=re_request_time,
            ),
        ],
    )

    stats = compute_repository_stats([pr])

    # 1 day and 4 hours = 1.167 days (approximately)
    assert stats.time_between_changes_requested_and_re_request.count == 1
    assert (
        abs(
            stats.time_between_changes_requested_and_re_request.minimum - 1.167
        )
        < 0.01
    )


def test_empty_pr_list():
    """Test that empty PR list returns empty distributions."""
    stats = compute_repository_stats([])

    assert stats.open_pr_duration.count == 0
    assert stats.closed_pr_duration.count == 0
    assert stats.merged_pr_duration.count == 0
    assert stats.time_to_first_review.count == 0
    assert stats.commits_per_pr.count == 0
    assert stats.comments_per_100_loc.count == 0
    assert stats.re_reviews_per_pr.count == 0


def test_repository_stats_dataclass_structure():
    """Test that RepositoryStats dataclass has all required fields."""
    pr = PullRequest(
        number=1,
        title="Test PR",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
    )

    stats = compute_repository_stats([pr])

    # Check all required fields exist
    assert hasattr(stats, "open_pr_duration")
    assert hasattr(stats, "closed_pr_duration")
    assert hasattr(stats, "merged_pr_duration")
    assert hasattr(stats, "time_to_first_review")
    assert hasattr(stats, "commits_per_pr")
    assert hasattr(stats, "comments_per_100_loc")
    assert hasattr(stats, "re_reviews_per_pr")
    assert hasattr(stats, "time_between_changes_requested_and_re_request")

    # All should be Distribution instances
    assert isinstance(stats.open_pr_duration, Distribution)
    assert isinstance(stats.closed_pr_duration, Distribution)
    assert isinstance(stats.merged_pr_duration, Distribution)
