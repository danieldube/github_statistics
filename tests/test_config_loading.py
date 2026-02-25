"""Tests for configuration loading and validation."""

import os
import tempfile

import pytest
import yaml

from github_statistics.config import Config, ConfigValidationError, load_config


def _valid_groups():
    return {
        "team_alpha": ["alice", "bob", "carol", "dave", "erin"],
    }


def test_load_minimal_valid_config():
    """Test loading a minimal valid configuration."""
    config_data = {
        "github": {"base_url": "https://github.mycompany.com/api/v3"},
        "repositories": ["org1/repo1"],
        "user_groups": _valid_groups(),
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.github_base_url == "https://github.mycompany.com/api/v3"
        assert config.github_api_token is None
        assert config.github_token_env == "GITHUB_TOKEN"
        assert config.github_verify_ssl is True
        assert config.repositories == ["org1/repo1"]
        assert config.user_groups == _valid_groups()
    finally:
        os.unlink(config_path)


def test_load_config_with_all_fields():
    """Test loading a configuration with all optional fields set."""
    config_data = {
        "github": {
            "base_url": "https://github.example.com/api/v3",
            "api_token": "my-direct-token",
            "token_env": "MY_GITHUB_TOKEN",
            "verify_ssl": False,
        },
        "repositories": ["owner1/repo1", "owner2/repo2"],
        "user_groups": {
            "team_alpha": ["alice", "bob", "carol", "dave", "erin"],
            "team_beta": ["frank", "grace", "heidi", "ivan", "judy"],
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.github_base_url == "https://github.example.com/api/v3"
        assert config.github_api_token == "my-direct-token"
        assert config.github_token_env == "MY_GITHUB_TOKEN"
        assert config.github_verify_ssl is False
        assert config.repositories == ["owner1/repo1", "owner2/repo2"]
        assert sorted(config.user_groups.keys()) == ["team_alpha", "team_beta"]
    finally:
        os.unlink(config_path)


def test_normalize_repository_formats():
    """Test repository normalization for mixed URL formats."""
    config_data = {
        "github": {"base_url": "https://github.mycompany.com/api/v3"},
        "repositories": [
            "org1/repo1",
            "https://github.mycompany.com/org2/repo2/",
            "git@github.mycompany.com:org3/repo3.git",
        ],
        "user_groups": _valid_groups(),
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)
        assert config.repositories == [
            "org1/repo1",
            "org2/repo2",
            "org3/repo3",
        ]
    finally:
        os.unlink(config_path)


def test_missing_user_groups_raises_error():
    """Test that missing user_groups fails validation."""
    config_data = {
        "github": {"base_url": "https://api.github.com"},
        "repositories": ["org/repo"],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ConfigValidationError, match="user_groups"):
            load_config(config_path)
    finally:
        os.unlink(config_path)


def test_group_with_less_than_five_members_fails():
    """Test that a group with less than 5 users is rejected."""
    config_data = {
        "github": {"base_url": "https://api.github.com"},
        "repositories": ["org/repo"],
        "user_groups": {"small_team": ["a", "b", "c", "d"]},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ConfigValidationError, match="at least 5"):
            load_config(config_path)
    finally:
        os.unlink(config_path)


def test_group_with_duplicate_members_fails():
    """Test that duplicate members in a group are rejected."""
    config_data = {
        "github": {"base_url": "https://api.github.com"},
        "repositories": ["org/repo"],
        "user_groups": {
            "team_alpha": ["alice", "alice", "carol", "dave", "erin"]
        },
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ConfigValidationError, match="duplicate"):
            load_config(config_path)
    finally:
        os.unlink(config_path)


def test_empty_group_name_fails():
    """Test that empty group names are rejected."""
    config_data = {
        "github": {"base_url": "https://api.github.com"},
        "repositories": ["org/repo"],
        "user_groups": {"": ["alice", "bob", "carol", "dave", "erin"]},
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ConfigValidationError, match="group name"):
            load_config(config_path)
    finally:
        os.unlink(config_path)


def test_missing_base_url_raises_error():
    """Test that missing github.base_url raises a validation error."""
    config_data = {
        "github": {},
        "repositories": ["org1/repo1"],
        "user_groups": _valid_groups(),
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ConfigValidationError, match="base_url.*required"):
            load_config(config_path)
    finally:
        os.unlink(config_path)


def test_missing_repositories_raises_error():
    """Test that missing repositories field raises a validation error."""
    config_data = {
        "github": {"base_url": "https://github.mycompany.com/api/v3"},
        "user_groups": _valid_groups(),
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(
            ConfigValidationError, match="repositories.*required"
        ):
            load_config(config_path)
    finally:
        os.unlink(config_path)


def test_empty_repositories_raises_error():
    """Test that an empty repositories list raises a validation error."""
    config_data = {
        "github": {"base_url": "https://github.mycompany.com/api/v3"},
        "repositories": [],
        "user_groups": _valid_groups(),
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ConfigValidationError, match="repositories.*empty"):
            load_config(config_path)
    finally:
        os.unlink(config_path)


def test_config_dataclass_instantiation():
    """Test that Config dataclass can be instantiated directly."""
    config = Config(
        github_base_url="https://api.github.com",
        github_api_token="direct-token",
        github_token_env="TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=["legacy-user"],
        user_groups=_valid_groups(),
    )

    assert config.github_base_url == "https://api.github.com"
    assert config.github_api_token == "direct-token"
    assert config.github_token_env == "TOKEN"
    assert config.user_groups == _valid_groups()


def test_file_not_found():
    """Test that attempting to load a non-existent file raises an error."""
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/to/config.yaml")


def test_invalid_yaml():
    """Test that invalid YAML syntax raises an error."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write("invalid: yaml: content: [unclosed")
        config_path = f.name

    try:
        with pytest.raises(yaml.YAMLError):
            load_config(config_path)
    finally:
        os.unlink(config_path)
