"""
Tests for data models (PRs, reviews, events, commits, comments).
"""

from datetime import datetime, timezone

from github_statistics.models import (
    CommentInfo,
    CommitInfo,
    PullRequest,
    ReadyForReviewEvent,
    ReviewEvent,
    ReviewRequestEvent,
)


def test_commit_info_instantiation():
    """Test that CommitInfo can be instantiated with expected fields."""
    commit = CommitInfo(
        sha="abc123",
        author="testuser",
        committed_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        message="Test commit",
    )

    assert commit.sha == "abc123"
    assert commit.author == "testuser"
    assert commit.committed_at == datetime(
        2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc
    )
    assert commit.message == "Test commit"


def test_comment_info_instantiation():
    """Test that CommentInfo can be instantiated with expected fields."""
    comment = CommentInfo(
        author="reviewer1",
        created_at=datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc),
        body="This looks good!",
    )

    assert comment.author == "reviewer1"
    assert comment.created_at == datetime(
        2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc
    )
    assert comment.body == "This looks good!"


def test_review_event_instantiation():
    """Test that ReviewEvent can be instantiated with expected fields."""
    review = ReviewEvent(
        reviewer="reviewer1",
        submitted_at=datetime(2024, 1, 3, 14, 0, 0, tzinfo=timezone.utc),
        state="APPROVED",
    )

    assert review.reviewer == "reviewer1"
    assert review.submitted_at == datetime(
        2024, 1, 3, 14, 0, 0, tzinfo=timezone.utc
    )
    assert review.state == "APPROVED"


def test_review_event_with_changes_requested():
    """Test ReviewEvent with CHANGES_REQUESTED state."""
    review = ReviewEvent(
        reviewer="reviewer2",
        submitted_at=datetime(2024, 1, 4, 9, 0, 0, tzinfo=timezone.utc),
        state="CHANGES_REQUESTED",
    )

    assert review.state == "CHANGES_REQUESTED"


def test_review_request_event_instantiation():
    """Test that ReviewRequestEvent can be instantiated."""
    event = ReviewRequestEvent(
        requested_reviewer="reviewer1",
        requested_at=datetime(2024, 1, 5, 11, 0, 0, tzinfo=timezone.utc),
    )

    assert event.requested_reviewer == "reviewer1"
    assert event.requested_at == datetime(
        2024, 1, 5, 11, 0, 0, tzinfo=timezone.utc
    )


def test_ready_for_review_event_instantiation():
    """Test that ReadyForReviewEvent can be instantiated."""
    event = ReadyForReviewEvent(
        ready_at=datetime(2024, 1, 6, 8, 0, 0, tzinfo=timezone.utc)
    )

    assert event.ready_at == datetime(2024, 1, 6, 8, 0, 0, tzinfo=timezone.utc)


def test_pull_request_minimal():
    """Test PullRequest with minimal required fields."""
    pr = PullRequest(
        number=1,
        title="Test PR",
        author="testuser",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
    )

    assert pr.number == 1
    assert pr.title == "Test PR"
    assert pr.author == "testuser"
    assert pr.created_at == datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    assert pr.state == "open"
    assert pr.additions == 10
    assert pr.deletions == 5


def test_pull_request_with_optional_fields():
    """Test PullRequest with optional fields populated."""
    pr = PullRequest(
        number=2,
        title="Another PR",
        author="developer",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="closed",
        additions=20,
        deletions=10,
        closed_at=datetime(2024, 1, 5, 16, 0, 0, tzinfo=timezone.utc),
        merged_at=datetime(2024, 1, 5, 16, 0, 0, tzinfo=timezone.utc),
    )

    assert pr.closed_at == datetime(2024, 1, 5, 16, 0, 0, tzinfo=timezone.utc)
    assert pr.merged_at == datetime(2024, 1, 5, 16, 0, 0, tzinfo=timezone.utc)


