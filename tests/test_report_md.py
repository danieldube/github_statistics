"""Tests for Markdown report generation with group-only output."""

from datetime import datetime, timezone

from github_statistics.cli import RunOptions
from github_statistics.config import Config
from github_statistics.report_md import render_report
from github_statistics.stats import Distribution, GroupStats, RepositoryStats


def _base_options():
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=[],
        user_groups={
            "team_alpha": ["alice", "bob", "carol", "dave", "erin"],
        },
    )
    return RunOptions(
        config=config,
        since=datetime(2026, 1, 1, tzinfo=timezone.utc),
        until=datetime(2026, 2, 1, tzinfo=timezone.utc),
        repositories=["org/repo1"],
        users=[],
        output="test.md",
        max_workers=4,
    )


def _repo_stats():
    return {
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


def _group_stats():
    return {
        "team_alpha": GroupStats(
            member_count=5,
            active_member_count=5,
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


def test_render_report_basic_structure_group_only():
    """Report has repositories and groups, not per-user sections."""
    report = render_report(_repo_stats(), _group_stats(), _base_options())

    assert "# GitHub Statistics Report" in report
    assert "## Repositories" in report
    assert "## Groups" in report
    assert "### team_alpha" in report
    assert "### alice" not in report
    assert "## Users" not in report


def test_render_report_includes_active_member_count():
    """Group section includes active-member count."""
    report = render_report(_repo_stats(), _group_stats(), _base_options())

    assert "**Active members:** 5 / 5" in report


def test_render_report_handles_empty_group_stats():
    """Empty group stats are rendered gracefully."""
    report = render_report(_repo_stats(), {}, _base_options())

    assert "No group statistics available." in report


def test_render_report_override_annotation():
    """Override path shows a visible warning block."""
    options = _base_options()
    options.data_protection_override_used = True
    report = render_report(_repo_stats(), _group_stats(), options)

    assert "WARNING" in report
    assert "data-protection override" in report.lower()
