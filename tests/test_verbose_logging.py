"""Tests for verbose request logging."""

import os
import sys
from unittest.mock import MagicMock, patch

import responses
import yaml

from github_statistics.cli import RunOptions, main, parse_arguments
from github_statistics.config import Config
from github_statistics.github_client import HttpGitHubClient


def test_parse_arguments_with_verbose():
    """Test parsing with --verbose flag."""
    args = parse_arguments(["config.yaml", "--verbose"])

    assert args.verbose is True


def test_run_options_verbose_generates_default_request_log_path(tmp_path):
    """Test that verbose mode generates a default request log path."""
    config = Config(
        github_base_url="https://api.github.com",
        github_verify_ssl=True,
        repositories=["org/repo1"],
        users=[],
    )
    config_file = tmp_path / "my_config.yaml"
    config_file.write_text("github: {}\nrepositories: []\n")

    args = parse_arguments([str(config_file), "--verbose"])
    options = RunOptions.from_config_and_args(config, args)

    assert options.verbose is True
    assert options.request_log_path == str(tmp_path / "my_config_requests.log")


def test_main_with_verbose_passes_request_log_path(tmp_path, monkeypatch):
    """Test that main() passes request_log_path to HttpGitHubClient."""
    config_data = {
        "github": {
            "base_url": "https://api.github.com",
            "api_token": "test-token",
        },
        "repositories": ["org/repo1"],
        "users": [],
    }
    config_file = tmp_path / "verbose_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    monkeypatch.setattr(
        sys,
        "argv",
        ["github_statistics", str(config_file), "--verbose"],
    )

    with patch(
        "github_statistics.github_client.HttpGitHubClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.list_pull_requests.return_value = []

        exit_code = main()

    assert exit_code == 0
    _, kwargs = mock_client_class.call_args
    assert kwargs["request_log_path"] == str(
        tmp_path / "verbose_config_requests.log"
    )


@responses.activate
def test_http_client_request_logging_writes_requests_only(tmp_path):
    """Test that request logging writes request lines but not responses."""
    responses.add(
        responses.GET,
        "https://api.github.com/repos/owner/repo/pulls",
        json=[
            {
                "number": 1,
                "title": "Response title should not be logged",
            }
        ],
        status=200,
    )

    log_path = tmp_path / "requests.log"
    client = HttpGitHubClient(
        base_url="https://api.github.com",
        token="test-token",
        verify_ssl=True,
        request_log_path=str(log_path),
    )

    prs = client.list_pull_requests("owner", "repo")
    assert len(prs) == 1

    assert os.path.exists(log_path)
    log_content = log_path.read_text()
    assert "GET https://api.github.com/repos/owner/repo/pulls?state=all" in (
        log_content
    )
    assert "Response title should not be logged" not in log_content
