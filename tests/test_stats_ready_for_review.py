"""Tests for heuristic metrics related to ready-for-review and commit classification."""

from datetime import datetime, timezone

from github_statistics.models import (
    CommitInfo,
    PullRequest,
    ReadyForReviewEvent,
    ReviewEvent,
    ReviewRequestEvent,
)
from github_statistics.stats import classify_commits_requested_vs_unrequested


def test_classify_commits_no_ready_for_review():
    """Test that PRs without ready_for_review_at return (0, 0)."""
    pr = PullRequest(
        number=1,
        title="PR without ready event",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            CommitInfo(
                sha="abc123",
                author="alice",
                committed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                message="Commit 1",
            ),
        ],
        ready_for_review_at=None,  # No ready-for-review event
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # Without ready-for-review event, we can't classify commits
    assert requested == 0
    assert unrequested == 0


def test_classify_commits_all_before_ready():
    """Test that commits before ready-for-review are not counted."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with early commits",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            CommitInfo(
                sha="abc123",
                author="alice",
                committed_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                message="Commit before ready",
            ),
            CommitInfo(
                sha="def456",
                author="alice",
                committed_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                message="Another early commit",
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # All commits before ready-for-review
    assert requested == 0
    assert unrequested == 0


def test_classify_commits_after_ready_no_reviews():
    """Test commits after ready-for-review with no reviews are unrequested."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with commits after ready, no reviews",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            CommitInfo(
                sha="abc123",
                author="alice",
                committed_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
                message="Commit after ready",
            ),
            CommitInfo(
                sha="def456",
                author="alice",
                committed_at=datetime(2026, 1, 7, tzinfo=timezone.utc),
                message="Another commit after ready",
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # 2 commits after ready-for-review, no reviews = all unrequested
    assert requested == 0
    assert unrequested == 2


def test_classify_commits_after_changes_requested():
    """Test commits after CHANGES_REQUESTED are classified as requested."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)
    changes_requested_time = datetime(2026, 1, 6, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with changes requested",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            CommitInfo(
                sha="abc123",
                author="alice",
                committed_at=datetime(2026, 1, 7, tzinfo=timezone.utc),
                message="Fix requested changes",
            ),
            CommitInfo(
                sha="def456",
                author="alice",
                committed_at=datetime(2026, 1, 8, tzinfo=timezone.utc),
                message="More fixes",
            ),
        ],
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=changes_requested_time,
                state="CHANGES_REQUESTED",
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # 2 commits after CHANGES_REQUESTED = all requested
    assert requested == 2
    assert unrequested == 0


def test_classify_commits_mixed_requested_unrequested():
    """Test classification of mixed requested and unrequested commits."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)
    changes_requested_time = datetime(2026, 1, 7, tzinfo=timezone.utc)
    re_request_time = datetime(2026, 1, 9, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with mixed commits",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            # After ready, before any review
            CommitInfo(
                sha="commit1",
                author="alice",
                committed_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
                message="Unrequested commit 1",
            ),
            # After CHANGES_REQUESTED
            CommitInfo(
                sha="commit2",
                author="alice",
                committed_at=datetime(2026, 1, 8, tzinfo=timezone.utc),
                message="Fix for changes requested",
            ),
            # After re-request (cycle closed)
            CommitInfo(
                sha="commit3",
                author="alice",
                committed_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
                message="Unrequested commit 2",
            ),
        ],
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=changes_requested_time,
                state="CHANGES_REQUESTED",
            ),
        ],
        review_requests=[
            ReviewRequestEvent(
                requested_reviewer="bob",
                requested_at=re_request_time,
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # 1 requested (commit2), 2 unrequested (commit1, commit3)
    assert requested == 1
    assert unrequested == 2


def test_classify_commits_multiple_changes_requested_cycles():
    """Test multiple CHANGES_REQUESTED cycles with commits."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with multiple cycles",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            # Unrequested before first review
            CommitInfo(
                sha="commit1",
                author="alice",
                committed_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
                message="Initial commit",
            ),
            # Requested after first CHANGES_REQUESTED
            CommitInfo(
                sha="commit2",
                author="alice",
                committed_at=datetime(2026, 1, 8, tzinfo=timezone.utc),
                message="Fix cycle 1",
            ),
            # Unrequested after re-request
            CommitInfo(
                sha="commit3",
                author="alice",
                committed_at=datetime(2026, 1, 11, tzinfo=timezone.utc),
                message="Additional work",
            ),
            # Requested after second CHANGES_REQUESTED
            CommitInfo(
                sha="commit4",
                author="alice",
                committed_at=datetime(2026, 1, 13, tzinfo=timezone.utc),
                message="Fix cycle 2",
            ),
        ],
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 7, tzinfo=timezone.utc),
                state="CHANGES_REQUESTED",
            ),
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 12, tzinfo=timezone.utc),
                state="CHANGES_REQUESTED",
            ),
        ],
        review_requests=[
            ReviewRequestEvent(
                requested_reviewer="bob",
                requested_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
            ),
            ReviewRequestEvent(
                requested_reviewer="bob",
                requested_at=datetime(2026, 1, 14, tzinfo=timezone.utc),
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # 2 requested (commit2, commit4), 2 unrequested (commit1, commit3)
    assert requested == 2
    assert unrequested == 2


def test_classify_commits_approved_review_closes_cycle():
    """Test that APPROVED review closes a CHANGES_REQUESTED cycle."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with approved after changes",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            # After ready, before review
            CommitInfo(
                sha="commit1",
                author="alice",
                committed_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
                message="Initial",
            ),
            # After CHANGES_REQUESTED
            CommitInfo(
                sha="commit2",
                author="alice",
                committed_at=datetime(2026, 1, 8, tzinfo=timezone.utc),
                message="Fix",
            ),
            # After APPROVED (cycle closed)
            CommitInfo(
                sha="commit3",
                author="alice",
                committed_at=datetime(2026, 1, 11, tzinfo=timezone.utc),
                message="New work",
            ),
        ],
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 7, tzinfo=timezone.utc),
                state="CHANGES_REQUESTED",
            ),
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
                state="APPROVED",
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # 1 requested (commit2), 2 unrequested (commit1, commit3)
    assert requested == 1
    assert unrequested == 2


