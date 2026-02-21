"""
Tests for CLI argument parsing and handling.
"""

import os
import sys
from datetime import datetime

import pytest
import yaml

from github_statistics.cli import RunOptions, main, parse_arguments
from github_statistics.config import Config


def test_parse_arguments_minimal():
    """Test parsing with only the required config path argument."""
    args = parse_arguments(["my_config.yaml"])

    assert args.config_path == "my_config.yaml"
    assert args.since is None
    assert args.until is None
    assert args.users is None
    assert args.repos is None
    assert args.output is None
    assert args.max_workers == 4  # default


def test_parse_arguments_with_since():
    """Test parsing with --since flag."""
    args = parse_arguments(["config.yaml", "--since", "2024-01-01"])

    assert args.config_path == "config.yaml"
    assert args.since == "2024-01-01"


def test_parse_arguments_with_until():
    """Test parsing with --until flag."""
    args = parse_arguments(["config.yaml", "--until", "2024-12-31"])

    assert args.config_path == "config.yaml"
    assert args.until == "2024-12-31"


def test_parse_arguments_with_since_and_until():
    """Test parsing with both --since and --until."""
    args = parse_arguments(
        ["config.yaml", "--since", "2024-01-01", "--until", "2024-12-31"]
    )

    assert args.since == "2024-01-01"
    assert args.until == "2024-12-31"


def test_parse_arguments_with_users():
    """Test parsing with --users flag."""
    args = parse_arguments(["config.yaml", "--users", "alice,bob,charlie"])

    assert args.users == "alice,bob,charlie"


def test_parse_arguments_with_repos():
    """Test parsing with --repos flag."""
    args = parse_arguments(["config.yaml", "--repos", "org1/repo1,org2/repo2"])

    assert args.repos == "org1/repo1,org2/repo2"


def test_parse_arguments_with_output():
    """Test parsing with --output flag."""
    args = parse_arguments(["config.yaml", "--output", "my_report.md"])

    assert args.output == "my_report.md"


def test_parse_arguments_with_max_workers():
    """Test parsing with --max-workers flag."""
    args = parse_arguments(["config.yaml", "--max-workers", "8"])

    assert args.max_workers == 8


def test_parse_arguments_all_flags():
    """Test parsing with all optional flags."""
    args = parse_arguments(
        [
            "config.yaml",
            "--since",
            "2024-01-01",
            "--until",
            "2024-12-31",
            "--users",
            "alice,bob",
            "--repos",
            "org/repo",
            "--output",
            "report.md",
            "--max-workers",
            "10",
        ]
    )

    assert args.config_path == "config.yaml"
    assert args.since == "2024-01-01"
    assert args.until == "2024-12-31"
    assert args.users == "alice,bob"
    assert args.repos == "org/repo"
    assert args.output == "report.md"
    assert args.max_workers == 10


def test_create_run_options_minimal():
    """Test creating RunOptions from config only."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1", "org/repo2"],
        users=["alice", "bob"],
    )

    args = parse_arguments(["config.yaml"])
    options = RunOptions.from_config_and_args(config, args)

    assert options.config == config
    assert options.since is None
    assert options.until is None
    assert options.repositories == ["org/repo1", "org/repo2"]  # from config
    assert options.users == ["alice", "bob"]  # from config
    # Output is now an absolute path, check basename
    assert os.path.basename(options.output) == "config_statistics.md"
    assert options.max_workers == 4


def test_create_run_options_with_date_range():
    """Test creating RunOptions with date range."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    args = parse_arguments(
        ["config.yaml", "--since", "2024-01-01", "--until", "2024-12-31"]
    )
    options = RunOptions.from_config_and_args(config, args)

    assert options.since == datetime(2024, 1, 1)
    assert options.until == datetime(2024, 12, 31)


def test_create_run_options_repos_narrows_config():
    """Test that --repos CLI flag narrows configured repositories."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1", "org/repo2", "org/repo3"],
        users=["alice"],
    )

    args = parse_arguments(["config.yaml", "--repos", "org/repo1,org/repo3"])
    options = RunOptions.from_config_and_args(config, args)

    # Only repos that are both in config AND in CLI filter
    assert options.repositories == ["org/repo1", "org/repo3"]


def test_create_run_options_repos_invalid_ignored():
    """Test that --repos with repos not in config are ignored."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1", "org/repo2"],
        users=["alice"],
    )

    args = parse_arguments(["config.yaml", "--repos", "org/repo1,org/invalid"])
    options = RunOptions.from_config_and_args(config, args)

    # Only repo1 is in both config and CLI, invalid is ignored
    assert options.repositories == ["org/repo1"]


def test_create_run_options_users_overrides_config():
    """Test that --users CLI flag overrides configured users."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice", "bob", "charlie"],
    )

    args = parse_arguments(["config.yaml", "--users", "alice,charlie"])
    options = RunOptions.from_config_and_args(config, args)

    # CLI users override config users
    assert options.users == ["alice", "charlie"]


def test_create_run_options_custom_output():
    """Test that --output CLI flag sets custom output path."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    args = parse_arguments(["config.yaml", "--output", "custom_report.md"])
    options = RunOptions.from_config_and_args(config, args)

    assert options.output == "custom_report.md"


