# AGENTS.md

## Project Overview

This project implements a Python command line tool `github_statistics` that computes pull request (PR) statistics from a GitHub (Enterprise/on-prem) instance. The tool reads a YAML configuration file, queries the GitHub REST API for one or more repositories, aggregates PR- and user-level data, computes statistical distributions (min, max, mean, median, count), and outputs a Markdown report.

The tool must:

- Be installable via `pip install github_statistics`.
- Expose a CLI: `github_statistics my_config.yaml [options]`.
- Support Python 3.8+.
- Work with a self-hosted GitHub Enterprise instance reachable over VPN.
- Be implemented test-driven: for each feature, tests are written first and code is then implemented to satisfy the tests.

## Agent Roles

### 1. Architect & Spec Agent

**Purpose:** Maintain and refine the overall design and specification.

**Responsibilities:**

- Maintain a high-level system design consistent with this document.
- Clarify and formalize metric definitions and assumptions.
- Define data models (dataclasses) for PRs, reviews, comments, commits, and events.
- Ensure compatibility with Python 3.8+ and test-driven development practices.
- Keep documentation synchronized with implementation changes.

**Key Outputs:**

- Updated architecture sketches and data model definitions.
- Clarified metric semantics (e.g., what constitutes “requested changes committed”).
- Documentation of limitations and heuristics.

### 2. GitHub API & Data Collection Agent

**Purpose:** Implement reliable, testable access to the GitHub REST API and assemble complete PR datasets.

**Responsibilities:**

- Implement a configurable HTTP client for GitHub Enterprise:
  - Base URL, token from environment variable, SSL verification settings.
- Implement API calls for:
  - Listing PRs (`/repos/{owner}/{repo}/pulls?state=all`).
  - PR details (`/repos/{owner}/{repo}/pulls/{number}`).
  - PR files (`/repos/{owner}/{repo}/pulls/{number}/files`).
  - PR commits (`/repos/{owner}/{repo}/pulls/{number}/commits`).
  - PR reviews (`/repos/{owner}/{repo}/pulls/{number}/reviews`).
  - PR review comments (`/repos/{owner}/{repo}/pulls/{number}/comments`).
  - Issue comments (`/repos/{owner}/{repo}/issues/{number}/comments`).
  - Timeline events (`/repos/{owner}/{repo}/issues/{number}/timeline`), when available.
- Respect pagination and rate limits; implement retry/backoff for transient errors.
- Implement repository and time-horizon filtering at collection time when possible.
- Provide pure Python objects (dataclasses) to downstream agents, independent of HTTP details.
- Enable concurrency (e.g., ThreadPoolExecutor) with a configurable worker count.

**Constraints & Assumptions:**

- All timestamps should be converted to timezone-aware datetimes (UTC).
- If certain endpoints (e.g., timeline) are unavailable on older Enterprise versions, expose this fact so stats agents can degrade gracefully.
- Avoid hardcoding GitHub.com; base URL must be configurable.

### 3. Metrics & Statistics Agent

**Purpose:** Compute all required metrics and distributions from the collected PR data.

**Responsibilities:**

- Implement pure functions that accept lists of PR objects and return:
  - Repository-level statistics.
  - User-level statistics.
- Metrics to compute (as distributions, min/max/mean/median/count) for repositories:

  - Duration of open PRs (created → now or until date).
  - Duration of closed PRs (created → closed_at, not merged).
  - Duration of merged PRs (created → merged_at).
  - Comments per 100 LOC (for each PR, comments / changed LOC * 100).
  - Commits per PR.
  - Re-reviews per PR.
  - Time between request for changes and re-requesting review.
  - Time to first review.

- Metrics to compute (as distributions and rates) for users (where applicable):

  - Time between requested (or re-requested) review and submitting review.
  - Request-for-changes rate vs direct-approval rate.
  - Comments per 100 LOC (as reviewer and/or author, depending on configuration).
  - Changed lines of code per created PR (as author).

- Implement heuristic metrics, clearly documented:

  - Time between CHANGES_REQUESTED and first commit by the PR author after that time (optional).
  - Count of commits after a PR is ready for review that are not associated with a “changes requested” cycle.

**Constraints & Assumptions:**

- Use only Python standard library where possible (`statistics`, `datetime`, etc.).
- Metrics must handle edge cases (e.g., no reviews, zero LOC, missing timeline events).
- Heuristic metrics must be clearly documented as approximations and must gracefully degrade if required event data is missing.

### 4. CLI & Configuration Agent

**Purpose:** Provide a user-friendly command line interface and configuration handling.

**Responsibilities:**

- Implement a CLI entry point:

  - Command: `github_statistics my_config.yaml [options]`.
  - Arguments:
    - `config_path` (YAML file, required).
    - `--since` and `--until` (ISO date strings, optional).
    - `--users` (comma-separated list, optional).
    - `--repos` (comma-separated list of repo URLs or `owner/repo`, optional).
    - `--output` (output Markdown path, default `<config_basename>_statistics.md`).
    - `--max-workers` (int, default e.g. 4).

- Parse YAML configuration with structure similar to:

  ```yaml
  github:
    # For public GitHub: https://api.github.com
    # For GitHub Enterprise: https://github.mycompany.com/api/v3
    base_url: https://api.github.com
    token_env: GITHUB_TOKEN
    verify_ssl: true

  repositories:
    - https://github.com/owner/repo1
    - org2/repo2

  users:
    - danieldube
    - uidg4302
  ```

- Normalize repository identifiers to `owner/repo` pairs.
- Apply CLI filters on top of config (CLI narrowing config, not expanding it).
- Ensure Python 3.8 compatibility.

### 5. Reporting & Output Agent

