"""Tests for Markdown report generation."""

from datetime import datetime, timezone

from github_statistics.cli import RunOptions
from github_statistics.config import Config
from github_statistics.report_md import render_report
from github_statistics.stats import Distribution, RepositoryStats, UserStats


def test_render_report_basic_structure():
    """Test that report has basic structure with sections."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["org/repo1"],
        users=["alice"],
        output="test.md",
        max_workers=4,
    )

    repo_stats = {
        "org/repo1": RepositoryStats(
            open_pr_duration=Distribution(1, 5.0, 5.0, 5.0, 5.0),
            closed_pr_duration=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            merged_pr_duration=Distribution(2, 3.0, 7.0, 5.0, 5.0),
            time_to_first_review=Distribution(1, 0.5, 0.5, 0.5, 0.5),
            commits_per_pr=Distribution(2, 2.0, 5.0, 3.5, 3.5),
            comments_per_100_loc=Distribution(1, 2.5, 2.5, 2.5, 2.5),
            re_reviews_per_pr=Distribution(1, 1.0, 1.0, 1.0, 1.0),
            time_between_changes_requested_and_re_request=Distribution(
                0, 0.0, 0.0, 0.0, 0.0
            ),
        )
    }

    user_stats = {
        "alice": UserStats(
            time_to_submit_review=Distribution(2, 1.5, 4.0, 2.75, 2.75),
            changes_requested_rate=20.0,
            direct_approval_rate=80.0,
            loc_per_created_pr=Distribution(3, 50.0, 200.0, 125.0, 125.0),
            comments_per_100_loc_as_reviewer=Distribution(
                2, 1.0, 3.0, 2.0, 2.0
            ),
            comments_per_100_loc_as_author=Distribution(1, 2.5, 2.5, 2.5, 2.5),
        )
    }

    report = render_report(repo_stats, user_stats, options)

    # Check basic structure
    assert "# GitHub Statistics Report" in report
    assert "## Repositories" in report
    assert "## Users" in report
    assert "### org/repo1" in report
    assert "### alice" in report


def test_render_report_with_date_filters():
    """Test that date filters appear in metadata section."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    since = datetime(2026, 1, 1, tzinfo=timezone.utc)
    until = datetime(2026, 2, 1, tzinfo=timezone.utc)

    options = RunOptions(
        config=config,
        since=since,
        until=until,
        repositories=["org/repo1"],
        users=["alice"],
        output="test.md",
        max_workers=4,
    )

    repo_stats = {}
    user_stats = {}

    report = render_report(repo_stats, user_stats, options)

    assert "2026-01-01" in report
    assert "2026-02-01" in report


def test_render_report_distribution_formatting():
    """Test that distributions are formatted with correct precision."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["org/repo"],
        users=[],
        output="test.md",
        max_workers=4,
    )

    repo_stats = {
        "org/repo": RepositoryStats(
            open_pr_duration=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            closed_pr_duration=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            merged_pr_duration=Distribution(
                5, 1.234, 10.567, 5.891, 5.5
            ),  # Various decimals
            time_to_first_review=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            commits_per_pr=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            comments_per_100_loc=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            re_reviews_per_pr=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            time_between_changes_requested_and_re_request=Distribution(
                0, 0.0, 0.0, 0.0, 0.0
            ),
        )
    }

    user_stats = {}

    report = render_report(repo_stats, user_stats, options)

    # Check that numbers are formatted with 1-2 decimal places
    assert "1.23" in report or "1.2" in report  # min
    assert "10.57" in report or "10.6" in report  # max
    assert "5.89" in report or "5.9" in report  # mean
    assert "5.5" in report or "5.50" in report  # median


def test_render_report_no_data():
    """Test that empty stats are handled gracefully."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo"],
        users=["bob"],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["org/repo"],
        users=["bob"],
        output="test.md",
        max_workers=4,
    )

    # Empty stats
    repo_stats = {}
    user_stats = {}

    report = render_report(repo_stats, user_stats, options)

    assert "# GitHub Statistics Report" in report
    assert (
        "no" in report.lower() and "available" in report.lower()
    ) or "no data" in report.lower()


