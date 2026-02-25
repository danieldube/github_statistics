"""
Command-line interface for github_statistics.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from github_statistics.config import Config, ConfigValidationError, load_config


@dataclass
class RunOptions:
    """
    Runtime options combining configuration and CLI arguments.

    Attributes:
        config: The loaded configuration.
        since: Optional start date for filtering PRs.
        until: Optional end date for filtering PRs.
        repositories: List of repositories to analyze (after CLI filtering).
        users: List of users to analyze (after CLI filtering/override).
        output: Path to the output Markdown file.
        max_workers: Maximum number of concurrent workers.
        verbose: Whether verbose request logging is enabled.
        request_log_path: Path to the request log file if verbose is enabled.
        overwrite_data_protection: Whether override flag is set.
        data_protection_override_used: Whether override was confirmed and used.
    """

    config: Config
    since: Optional[datetime]
    until: Optional[datetime]
    repositories: List[str]
    users: List[str]
    output: str
    max_workers: int
    verbose: bool = False
    request_log_path: Optional[str] = None
    overwrite_data_protection: bool = False
    data_protection_override_used: bool = False

    @staticmethod
    def _parse_cli_datetime(value: str, flag_name: str) -> datetime:
        """Parse CLI datetime and normalize to timezone-aware UTC."""
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as e:
            raise ValueError(
                f"Invalid date format for {flag_name}: '{value}'. Expected ISO format (YYYY-MM-DD)."
            ) from e

        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    @staticmethod
    def from_config_and_args(config: Config, args) -> "RunOptions":
        """
        Create RunOptions from a Config object and parsed CLI arguments.

        Args:
            config: Loaded configuration.
            args: Parsed command-line arguments from argparse.

        Returns:
            RunOptions instance.

        Raises:
            ValueError: If date formats are invalid.
        """
        # Parse date arguments
        since = None
        until = None

        if args.since:
            since = RunOptions._parse_cli_datetime(args.since, "--since")

        if args.until:
            until = RunOptions._parse_cli_datetime(args.until, "--until")

        # Handle repository filtering
        # CLI --repos narrows the config repositories (intersection)
        repositories = config.repositories
        if args.repos:
            cli_repos = [repo.strip() for repo in args.repos.split(",")]
            # Keep only repos that are in both config and CLI filter
            repositories = [
                repo for repo in config.repositories if repo in cli_repos
            ]

        # Handle user filtering
        # CLI --users overrides config users
        users = config.users
        if args.users:
            users = [user.strip() for user in args.users.split(",")]

        # Determine output filename
        config_dir = os.path.dirname(os.path.abspath(args.config_path))
        config_basename = os.path.splitext(os.path.basename(args.config_path))[
            0
        ]
        output = args.output
        if output is None:
            # Default: <config_basename>_statistics.md in same dir as config
            output = os.path.join(
                config_dir, f"{config_basename}_statistics.md"
            )
        verbose = args.verbose
        request_log_path = None
        if verbose:
            request_log_path = os.path.join(
                config_dir, f"{config_basename}_requests.log"
            )
        overwrite_data_protection = args.overwrite_data_protection

        return RunOptions(
            config=config,
            since=since,
            until=until,
            repositories=repositories,
            users=users,
            output=output,
            max_workers=args.max_workers,
            verbose=verbose,
            request_log_path=request_log_path,
            overwrite_data_protection=overwrite_data_protection,
        )


def parse_arguments(args: List[str]):
    """
    Parse command-line arguments.

    Args:
        args: List of argument strings (typically sys.argv[1:]).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="github_statistics",
        description="Compute pull request statistics from GitHub Enterprise.",
    )

    parser.add_argument(
        "config_path", help="Path to the YAML configuration file"
    )

    parser.add_argument(
        "--since",
        help="Start date for PR filtering (ISO format: YYYY-MM-DD)",
        default=None,
    )

    parser.add_argument(
        "--until",
        help="End date for PR filtering (ISO format: YYYY-MM-DD)",
        default=None,
    )

    parser.add_argument(
        "--users",
        help="Comma-separated list of users to analyze (overrides config)",
        default=None,
    )

    parser.add_argument(
        "--repos",
        help="Comma-separated list of repositories to analyze (narrows config)",
        default=None,
    )

    parser.add_argument(
        "--output",
        help="Path to output Markdown file (default: <config_basename>_statistics.md)",
        default=None,
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Maximum number of concurrent workers (default: 4)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log all GitHub API requests to <config_basename>_requests.log",
    )
    parser.add_argument(
        "--overwrite-data-protection",
        action="store_true",
        help=(
            "Override data-protection threshold blocking (requires explicit "
            "interactive confirmation)"
        ),
    )

    return parser.parse_args(args)