def test_pull_request_aggregates_commits():
    """Test that PullRequest can aggregate a list of commits."""
    commits = [
        CommitInfo(
            sha="abc123",
            author="dev1",
            committed_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            message="First commit",
        ),
        CommitInfo(
            sha="def456",
            author="dev1",
            committed_at=datetime(2024, 1, 3, 14, 0, 0, tzinfo=timezone.utc),
            message="Second commit",
        ),
    ]

    pr = PullRequest(
        number=3,
        title="PR with commits",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=50,
        deletions=20,
        commits=commits,
    )

    assert len(pr.commits) == 2
    assert pr.commits[0].sha == "abc123"
    assert pr.commits[1].sha == "def456"


def test_pull_request_aggregates_comments():
    """Test that PullRequest can aggregate a list of comments."""
    comments = [
        CommentInfo(
            author="reviewer1",
            created_at=datetime(2024, 1, 2, 9, 0, 0, tzinfo=timezone.utc),
            body="First comment",
        ),
        CommentInfo(
            author="reviewer2",
            created_at=datetime(2024, 1, 3, 10, 0, 0, tzinfo=timezone.utc),
            body="Second comment",
        ),
    ]

    pr = PullRequest(
        number=4,
        title="PR with comments",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=30,
        deletions=15,
        comments=comments,
    )

    assert len(pr.comments) == 2
    assert pr.comments[0].body == "First comment"
    assert pr.comments[1].body == "Second comment"


def test_pull_request_aggregates_reviews():
    """Test that PullRequest can aggregate a list of review events."""
    reviews = [
        ReviewEvent(
            reviewer="reviewer1",
            submitted_at=datetime(2024, 1, 3, 14, 0, 0, tzinfo=timezone.utc),
            state="APPROVED",
        ),
        ReviewEvent(
            reviewer="reviewer2",
            submitted_at=datetime(2024, 1, 4, 9, 0, 0, tzinfo=timezone.utc),
            state="CHANGES_REQUESTED",
        ),
    ]

    pr = PullRequest(
        number=5,
        title="PR with reviews",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=40,
        deletions=25,
        reviews=reviews,
    )

    assert len(pr.reviews) == 2
    assert pr.reviews[0].state == "APPROVED"
    assert pr.reviews[1].state == "CHANGES_REQUESTED"


def test_pull_request_aggregates_review_requests():
    """Test that PullRequest can aggregate review request events."""
    review_requests = [
        ReviewRequestEvent(
            requested_reviewer="reviewer1",
            requested_at=datetime(2024, 1, 2, 11, 0, 0, tzinfo=timezone.utc),
        ),
        ReviewRequestEvent(
            requested_reviewer="reviewer2",
            requested_at=datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc),
        ),
    ]

    pr = PullRequest(
        number=6,
        title="PR with review requests",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=35,
        deletions=18,
        review_requests=review_requests,
    )

    assert len(pr.review_requests) == 2
    assert pr.review_requests[0].requested_reviewer == "reviewer1"
    assert pr.review_requests[1].requested_reviewer == "reviewer2"


def test_pull_request_with_ready_for_review_event():
    """Test PullRequest with ready-for-review event."""
    ready_event = ReadyForReviewEvent(
        ready_at=datetime(2024, 1, 2, 15, 0, 0, tzinfo=timezone.utc)
    )

    pr = PullRequest(
        number=7,
        title="PR with ready event",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=25,
        deletions=12,
        ready_for_review_at=ready_event,
    )

    assert pr.ready_for_review_at is not None
    assert pr.ready_for_review_at.ready_at == datetime(
        2024, 1, 2, 15, 0, 0, tzinfo=timezone.utc
    )


