"""
Configuration loading and validation.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails."""

    pass


@dataclass
class Config:
    """
    Configuration for github_statistics.

    Attributes:
        github_base_url: Base URL for the GitHub API (e.g., https://github.com/api/v3).
        github_api_token: Directly configured GitHub API token (optional).
        github_token_env: Name of the environment variable containing the GitHub token.
        github_verify_ssl: Whether to verify SSL certificates.
        repositories: List of repository identifiers in owner/repo format.
        users: Legacy users list (deprecated by group-based reporting).
        user_groups: Named user groups for aggregation and data-protection checks.
    """

    github_base_url: str
    github_verify_ssl: bool
    repositories: List[str]
    users: List[str]
    user_groups: Dict[str, List[str]] = field(default_factory=dict)
    github_api_token: Optional[str] = None
    github_token_env: str = "GITHUB_TOKEN"


def normalize_repository(repo_identifier: str) -> str:
    """
    Normalize a repository identifier to owner/repo format.

    Handles:
    - owner/repo (already normalized)
    - https://github.com/owner/repo
    - https://github.com/owner/repo/
    - git@github.com:owner/repo.git

    Args:
        repo_identifier: Repository URL or owner/repo string.

    Returns:
        Normalized owner/repo string.
    """
    # Remove trailing slashes
    repo_identifier = repo_identifier.rstrip("/")

    # Handle git@ style URLs: git@github.com:owner/repo.git
    git_match = re.match(r"^git@[^:]+:(.+?)(?:\.git)?$", repo_identifier)
    if git_match:
        return git_match.group(1)

    # Handle HTTPS URLs: https://github.com/owner/repo
    https_match = re.match(
        r"^https?://[^/]+/(.+?)(?:\.git)?$", repo_identifier
    )
    if https_match:
        return https_match.group(1)

    # Already in owner/repo format
    return repo_identifier


def load_config(path: str) -> Config:
    """Load configuration from a YAML file.

    Args:
        path: Path to the configuration YAML file.

    Returns:
        Config object with validated and normalized data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the YAML syntax is invalid.
        ConfigValidationError: If required fields are missing or invalid.
    """
    # Read and parse YAML
    with open(path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ConfigValidationError(
            "Configuration file must contain a YAML dictionary"
        )

    # Validate github section
    if "github" not in data:
        raise ConfigValidationError(
            "Configuration must contain 'github' section (required)"
        )

    github_config = data["github"]
    if not isinstance(github_config, dict):
        raise ConfigValidationError("'github' section must be a dictionary")

    # Validate and extract github.base_url
    if "base_url" not in github_config:
        raise ConfigValidationError("github.base_url is required")

    github_base_url = github_config["base_url"]

    # Apply defaults for optional github fields
    github_api_token = github_config.get("api_token")
    github_token_env = github_config.get("token_env", "GITHUB_TOKEN")
    github_verify_ssl = github_config.get("verify_ssl", True)

    # Validate repositories
    if "repositories" not in data:
        raise ConfigValidationError(
            "Configuration must contain 'repositories' field (required)"
        )

    repositories = data["repositories"]
    if not isinstance(repositories, list):
        raise ConfigValidationError("'repositories' must be a list")

    if len(repositories) == 0:
        raise ConfigValidationError("'repositories' list cannot be empty")

    # Normalize repository identifiers
    normalized_repos = [normalize_repository(repo) for repo in repositories]

    # Handle users (legacy optional list)
    users = data.get("users", [])
    if not isinstance(users, list):
        raise ConfigValidationError("'users' must be a list")

    # Handle user groups (mandatory for data-protection policy)
    if "user_groups" not in data:
        raise ConfigValidationError("'user_groups' is required")

    user_groups = data["user_groups"]
    if not isinstance(user_groups, dict):
        raise ConfigValidationError("'user_groups' must be a dictionary")

    if len(user_groups) == 0:
        raise ConfigValidationError("'user_groups' cannot be empty")

    validated_groups: Dict[str, List[str]] = {}
    for group_name, members in user_groups.items():
        if not isinstance(group_name, str) or not group_name.strip():
            raise ConfigValidationError(
                "Each user group name must be a non-empty string"
            )
        if not isinstance(members, list):
            raise ConfigValidationError(
                f"Group '{group_name}' must contain a list of members"
            )
        if len(members) < 5:
            raise ConfigValidationError(
                f"Group '{group_name}' must contain at least 5 members"
            )
        if len(set(members)) != len(members):
            raise ConfigValidationError(
                f"Group '{group_name}' contains duplicate members"
            )
        if any(
            not isinstance(member, str) or not member.strip()
            for member in members
        ):
            raise ConfigValidationError(
                f"Group '{group_name}' contains invalid member names"
            )
        validated_groups[group_name] = members

    return Config(
        github_base_url=github_base_url,
        github_verify_ssl=github_verify_ssl,
        repositories=normalized_repos,
        users=users,
        user_groups=validated_groups,
        github_api_token=github_api_token,
        github_token_env=github_token_env,
    )