def main():
    """Entry point for the github_statistics CLI.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    try:
        # Parse command-line arguments
        args = parse_arguments(sys.argv[1:])

        # Load configuration
        try:
            config = load_config(args.config_path)
        except FileNotFoundError:
            print(
                f"Error: Configuration file not found: {args.config_path}",
                file=sys.stderr,
            )
            return 1
        except ConfigValidationError as e:
            print(
                f"Error: Configuration validation failed: {e}", file=sys.stderr
            )
            return 1

        # Create runtime options
        try:
            options = RunOptions.from_config_and_args(config, args)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        # Print progress
        print("Configuration loaded successfully.")
        print(f"  Repositories: {len(options.repositories)}")
        print(f"  Groups: {len(config.user_groups)}")
        if options.since:
            print(f"  Since: {options.since.date()}")
        if options.until:
            print(f"  Until: {options.until.date()}")
        print(f"  Output: {options.output}")
        print(f"  Max workers: {options.max_workers}")
        if options.verbose and options.request_log_path:
            print(f"  Request log: {options.request_log_path}")
        print()

        # Import modules (deferred to avoid import errors in early steps)
        from github_statistics.collector import collect_prs
        from github_statistics.github_client import HttpGitHubClient
        from github_statistics.report_md import render_report
        from github_statistics.stats import (
            compute_group_stats,
            compute_repository_stats,
            evaluate_data_protection_thresholds,
        )

        # Instantiate GitHub client
        print("Initializing GitHub client...")
        try:
            if config.github_api_token:
                client = HttpGitHubClient(
                    base_url=config.github_base_url,
                    token=config.github_api_token,
                    verify_ssl=config.github_verify_ssl,
                    request_log_path=options.request_log_path,
                )
            else:
                client = HttpGitHubClient.from_env(
                    base_url=config.github_base_url,
                    token_env=config.github_token_env,
                    verify_ssl=config.github_verify_ssl,
                    request_log_path=options.request_log_path,
                )
        except ValueError as e:
            print(
                f"Error: Failed to initialize GitHub client: {e}",
                file=sys.stderr,
            )
            return 1

        # Collect pull requests
        print("Collecting pull requests...")
        try:
            pull_requests = collect_prs(config, options, client)
            print(f"  Collected {len(pull_requests)} pull requests")
        except Exception as e:
            print(
                f"Error: Failed to collect pull requests: {e}",
                file=sys.stderr,
            )
            return 1

        # Enforce data-protection policy
        data_protection_result = evaluate_data_protection_thresholds(
            pull_requests=pull_requests,
            user_groups=config.user_groups,
            repositories=options.repositories,
            since=options.since,
            until=options.until,
        )
        if not data_protection_result.passed:
            print("Data protection threshold violations detected:")
            for violation in data_protection_result.violations:
                print(f"  - {violation.message}")

            if not options.overwrite_data_protection:
                print(
                    "Error: Data protection policy blocked output. "
                    "Re-run with --overwrite-data-protection to request "
                    "explicit override.",
                    file=sys.stderr,
                )
                return 1

            print(
                "DISCLAIMER: You are overriding mandatory data-protection "
                "thresholds. Output may reveal sensitive information."
            )
            confirmation = input("Type 'y' to continue: ").strip().lower()
            if confirmation != "y":
                print(
                    "Error: Data protection override was not confirmed.",
                    file=sys.stderr,
                )
                return 1

            options.data_protection_override_used = True

        # Compute statistics
        print("Computing statistics...")
        try:
            # Compute repository-level stats
            # For simplicity, compute stats for all PRs together
            # (PRs don't carry repo info, so we compute for all repos combined)
            repos_stats = {}
            repo_stats = compute_repository_stats(
                pull_requests, until=options.until
            )

            # Store with a key - if multiple repos, we could iterate
            # For now, store as "All repositories" or per repo if needed
            if len(options.repositories) == 1:
                repos_stats[options.repositories[0]] = repo_stats
            else:
                repos_stats["All repositories"] = repo_stats

            group_stats = compute_group_stats(
                pull_requests=pull_requests,
                user_groups=config.user_groups,
                active_group_counts=data_protection_result.group_active_counts,
            )
            print(
                f"  Computed stats for {len(repos_stats)} repository group(s)"
            )
            print(f"  Computed stats for {len(group_stats)} group(s)")
        except Exception as e:
            print(f"Error: Failed to compute statistics: {e}", file=sys.stderr)
            return 1

        # Generate report
        print("Generating report...")
        try:
            report = render_report(repos_stats, group_stats, options)
        except Exception as e:
            print(f"Error: Failed to generate report: {e}", file=sys.stderr)
            return 1

        # Write report to file
        print(f"Writing report to {options.output}...")
        try:
            with open(options.output, "w") as f:
                f.write(report)
            print(f"Report successfully written to {options.output}")
        except Exception as e:
            print(f"Error: Failed to write report: {e}", file=sys.stderr)
            return 1

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
