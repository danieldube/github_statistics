"""Tests for user-level statistics computation."""

from datetime import datetime, timezone

from github_statistics.models import (
    CommentInfo,
    PullRequest,
    ReviewEvent,
    ReviewRequestEvent,
)
from github_statistics.stats import compute_user_stats


def test_user_stats_time_to_submit_review():
    """Test time between review request and submission."""
    request_time = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    submit_time = datetime(2026, 1, 1, 14, 0, 0, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR for bob to review",
        author="alice",
        created_at=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        review_requests=[
            ReviewRequestEvent(
                requested_reviewer="bob",
                requested_at=request_time,
            ),
        ],
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=submit_time,
                state="APPROVED",
            ),
        ],
    )

    user_stats = compute_user_stats([pr])

    assert "bob" in user_stats
    # 4 hours = 4.0
    assert user_stats["bob"].time_to_submit_review.count == 1
    assert abs(user_stats["bob"].time_to_submit_review.minimum - 4.0) < 0.01


def test_user_stats_request_for_changes_rate():
    """Test request-for-changes rate calculation."""
    prs = [
        PullRequest(
            number=i,
            title=f"PR {i}",
            author="alice",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            state="open",
            additions=10,
            deletions=5,
            reviews=[
                ReviewEvent(
                    reviewer="bob",
                    submitted_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                    state="CHANGES_REQUESTED" if i <= 2 else "APPROVED",
                ),
            ],
        )
        for i in range(1, 6)  # 5 PRs total
    ]

    user_stats = compute_user_stats(prs)

    assert "bob" in user_stats
    # 2 out of 5 = 40% changes requested
    assert abs(user_stats["bob"].changes_requested_rate - 40.0) < 0.01
    # 3 out of 5 = 60% direct approval
    assert abs(user_stats["bob"].direct_approval_rate - 60.0) < 0.01


def test_user_stats_direct_approval_rate():
    """Test direct approval rate (APPROVED without CHANGES_REQUESTED)."""
    prs = [
        PullRequest(
            number=1,
            title="PR 1",
            author="alice",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            state="open",
            additions=10,
            deletions=5,
            reviews=[
                ReviewEvent(
                    reviewer="bob",
                    submitted_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                    state="APPROVED",
                ),
            ],
        ),
        PullRequest(
            number=2,
            title="PR 2",
            author="alice",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            state="open",
            additions=10,
            deletions=5,
            reviews=[
                ReviewEvent(
                    reviewer="bob",
                    submitted_at=datetime(
                        2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc
                    ),
                    state="CHANGES_REQUESTED",
                ),
                ReviewEvent(
                    reviewer="bob",
                    submitted_at=datetime(
                        2026, 1, 3, 10, 0, 0, tzinfo=timezone.utc
                    ),
                    state="APPROVED",
                ),
            ],
        ),
    ]

    user_stats = compute_user_stats(prs)

    # PR 1: direct approval, PR 2: changes requested first
    # 1 out of 2 = 50% direct approval
    assert abs(user_stats["bob"].direct_approval_rate - 50.0) < 0.01


def test_user_stats_loc_per_created_pr():
    """Test LOC per created PR for PR authors."""
    prs = [
        PullRequest(
            number=1,
            title="PR 1",
            author="alice",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            state="open",
            additions=80,
            deletions=20,  # 100 LOC
        ),
        PullRequest(
            number=2,
            title="PR 2",
            author="alice",
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            state="open",
            additions=150,
            deletions=50,  # 200 LOC
        ),
    ]

    user_stats = compute_user_stats(prs)

    assert "alice" in user_stats
    assert user_stats["alice"].loc_per_created_pr.count == 2
    assert user_stats["alice"].loc_per_created_pr.minimum == 100.0
    assert user_stats["alice"].loc_per_created_pr.maximum == 200.0
    assert user_stats["alice"].loc_per_created_pr.mean == 150.0


def test_user_stats_comments_per_100_loc_as_reviewer():
    """Test comments per 100 LOC as a reviewer."""
    pr = PullRequest(
        number=1,
        title="PR",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=80,
        deletions=20,  # 100 LOC
        comments=[
            CommentInfo(
                author="bob",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Comment 1",
            ),
            CommentInfo(
                author="bob",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Comment 2",
            ),
            CommentInfo(
                author="charlie",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Comment 3",
            ),
        ],
    )

    user_stats = compute_user_stats([pr])

    # Bob made 2 comments on 100 LOC = 2.0 per 100 LOC
    assert "bob" in user_stats
    assert user_stats["bob"].comments_per_100_loc_as_reviewer.count == 1
    assert user_stats["bob"].comments_per_100_loc_as_reviewer.minimum == 2.0

    # Charlie made 1 comment on 100 LOC = 1.0 per 100 LOC
    assert "charlie" in user_stats
    assert user_stats["charlie"].comments_per_100_loc_as_reviewer.count == 1
    assert (
        user_stats["charlie"].comments_per_100_loc_as_reviewer.minimum == 1.0
    )


