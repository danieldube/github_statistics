"""
Markdown report generation.

This module generates formatted Markdown reports from computed statistics.
"""

from typing import Dict

from github_statistics.stats import Distribution, RepositoryStats, UserStats


def _format_number(value: float, decimals: int = 2) -> str:
    """Format a number with specified decimal places.

    Args:
        value: Number to format.
        decimals: Number of decimal places (default: 2).

    Returns:
        Formatted string.
    """
    return f"{value:.{decimals}f}"


def _format_distribution(dist: Distribution, unit: str = "") -> str:
    """Format a distribution for display.

    Args:
        dist: Distribution object.
        unit: Optional unit to append (e.g., "days", "hours").

    Returns:
        Formatted string showing distribution statistics.
    """
    if dist.count == 0:
        return "no data"

    unit_str = f" {unit}" if unit else ""
    return (
        f"count: {dist.count}, "
        f"min: {_format_number(dist.minimum)}{unit_str}, "
        f"median: {_format_number(dist.median)}{unit_str}, "
        f"mean: {_format_number(dist.mean)}{unit_str}, "
        f"max: {_format_number(dist.maximum)}{unit_str}"
    )


def _format_percentage(value: float) -> str:
    """Format a percentage value.

    Args:
        value: Percentage value (0-100).

    Returns:
        Formatted percentage string.
    """
    return f"{_format_number(value)}%"


def render_report(
    repos_stats: Dict[str, RepositoryStats],
    users_stats: Dict[str, UserStats],
    options,
) -> str:
    """Generate a Markdown report from statistics.

    Args:
        repos_stats: Dictionary mapping repository name to RepositoryStats.
        users_stats: Dictionary mapping username to UserStats.
        options: Runtime options containing metadata (since, until, etc.).

    Returns:
        Markdown string containing formatted report.
    """
    lines = []

    # Title
    lines.append("# GitHub Statistics Report")
    lines.append("")

    # Metadata section
    lines.append("## Metadata")
    lines.append("")

    if options.since:
        lines.append(f"- **Time range start:** {options.since.date()}")
    else:
        lines.append("- **Time range start:** (no filter)")

    if options.until:
        lines.append(f"- **Time range end:** {options.until.date()}")
    else:
        lines.append("- **Time range end:** (no filter)")

    lines.append(f"- **Repositories analyzed:** {len(options.repositories)}")
    lines.append(f"- **Users analyzed:** {len(options.users)}")
    lines.append("")

    # Repositories section
    lines.append("## Repositories")
    lines.append("")

    if not repos_stats:
        lines.append("No repository statistics available.")
        lines.append("")
    else:
        # Sort repositories alphabetically for deterministic output
        for repo_name in sorted(repos_stats.keys()):
            stats = repos_stats[repo_name]
            lines.append(f"### {repo_name}")
            lines.append("")

            # Duration metrics
            lines.append(
                f"- **Duration open pull requests (days):** "
                f"{_format_distribution(stats.open_pr_duration)}"
            )
            lines.append(
                f"- **Duration closed pull requests (days):** "
                f"{_format_distribution(stats.closed_pr_duration)}"
            )
            lines.append(
                f"- **Duration merged pull requests (days):** "
                f"{_format_distribution(stats.merged_pr_duration)}"
            )

            # Review timing
            lines.append(
                f"- **Time to first review (days):** "
                f"{_format_distribution(stats.time_to_first_review)}"
            )
            lines.append(
                f"- **Time between changes requested and re-request (days):** "
                f"{_format_distribution(stats.time_between_changes_requested_and_re_request)}"
            )

            # Activity metrics
            lines.append(
                f"- **Commits per PR:** "
                f"{_format_distribution(stats.commits_per_pr)}"
            )
            lines.append(
                f"- **Re-reviews per PR:** "
                f"{_format_distribution(stats.re_reviews_per_pr)}"
            )
            lines.append(
                f"- **Comments per 100 LOC:** "
                f"{_format_distribution(stats.comments_per_100_loc)}"
            )
            lines.append("")

    # Users section
    lines.append("## Users")
    lines.append("")

    if not users_stats:
        lines.append("No user statistics available.")
        lines.append("")
    else:
        # Sort users alphabetically for deterministic output
        for username in sorted(users_stats.keys()):
            user_stat: UserStats = users_stats[username]
            lines.append(f"### {username}")
            lines.append("")

            # Review timing
            lines.append(
                f"- **Time between requested and submitting review (hours):** "
                f"{_format_distribution(user_stat.time_to_submit_review)}"
            )

            # Approval rates
            lines.append(
                f"- **Request for changes rate:** "
                f"{_format_percentage(user_stat.changes_requested_rate)}"
            )
            lines.append(
                f"- **Direct approval rate:** "
                f"{_format_percentage(user_stat.direct_approval_rate)}"
            )

            # Code metrics
            lines.append(
                f"- **Changed lines of code per created PR:** "
                f"{_format_distribution(user_stat.loc_per_created_pr)}"
            )
            lines.append(
                f"- **Comments per 100 LOC (as reviewer):** "
                f"{_format_distribution(user_stat.comments_per_100_loc_as_reviewer)}"
            )
            lines.append(
                f"- **Comments per 100 LOC (as author):** "
                f"{_format_distribution(user_stat.comments_per_100_loc_as_author)}"
            )
            lines.append("")

    return "\n".join(lines)
