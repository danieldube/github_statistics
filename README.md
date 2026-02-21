# GitHub Statistics

[![CI](https://github.com/USERNAME/insights/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/insights/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python command-line tool to compute pull request statistics from GitHub Enterprise instances.

## Installation

```bash
pip install -e .
```

For development, install with test dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

```bash
github_statistics my_config.yaml [options]
```

### Options

- `--since <ISO-DATE>`: Filter PRs created since this date
- `--until <ISO-DATE>`: Filter PRs created until this date
- `--users <user1,user2>`: Filter by specific users
- `--repos <repo1,repo2>`: Filter by specific repositories
- `--output <path>`: Output file path (default: `<config_basename>_statistics.md`)
- `--max-workers <N>`: Number of concurrent workers (default: 4)

## Configuration

Create a YAML configuration file:

```yaml
github:
  # For public GitHub, use: https://api.github.com
  # For GitHub Enterprise, use: https://github.mycompany.com/api/v3
  base_url: https://api.github.com
  api_token: your_token_here  # preferred
  token_env: GITHUB_TOKEN      # optional fallback
  verify_ssl: true

repositories:
  - https://github.com/owner/repo1
  - owner/repo2

users:
  - username1
  - username2
```

**Important:**

- For **public GitHub (github.com)**: use `base_url: https://api.github.com`
- For **GitHub Enterprise**: use `base_url: https://your-github-server.com/api/v3`

You can either set `github.api_token` directly in the config or use an environment variable fallback:

```bash
export GITHUB_TOKEN=your_token_here
```

## Development

### Setting Up Development Environment

Install the package with development dependencies:

```bash
pip install -e ".[dev]"
```

Install pre-commit hooks (required for all contributors):

```bash
pre-commit install
```

### Running Tests

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=github_statistics --cov-report=html
```

### Code Quality

This project uses pre-commit hooks to maintain code quality. All commits must pass the following checks:

- **Black**: Code formatting (line length: 79)
- **isort**: Import sorting
- **Ruff**: Fast Python linter
- **mypy**: Static type checking
- **Bandit**: Security vulnerability scanning
- **pydocstyle**: Docstring style checking (Google style)
- **General checks**: Trailing whitespace, file endings, YAML/TOML/JSON validation, etc.

Run all pre-commit checks manually:

```bash
pre-commit run --all-files
```

Run specific checks:

```bash
pre-commit run black --all-files
pre-commit run mypy --all-files
pre-commit run ruff --all-files
```

### Pull Request Checklist

Before submitting a pull request:

1. ✅ Install and run pre-commit hooks: `pre-commit install && pre-commit run --all-files`
2. ✅ All tests pass: `pytest`
3. ✅ Code coverage maintained: `pytest --cov=github_statistics`
4. ✅ Documentation updated if needed
5. ✅ Commit messages are clear and descriptive

## Requirements

- Python 3.8 or later
- PyYAML
- requests

## License

MIT
