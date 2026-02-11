# GitHub Statistics

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
  base_url: https://github.mycompany.com/api/v3
  token_env: GITHUB_TOKEN
  verify_ssl: true

repositories:
  - https://github.mycompany.com/org1/repo1
  - org2/repo2

users:
  - username1
  - username2
```

Set your GitHub token as an environment variable:

```bash
export GITHUB_TOKEN=your_token_here
```

## Development

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=github_statistics --cov-report=html
```

## Requirements

- Python 3.8 or later
- PyYAML
- requests

## License

MIT

