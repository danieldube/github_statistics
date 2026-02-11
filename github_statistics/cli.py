"""
Command-line interface for github_statistics.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import datetime
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
    """

    config: Config
    since: Optional[datetime]
    until: Optional[datetime]
    repositories: List[str]
    users: List[str]
    output: str
    max_workers: int

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
            try:
                since = datetime.fromisoformat(args.since)
            except ValueError as e:
                raise ValueError(
                    f"Invalid date format for --since: '{args.since}'. Expected ISO format (YYYY-MM-DD)."
                ) from e

        if args.until:
            try:
                until = datetime.fromisoformat(args.until)
            except ValueError as e:
                raise ValueError(
                    f"Invalid date format for --until: '{args.until}'. Expected ISO format (YYYY-MM-DD)."
                ) from e

        # Handle repository filtering
        # CLI --repos narrows the config repositories (intersection)
        repositories = config.repositories
        if args.repos:
            cli_repos = [repo.strip() for repo in args.repos.split(",")]
            # Keep only repos that are in both config and CLI filter
            repositories = [repo for repo in config.repositories if repo in cli_repos]

        # Handle user filtering
        # CLI --users overrides config users
        users = config.users
        if args.users:
            users = [user.strip() for user in args.users.split(",")]

        # Determine output filename
        output = args.output
        if output is None:
            # Default: <config_basename>_statistics.md
            config_basename = os.path.splitext(os.path.basename(args.config_path))[0]
            output = f"{config_basename}_statistics.md"

        return RunOptions(
            config=config,
            since=since,
            until=until,
            repositories=repositories,
            users=users,
            output=output,
            max_workers=args.max_workers,
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

    parser.add_argument("config_path", help="Path to the YAML configuration file")

    parser.add_argument(
        "--since", help="Start date for PR filtering (ISO format: YYYY-MM-DD)", default=None
    )

    parser.add_argument(
        "--until", help="End date for PR filtering (ISO format: YYYY-MM-DD)", default=None
    )

    parser.add_argument(
        "--users", help="Comma-separated list of users to analyze (overrides config)", default=None
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
            print(f"Error: Configuration file not found: {args.config_path}", file=sys.stderr)
            return 1
        except ConfigValidationError as e:
            print(f"Error: Configuration validation failed: {e}", file=sys.stderr)
            return 1

        # Create runtime options
        try:
            options = RunOptions.from_config_and_args(config, args)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        # Print confirmation (actual execution will be implemented in later steps)
        print("Configuration loaded successfully.")
        print(f"  Repositories: {len(options.repositories)}")
        print(f"  Users: {len(options.users)}")
        if options.since:
            print(f"  Since: {options.since.date()}")
        if options.until:
            print(f"  Until: {options.until.date()}")
        print(f"  Output: {options.output}")
        print(f"  Max workers: {options.max_workers}")
        print("\nData collection and analysis not yet fully implemented.")
        print("This functionality will be added in subsequent steps.")

        return 0

    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
