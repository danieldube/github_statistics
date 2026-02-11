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
    base_url: https://github.mycompany.com/api/v3
    token_env: GITHUB_TOKEN
    verify_ssl: true

  repositories:
    - https://github.mycompany.com/org1/repo1
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
- Integrate static checks (optional):
    - `flake8` / `ruff` for style.
    - `mypy` for type checking, if types are used extensively.

**Constraints:**

- Tests must be fast and deterministic; all network calls must be mocked in tests.
- No test may depend on actual GitHub access or VPN connectivity.

## Global Constraints and Non-Functional Requirements

- Python 3.8+ support.
- Test-driven workflow: each incremental development step adds or extends tests first, then implements/adjusts functionality.
- No hidden network calls: all GitHub interactions must go through the GitHub client abstraction to allow mocking.
- Clear error messages on:
    - Missing config entries.
    - Missing or invalid token.
    - Inaccessible GitHub base URL.
- Maintainable, modular code structure as described in the project layout.