def test_render_report_zero_count_distributions():
    """Test that distributions with zero count show 'no data'."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo"],
        users=[],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["org/repo"],
        users=[],
        output="test.md",
        max_workers=4,
    )

    # All distributions with count=0
    repo_stats = {
        "org/repo": RepositoryStats(
            open_pr_duration=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            closed_pr_duration=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            merged_pr_duration=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            time_to_first_review=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            commits_per_pr=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            comments_per_100_loc=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            re_reviews_per_pr=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            time_between_changes_requested_and_re_request=Distribution(
                0, 0.0, 0.0, 0.0, 0.0
            ),
        )
    }

    user_stats = {}

    report = render_report(repo_stats, user_stats, options)

    # Should indicate no data for distributions with count=0
    assert "no data" in report.lower()


def test_render_report_user_rates():
    """Test that user approval rates are formatted as percentages."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=[],
        users=["charlie"],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=[],
        users=["charlie"],
        output="test.md",
        max_workers=4,
    )

    repo_stats = {}

    user_stats = {
        "charlie": UserStats(
            time_to_submit_review=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            changes_requested_rate=25.5,
            direct_approval_rate=74.5,
            loc_per_created_pr=Distribution(0, 0.0, 0.0, 0.0, 0.0),
            comments_per_100_loc_as_reviewer=Distribution(
                0, 0.0, 0.0, 0.0, 0.0
            ),
            comments_per_100_loc_as_author=Distribution(0, 0.0, 0.0, 0.0, 0.0),
        )
    }

    report = render_report(repo_stats, user_stats, options)

    # Check percentage formatting
    assert "25.5%" in report or "25.50%" in report
    assert "74.5%" in report or "74.50%" in report


def test_render_report_sorted_output():
    """Test that repositories and users are sorted alphabetically."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/zebra", "org/alpha", "org/beta"],
        users=["zoe", "alice", "bob"],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["org/zebra", "org/alpha", "org/beta"],
        users=["zoe", "alice", "bob"],
        output="test.md",
        max_workers=4,
    )

    empty_dist = Distribution(0, 0.0, 0.0, 0.0, 0.0)
    empty_repo_stats = RepositoryStats(
        open_pr_duration=empty_dist,
        closed_pr_duration=empty_dist,
        merged_pr_duration=empty_dist,
        time_to_first_review=empty_dist,
        commits_per_pr=empty_dist,
        comments_per_100_loc=empty_dist,
        re_reviews_per_pr=empty_dist,
        time_between_changes_requested_and_re_request=empty_dist,
    )

    empty_user_stats = UserStats(
        time_to_submit_review=empty_dist,
        changes_requested_rate=0.0,
        direct_approval_rate=0.0,
        loc_per_created_pr=empty_dist,
        comments_per_100_loc_as_reviewer=empty_dist,
        comments_per_100_loc_as_author=empty_dist,
    )

    repo_stats = {
        "org/zebra": empty_repo_stats,
        "org/alpha": empty_repo_stats,
        "org/beta": empty_repo_stats,
    }

    user_stats = {
        "zoe": empty_user_stats,
        "alice": empty_user_stats,
        "bob": empty_user_stats,
    }

    report = render_report(repo_stats, user_stats, options)

    # Find positions of repo names
    alpha_pos = report.find("### org/alpha")
    beta_pos = report.find("### org/beta")
    zebra_pos = report.find("### org/zebra")

    # Repos should be in alphabetical order
    assert alpha_pos < beta_pos < zebra_pos

    # Find positions of user names
    alice_user_pos = report.find("### alice")
    bob_user_pos = report.find("### bob")
    zoe_user_pos = report.find("### zoe")

    # Users should be in alphabetical order
    assert alice_user_pos < bob_user_pos < zoe_user_pos


def test_render_report_metric_labels():
    """Test that all expected metric labels appear in report."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo"],
        users=["dave"],
    )

    options = RunOptions(
        config=config,
        since=None,
        until=None,
        repositories=["org/repo"],
        users=["dave"],
        output="test.md",
        max_workers=4,
    )

    dist = Distribution(1, 1.0, 1.0, 1.0, 1.0)
    repo_stats = {
        "org/repo": RepositoryStats(
            open_pr_duration=dist,
            closed_pr_duration=dist,
            merged_pr_duration=dist,
            time_to_first_review=dist,
            commits_per_pr=dist,
            comments_per_100_loc=dist,
            re_reviews_per_pr=dist,
            time_between_changes_requested_and_re_request=dist,
        )
    }

    user_stats = {
        "dave": UserStats(
            time_to_submit_review=dist,
            changes_requested_rate=15.0,
            direct_approval_rate=85.0,
            loc_per_created_pr=dist,
            comments_per_100_loc_as_reviewer=dist,
            comments_per_100_loc_as_author=dist,
        )
    }

    report = render_report(repo_stats, user_stats, options)

    # Check repository metric labels
    assert "Duration open pull requests" in report
    assert "Duration closed pull requests" in report
    assert "Duration merged pull requests" in report
    assert "Time to first review" in report
    assert "Commits per PR" in report
    assert "Comments per 100 LOC" in report
    assert "Re-reviews per PR" in report

    # Check user metric labels
    assert "Time between requested and submitting review" in report
    assert (
        "Request for changes rate" in report
        or "Changes requested rate" in report
    )
    assert "Direct approval rate" in report
    assert (
        "Changed lines of code per created PR" in report
        or "LOC per created PR" in report
    )