**Purpose:** Turn metrics into a Markdown report.

**Responsibilities:**

- Generate a Markdown file containing:

  - Global information: time horizon and applied filters.
  - Per-repository sections, e.g.:

      ```markdown
      ## Repositories

      ### <repo URL or owner/repo>
      - **Duration open pull requests (days):**
        - count: N
        - min: 0.5, median: 4.2, mean: 6.1, max: 28.3
      - **Duration closed pull requests (days):**
        ...
      - **Comments per 100 LOC:**
        - ...
      ```

  - Per-user sections, e.g.:

      ```markdown
      ## Users

      ### <username>
      - **Time between requested and submitting review (hours):**
        - count: N
        - min: 0.1, median: 2.3, mean: 3.4, max: 12.0
      - **Request for changes rate:** 15.0%
      - **Direct approval rate:** 80.0%
      - **Comments per 100 LOC:** ...
      - **Changed lines of code per created PR:** ...
      ```

- Ensure numeric formatting is consistent (e.g., 1–2 decimal places).
- Reflect missing data (e.g., “no reviews available”) in a clear, non-crashing way.

### 6. Testing & Quality Agent

**Purpose:** Enforce test-driven development and maintain quality.

**Responsibilities:**

- Enforce the rule: for each feature, tests are written first, then implementation is updated to pass tests.
- Maintain a test suite using `pytest` (preferred).

  - Unit tests for:
    - Config parsing and CLI argument handling.
    - GitHub client behavior with mocked HTTP responses.
    - Data transformation into PR models.
    - Metric calculation functions (stats) with synthetic inputs.
    - Markdown report generation.
  - Integration tests (optional but recommended):
    - End-to-end run against mocked GitHub API (e.g., using `responses` or `httpx` mocking).
- Ensure coverage for Python 3.8+.
- Integrate static checks and code quality tools:
  - `black` for code formatting (line length: 79).
  - `ruff` for fast linting and style checks.
  - `mypy` for type checking.
  - `isort` for import sorting.
  - `bandit` for security checks.
  - `pydocstyle` for docstring conventions (Google style).
- Enforce pre-commit hooks to maintain code quality (see Pre-commit Hooks section below).

**Constraints:**

- Tests must be fast and deterministic; all network calls must be mocked in tests.
- No test may depend on actual GitHub access or VPN connectivity.
- All pull requests must pass pre-commit checks before merge.

## Code Quality & Pre-commit Hooks

This project uses pre-commit hooks to enforce code quality standards. All contributors must install and use pre-commit hooks.

### Installation

After cloning the repository, install pre-commit hooks:

```bash
# Install development dependencies (includes pre-commit)
pip install -e ".[dev]"

# Install the pre-commit hooks
pre-commit install
```

### Enabled Checks

The following checks run automatically on every commit:

1. **General File Checks** (via pre-commit-hooks):
   - Remove trailing whitespace
   - Ensure files end with newline
   - Validate YAML, TOML, and JSON syntax
   - Prevent large files from being committed
   - Check for merge conflicts
   - Detect debug statements
   - Ensure consistent line endings (LF)

2. **Black** - Code formatting (line length: 79, Python 3.8+)
   - Automatically formats Python code to ensure consistency

3. **isort** - Import sorting
   - Organizes imports alphabetically and by type
   - Configured to work with Black

4. **Ruff** - Fast Python linter
   - Checks for common errors and style issues
   - Automatically fixes many issues
   - Replaces flake8, pyflakes, pycodestyle, and more

5. **mypy** - Type checking
   - Static type checking for Python code
   - Configured for Python 3.8+
   - Excludes test files

6. **Bandit** - Security vulnerability scanner
   - Scans for common security issues
   - Excludes test files (asserts allowed)

7. **pydocstyle** - Docstring style checker
   - Enforces Google-style docstrings
   - Ensures documentation quality

8. **YAML Formatter** - YAML file formatting
   - Ensures consistent YAML formatting

9. **Markdownlint** - Markdown linting
   - Ensures consistent Markdown formatting

### Running Hooks Manually

To run all hooks on all files:

```bash
pre-commit run --all-files
```

To run a specific hook:

```bash
pre-commit run black --all-files
pre-commit run mypy --all-files
pre-commit run ruff --all-files
```

### Updating Hooks

To update pre-commit hooks to the latest versions:

```bash
pre-commit autoupdate
```

### Pull Request Requirements

All pull requests MUST:

1. Pass all pre-commit checks
2. Pass all pytest tests (`pytest`)
3. Maintain or improve code coverage
4. Include tests for new functionality
5. Update documentation as needed

To verify your changes before pushing:

```bash
# Run pre-commit checks
pre-commit run --all-files

# Run tests
pytest

# Run tests with coverage
pytest --cov=github_statistics --cov-report=term-missing
```

### Configuration Files

- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `pyproject.toml` - Tool configurations (black, ruff, mypy, bandit, isort, pydocstyle, pytest)
- `.markdownlint.json` - Markdown linting rules

### Bypassing Hooks (Emergency Only)

In rare cases where you need to bypass pre-commit hooks:

```bash
git commit --no-verify -m "message"
```

**WARNING:** This should only be used in exceptional circumstances and requires explicit approval from maintainers.

## Global Constraints and Non-Functional Requirements

- Python 3.8+ support.
- Test-driven workflow: each incremental development step adds or extends tests first, then implements/adjusts functionality.
- No hidden network calls: all GitHub interactions must go through the GitHub client abstraction to allow mocking.
- Clear error messages on:
  - Missing config entries.
  - Missing or invalid token.
  - Inaccessible GitHub base URL.
- Maintainable, modular code structure as described in the project layout.