def test_classify_commits_only_commits_by_pr_author():
    """Test that only commits by PR author are counted."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with commits from different authors",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            CommitInfo(
                sha="commit1",
                author="alice",
                committed_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
                message="Alice's commit",
            ),
            CommitInfo(
                sha="commit2",
                author="bob",  # Different author
                committed_at=datetime(2026, 1, 7, tzinfo=timezone.utc),
                message="Bob's commit",
            ),
            CommitInfo(
                sha="commit3",
                author="alice",
                committed_at=datetime(2026, 1, 8, tzinfo=timezone.utc),
                message="Another Alice commit",
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # Only 2 commits by alice (PR author)
    assert requested == 0
    assert unrequested == 2


def test_classify_commits_empty_commits_list():
    """Test PR with no commits after ready-for-review."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with no commits",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    assert requested == 0
    assert unrequested == 0


def test_classify_commits_commented_review_does_not_open_cycle():
    """Test that COMMENTED reviews don't open a requested cycle."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with COMMENTED review",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            CommitInfo(
                sha="commit1",
                author="alice",
                committed_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
                message="Commit 1",
            ),
            CommitInfo(
                sha="commit2",
                author="alice",
                committed_at=datetime(2026, 1, 8, tzinfo=timezone.utc),
                message="Commit 2",
            ),
        ],
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 7, tzinfo=timezone.utc),
                state="COMMENTED",  # Just comments, no changes requested
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # No CHANGES_REQUESTED, so all commits are unrequested
    assert requested == 0
    assert unrequested == 2


def test_classify_commits_changes_requested_without_subsequent_commits():
    """Test CHANGES_REQUESTED without any commits after it."""
    ready_time = datetime(2026, 1, 5, tzinfo=timezone.utc)

    pr = PullRequest(
        number=1,
        title="PR with changes requested but no fixes yet",
        author="alice",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        state="open",
        additions=10,
        deletions=5,
        commits=[
            CommitInfo(
                sha="commit1",
                author="alice",
                committed_at=datetime(2026, 1, 6, tzinfo=timezone.utc),
                message="Initial work",
            ),
        ],
        reviews=[
            ReviewEvent(
                reviewer="bob",
                submitted_at=datetime(2026, 1, 7, tzinfo=timezone.utc),
                state="CHANGES_REQUESTED",
            ),
        ],
        ready_for_review_at=ReadyForReviewEvent(ready_at=ready_time),
    )

    requested, unrequested = classify_commits_requested_vs_unrequested(pr)

    # Commit before CHANGES_REQUESTED = unrequested
    assert requested == 0
    assert unrequested == 1
