"""
Tests for configuration loading and validation.
"""

import os
import tempfile

import pytest
import yaml

from github_statistics.config import Config, ConfigValidationError, load_config


def test_load_minimal_valid_config():
    """Test loading a minimal valid configuration."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": [
            "org1/repo1",
        ],
        "users": [
            "user1",
        ],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.github_base_url == "https://github.mycompany.com/api/v3"
        assert config.github_token_env == "GITHUB_TOKEN"  # default
        assert config.github_verify_ssl is True  # default
        assert config.repositories == ["org1/repo1"]
        assert config.users == ["user1"]
    finally:
        os.unlink(config_path)


def test_load_config_with_all_fields():
    """Test loading a configuration with all fields explicitly set."""
    config_data = {
        "github": {
            "base_url": "https://github.example.com/api/v3",
            "token_env": "MY_GITHUB_TOKEN",
            "verify_ssl": False,
        },
        "repositories": [
            "owner1/repo1",
            "owner2/repo2",
        ],
        "users": [
            "alice",
            "bob",
        ],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.github_base_url == "https://github.example.com/api/v3"
        assert config.github_token_env == "MY_GITHUB_TOKEN"
        assert config.github_verify_ssl is False
        assert config.repositories == ["owner1/repo1", "owner2/repo2"]
        assert config.users == ["alice", "bob"]
    finally:
        os.unlink(config_path)


def test_normalize_repository_url_https():
    """Test that HTTPS repository URLs are normalized to owner/repo."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": [
            "https://github.mycompany.com/org1/repo1",
            "https://github.mycompany.com/org2/repo2/",  # trailing slash
        ],
        "users": ["user1"],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.repositories == ["org1/repo1", "org2/repo2"]
    finally:
        os.unlink(config_path)


def test_normalize_repository_url_git():
    """Test that git@ style URLs are normalized to owner/repo."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": [
            "git@github.mycompany.com:org1/repo1.git",
        ],
        "users": ["user1"],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.repositories == ["org1/repo1"]
    finally:
        os.unlink(config_path)


def test_normalize_repository_mixed_formats():
    """Test that mixed repository formats are all normalized."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": [
            "org1/repo1",  # already normalized
            "https://github.mycompany.com/org2/repo2",  # HTTPS URL
            "git@github.mycompany.com:org3/repo3.git",  # SSH URL
        ],
        "users": ["user1"],
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


def test_users_list_loaded_as_is():
    """Test that the users list is loaded without modification."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": ["org1/repo1"],
        "users": [
            "alice123",
            "bob-456",
            "charlie_789",
        ],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.users == ["alice123", "bob-456", "charlie_789"]
    finally:
        os.unlink(config_path)


def test_default_token_env():
    """Test that token_env defaults to GITHUB_TOKEN when not specified."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": ["org1/repo1"],
        "users": ["user1"],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.github_token_env == "GITHUB_TOKEN"
    finally:
        os.unlink(config_path)


def test_default_verify_ssl():
    """Test that verify_ssl defaults to True when not specified."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": ["org1/repo1"],
        "users": ["user1"],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.github_verify_ssl is True
    finally:
        os.unlink(config_path)


def test_missing_base_url_raises_error():
    """Test that missing github.base_url raises a validation error."""
    config_data = {
        "github": {
            # base_url missing
            "token_env": "GITHUB_TOKEN",
        },
        "repositories": ["org1/repo1"],
        "users": ["user1"],
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


def test_missing_github_section_raises_error():
    """Test that missing github section raises a validation error."""
    config_data = {
        # github section missing
        "repositories": ["org1/repo1"],
        "users": ["user1"],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        with pytest.raises(ConfigValidationError, match="github.*required"):
            load_config(config_path)
    finally:
        os.unlink(config_path)


def test_empty_repositories_raises_error():
    """Test that an empty repositories list raises a validation error."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": [],  # empty
        "users": ["user1"],
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


def test_missing_repositories_raises_error():
    """Test that missing repositories field raises a validation error."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        # repositories missing
        "users": ["user1"],
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


def test_empty_users_allowed():
    """Test that an empty users list is allowed (optional field)."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": ["org1/repo1"],
        "users": [],  # empty is OK
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.users == []
    finally:
        os.unlink(config_path)


def test_missing_users_defaults_to_empty():
    """Test that missing users field defaults to an empty list."""
    config_data = {
        "github": {
            "base_url": "https://github.mycompany.com/api/v3",
        },
        "repositories": ["org1/repo1"],
        # users missing
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config.users == []
    finally:
        os.unlink(config_path)


def test_config_dataclass_instantiation():
    """Test that Config dataclass can be instantiated directly."""
    config = Config(
        github_base_url="https://api.github.com",
        github_token_env="TOKEN",
        github_verify_ssl=True,
        repositories=["owner/repo"],
        users=["user1"],
    )

    assert config.github_base_url == "https://api.github.com"
    assert config.github_token_env == "TOKEN"
    assert config.github_verify_ssl is True
    assert config.repositories == ["owner/repo"]
    assert config.users == ["user1"]


def test_file_not_found():
    """Test that attempting to load a non-existent file raises an appropriate error."""
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/to/config.yaml")


def test_invalid_yaml():
    """Test that invalid YAML syntax raises an appropriate error."""
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