def test_pull_request_complete_aggregation():
    """Test PullRequest with all aggregated data."""
    commits = [
        CommitInfo(
            sha="abc",
            author="dev1",
            committed_at=datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            message="Commit 1",
        )
    ]
    comments = [
        CommentInfo(
            author="reviewer1",
            created_at=datetime(2024, 1, 3, 9, 0, 0, tzinfo=timezone.utc),
            body="Comment 1",
        )
    ]
    reviews = [
        ReviewEvent(
            reviewer="reviewer1",
            submitted_at=datetime(2024, 1, 4, 14, 0, 0, tzinfo=timezone.utc),
            state="APPROVED",
        )
    ]
    review_requests = [
        ReviewRequestEvent(
            requested_reviewer="reviewer1",
            requested_at=datetime(2024, 1, 3, 11, 0, 0, tzinfo=timezone.utc),
        )
    ]
    ready_event = ReadyForReviewEvent(
        ready_at=datetime(2024, 1, 2, 13, 0, 0, tzinfo=timezone.utc)
    )

    pr = PullRequest(
        number=8,
        title="Complete PR",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="merged",
        additions=100,
        deletions=50,
        closed_at=datetime(2024, 1, 5, 16, 0, 0, tzinfo=timezone.utc),
        merged_at=datetime(2024, 1, 5, 16, 0, 0, tzinfo=timezone.utc),
        commits=commits,
        comments=comments,
        reviews=reviews,
        review_requests=review_requests,
        ready_for_review_at=ready_event,
    )

    assert len(pr.commits) == 1
    assert len(pr.comments) == 1
    assert len(pr.reviews) == 1
    assert len(pr.review_requests) == 1
    assert pr.ready_for_review_at is not None


def test_pull_request_created_before_closed_invariant():
    """Test that created_at is before closed_at when both exist."""
    pr = PullRequest(
        number=9,
        title="Closed PR",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="closed",
        additions=10,
        deletions=5,
        closed_at=datetime(2024, 1, 5, 16, 0, 0, tzinfo=timezone.utc),
    )

    # Verify invariant
    assert pr.created_at < pr.closed_at


def test_pull_request_created_before_merged_invariant():
    """Test that created_at is before merged_at when both exist."""
    pr = PullRequest(
        number=10,
        title="Merged PR",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="merged",
        additions=10,
        deletions=5,
        merged_at=datetime(2024, 1, 5, 16, 0, 0, tzinfo=timezone.utc),
    )

    # Verify invariant
    assert pr.created_at < pr.merged_at


def test_pull_request_default_empty_lists():
    """Test that list fields default to empty lists."""
    pr = PullRequest(
        number=11,
        title="PR with defaults",
        author="dev1",
        created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
    )

    # Verify default empty lists
    assert pr.commits == []
    assert pr.comments == []
    assert pr.reviews == []
    assert pr.review_requests == []


def test_all_timestamps_are_datetime_objects():
    """Test that all timestamp fields use datetime objects."""
    now = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

    # Test all model timestamps
    commit = CommitInfo(
        sha="test", author="dev", committed_at=now, message="test"
    )
    assert isinstance(commit.committed_at, datetime)

    comment = CommentInfo(author="dev", created_at=now, body="test")
    assert isinstance(comment.created_at, datetime)

    review = ReviewEvent(reviewer="dev", submitted_at=now, state="APPROVED")
    assert isinstance(review.submitted_at, datetime)

    review_req = ReviewRequestEvent(requested_reviewer="dev", requested_at=now)
    assert isinstance(review_req.requested_at, datetime)

    ready = ReadyForReviewEvent(ready_at=now)
    assert isinstance(ready.ready_at, datetime)

    pr = PullRequest(
        number=12,
        title="Test",
        author="dev",
        created_at=now,
        state="open",
        additions=10,
        deletions=5,
    )
    assert isinstance(pr.created_at, datetime)


def test_pull_request_states():
    """Test various PR states."""
    states = ["open", "closed", "merged"]

    for state in states:
        pr = PullRequest(
            number=100,
            title="Test",
            author="dev",
            created_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            state=state,
            additions=10,
            deletions=5,
        )
        assert pr.state == state


def test_review_states():
    """Test various review states."""
    states = ["APPROVED", "CHANGES_REQUESTED", "COMMENTED", "DISMISSED"]

    for state in states:
        review = ReviewEvent(
            reviewer="reviewer",
            submitted_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            state=state,
        )
        assert review.state == state