def test_create_run_options_max_workers():
    """Test that --max-workers CLI flag is passed through."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    args = parse_arguments(["config.yaml", "--max-workers", "10"])
    options = RunOptions.from_config_and_args(config, args)

    assert options.max_workers == 10


def test_invalid_date_format_since():
    """Test that invalid --since date format raises error."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    args = parse_arguments(["config.yaml", "--since", "invalid-date"])

    with pytest.raises(ValueError, match="Invalid date format.*since"):
        RunOptions.from_config_and_args(config, args)


def test_invalid_date_format_until():
    """Test that invalid --until date format raises error."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    args = parse_arguments(["config.yaml", "--until", "not-a-date"])

    with pytest.raises(ValueError, match="Invalid date format.*until"):
        RunOptions.from_config_and_args(config, args)


def test_main_loads_config(tmp_path, monkeypatch, capsys):
    """Test that main() loads configuration using load_config."""
    from unittest.mock import MagicMock, patch

    # Create a temporary config file
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": ["org1/repo1"],
        "users": ["user1"],
    }

    config_file = tmp_path / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Mock sys.argv
    monkeypatch.setattr(sys, "argv", ["github_statistics", str(config_file)])

    # Mock the HttpGitHubClient so we don't need a real token
    with patch(
        "github_statistics.github_client.HttpGitHubClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.from_token_or_env.return_value = mock_client
        mock_client.list_pull_requests.return_value = []

        # Mock environment variable
        monkeypatch.setenv("GITHUB_TOKEN", "fake_token")

        # Run main - it should load config and complete successfully
        exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Configuration loaded" in captured.out


def test_main_with_cli_options(tmp_path, monkeypatch, capsys):
    """Test that main() handles CLI options correctly."""
    from unittest.mock import MagicMock, patch

    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": ["org1/repo1", "org1/repo2"],
        "users": ["user1", "user2"],
    }

    config_file = tmp_path / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Use custom output in tmp_path to avoid creating files in project root
    custom_output = str(tmp_path / "custom.md")

    # Mock sys.argv with options
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "github_statistics",
            str(config_file),
            "--since",
            "2024-01-01",
            "--until",
            "2024-12-31",
            "--users",
            "user1",
            "--repos",
            "org1/repo1",
            "--output",
            custom_output,
        ],
    )

    # Mock the HttpGitHubClient
    with patch(
        "github_statistics.github_client.HttpGitHubClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.from_token_or_env.return_value = mock_client
        mock_client.list_pull_requests.return_value = []

        # Mock environment variable
        monkeypatch.setenv("GITHUB_TOKEN", "fake_token")

        exit_code = main()

    assert exit_code == 0
    # Verify the output file was created in tmp_path, not current directory
    assert os.path.exists(custom_output)


def test_main_missing_config_file(monkeypatch, capsys):
    """Test that main() exits with error for missing config file."""
    monkeypatch.setattr(
        sys, "argv", ["github_statistics", "/nonexistent/config.yaml"]
    )

    exit_code = main()

    assert exit_code != 0
    captured = capsys.readouterr()
    assert (
        "error" in captured.err.lower() or "not found" in captured.err.lower()
    )


def test_main_invalid_date_exits_with_error(tmp_path, monkeypatch, capsys):
    """Test that main() exits with error for invalid date format."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": ["org1/repo1"],
        "users": ["user1"],
    }

    config_file = tmp_path / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "github_statistics",
            str(config_file),
            "--since",
            "invalid-date-format",
        ],
    )

    exit_code = main()

    assert exit_code != 0
    captured = capsys.readouterr()
    assert "date" in captured.err.lower()


def test_default_output_filename(tmp_path):
    """Test that default output filename is based on config filename."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    # Test with simple filename - output is now absolute path, check basename
    args = parse_arguments(["my_config.yaml"])
    options = RunOptions.from_config_and_args(config, args)
    assert os.path.basename(options.output) == "my_config_statistics.md"

    # Test with path - output should be in same directory as input
    args = parse_arguments(["/path/to/project_config.yaml"])
    options = RunOptions.from_config_and_args(config, args)
    assert os.path.basename(options.output) == "project_config_statistics.md"
    assert os.path.dirname(options.output) == "/path/to"

    # Test with .yml extension
    args = parse_arguments(["config.yml"])
    options = RunOptions.from_config_and_args(config, args)
    assert os.path.basename(options.output) == "config_statistics.md"


def test_run_options_dataclass():
    """Test that RunOptions can be instantiated directly."""
    config = Config(
        github_base_url="https://github.com/api/v3",
        github_token_env="GITHUB_TOKEN",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=["alice"],
    )

    options = RunOptions(
        config=config,
        since=datetime(2024, 1, 1),
        until=datetime(2024, 12, 31),
        repositories=["org/repo1"],
        users=["alice"],
        output="report.md",
        max_workers=8,
    )

    assert options.config == config
    assert options.since == datetime(2024, 1, 1)
    assert options.until == datetime(2024, 12, 31)
    assert options.repositories == ["org/repo1"]
    assert options.users == ["alice"]
    assert options.output == "report.md"
    assert options.max_workers == 8