def test_user_stats_comments_per_100_loc_as_author():
    """Test comments per 100 LOC as a PR author."""
    pr = PullRequest(
        number=1,
        title="PR",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=50,
        deletions=50,  # 100 LOC
        comments=[
            CommentInfo(
                author="alice",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Author comment 1",
            ),
            CommentInfo(
                author="alice",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Author comment 2",
            ),
            CommentInfo(
                author="alice",
                created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                body="Author comment 3",
            ),
        ],
    )

    user_stats = compute_user_stats([pr])

    # Alice made 3 comments on her own 100 LOC PR = 3.0 per 100 LOC
    assert "alice" in user_stats
    assert user_stats["alice"].comments_per_100_loc_as_author.count == 1
    assert user_stats["alice"].comments_per_100_loc_as_author.minimum == 3.0


def test_user_stats_multiple_users():
    """Test that stats are computed correctly for multiple users."""
    prs = [
        PullRequest(
            number=1,
            title="Alice's PR",
            author="alice",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            state="open",
            additions=100,
            deletions=50,
        ),
        PullRequest(
            number=2,
            title="Bob's PR",
            author="bob",
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
            state="open",
            additions=200,
            deletions=100,
        ),
    ]

    user_stats = compute_user_stats(prs)

    assert "alice" in user_stats
    assert "bob" in user_stats
    assert user_stats["alice"].loc_per_created_pr.mean == 150.0
    assert user_stats["bob"].loc_per_created_pr.mean == 300.0


def test_user_stats_reviewer_without_request():
    """Test reviewer who reviewed without explicit request."""
    pr = PullRequest(
        number=1,
        title="PR",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                state="APPROVED",
            ),
        ],
        # No review_requests for bob
    )

    user_stats = compute_user_stats([pr])

    # Bob reviewed but has no time_to_submit_review data (no request)
    assert "bob" in user_stats
    assert user_stats["bob"].time_to_submit_review.count == 0
    # But still has approval rate
    assert user_stats["bob"].direct_approval_rate == 100.0


def test_user_stats_empty_pr_list():
    """Test that empty PR list returns empty user stats."""
    user_stats = compute_user_stats([])

    assert user_stats == {}


def test_user_stats_dataclass_structure():
    """Test that UserStats dataclass has all required fields."""
    pr = PullRequest(
        number=1,
        title="Test PR",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
    )

    user_stats = compute_user_stats([pr])

    # Alice should have stats as author
    assert "alice" in user_stats
    stats = user_stats["alice"]

    # Check all required fields exist
    assert hasattr(stats, "time_to_submit_review")
    assert hasattr(stats, "changes_requested_rate")
    assert hasattr(stats, "direct_approval_rate")
    assert hasattr(stats, "loc_per_created_pr")
    assert hasattr(stats, "comments_per_100_loc_as_reviewer")
    assert hasattr(stats, "comments_per_100_loc_as_author")


def test_user_stats_zero_reviews():
    """Test user with zero reviews."""
    pr = PullRequest(
        number=1,
        title="PR",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
    )

    user_stats = compute_user_stats([pr])

    # Alice has no reviews, so approval rates should be 0
    assert user_stats["alice"].changes_requested_rate == 0.0
    assert user_stats["alice"].direct_approval_rate == 0.0


def test_user_stats_re_requested_review():
    """Test time to submit review when re-requested."""
    first_request = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    first_review = datetime(2026, 1, 1, 14, 0, 0, tzinfo=timezone.utc)
    second_request = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    second_review = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR",
        author="alice",
        created_at=datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        review_requests=[
            ReviewRequestEvent(
                requested_reviewer="bob",
                requested_at=first_request,
            ),
            ReviewRequestEvent(
                requested_reviewer="bob",
                requested_at=second_request,
            ),
        ],
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=first_review,
                state="CHANGES_REQUESTED",
            ),
            ReviewEvent(
                reviewer="bob",
                submitted_at=second_review,
                state="APPROVED",
            ),
        ],
    )

    user_stats = compute_user_stats([pr])

    # Should have 2 review times: 4 hours and 2 hours
    assert user_stats["bob"].time_to_submit_review.count == 2
    assert user_stats["bob"].time_to_submit_review.minimum == 2.0
    assert user_stats["bob"].time_to_submit_review.maximum == 4.0
