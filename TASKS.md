# TASKS.md

This document describes a step-by-step, test-driven plan to implement the `github_statistics` project. Each step includes writing tests first, then implementing the functionality to satisfy those tests. The project targets Python 3.8+.

## Step 0: Project Skeleton and Tooling

1. Create project structure:

   ```text
   github_statistics/
     github_statistics/
       __init__.py
       cli.py
       config.py
       github_client.py
       models.py
       collector.py
       stats.py
       report_md.py
     tests/
       __init__.py
   ```

2. Add basic packaging configuration (`pyproject.toml` or `setup.cfg`) with:
    - Name: `github_statistics`
    - Minimum Python version: `>=3.8`
    - Entry point: `github_statistics = github_statistics.cli:main`

3. Choose dependencies:
    - `PyYAML` for YAML parsing.
    - `requests` or `httpx` for HTTP.
    - `pytest` for testing.

4. Write initial tests:

    - `tests/test_project_structure.py`: Verify that modules can be imported.
    - `tests/test_version.py` (optional): Verify package has a `__version__` attribute.

5. Implement minimal code and packaging to make these tests pass.

## Step 1: Configuration Loading and Validation

1. Tests (write first):

    - `tests/test_config_loading.py`:
        - Test loading a minimal valid `my_config.yaml` with keys:
            - `github.base_url`
            - `github.token_env`
            - `github.verify_ssl`
            - `repositories`
            - `users`
        - Test that repository URLs and `owner/repo` forms are normalized into a canonical `owner/repo` representation.
        - Test that users list is loaded as-is.
        - Test default behaviors if some optional keys are missing (e.g., default `token_env="GITHUB_TOKEN"`, default `verify_ssl=True`).
        - Test validation errors:
            - Missing `github.base_url`.
            - Empty `repositories` list.

2. Implementation:

    - Implement `Config` dataclass in `config.py` with fields for:
        - `github_base_url`
        - `github_token_env`
        - `github_verify_ssl`
        - `repositories` (normalized to `owner/repo`)
        - `users`
    - Implement function `load_config(path: str) -> Config`:
        - Read YAML.
        - Apply defaults and validation.
        - Normalize repository identifiers.
    - Ensure tests pass on Python 3.8+.

## Step 2: CLI Entry Point and Argument Handling

1. Tests:

    - `tests/test_cli_args.py` using `pytest` and `capsys` or `click.testing`/`typer.testing` if a CLI framework is used.
    - Test that running `github_statistics <config>`:
        - Loads configuration using `load_config`.
        - Applies optional flags:
            - `--since` and `--until` correctly parsed as dates.
            - `--users` overrides or narrows configured users.
            - `--repos` narrows configured repositories.
            - `--output` changes the output file path.
    - Test that invalid date formats or unknown options result in clean error messages and exit codes.

2. Implementation:

    - Implement `main()` in `cli.py`:
        - Parse arguments with `argparse` or `typer`.
        - Call `load_config`.
        - Construct an internal `RunOptions` structure combining config and CLI filters.
    - Keep actual execution stubbed (e.g., no GitHub calls yet) so tests only cover argument and config handling.

## Step 3: Data Models (PRs, Reviews, Events, Commits, Comments)

1. Tests:

    - `tests/test_models.py`:
        - Test that dataclasses can be instantiated with expected fields:
            - `PullRequest`, `ReviewEvent`, `ReviewRequestEvent`, `ReadyForReviewEvent`, `CommitInfo`, `CommentInfo`.
        - Test that a `PullRequest` can aggregate lists of commits, comments, and events.
        - Test simple invariants (e.g., `created_at` must be before `closed_at` in synthetic examples).

2. Implementation:

    - Define models in `models.py` using `dataclasses` for Python 3.8+.
    - Ensure all timestamps use `datetime` objects; document assumption that they are UTC.

## Step 4: GitHub Client Abstraction (No Real Network Yet)

1. Tests:

    - `tests/test_github_client_interface.py`:
        - Define a `GitHubClient` interface with methods like:
            - `list_pull_requests(owner, repo, since=None, until=None)`
            - `get_pull_request_details(owner, repo, number)`
            - `get_pull_request_files(owner, repo, number)`
            - `get_pull_request_reviews(owner, repo, number)`
            - `get_pull_request_review_comments(owner, repo, number)`
            - `get_issue_comments(owner, repo, number)`
            - `get_issue_timeline(owner, repo, number)`
        - Use a fake or stub implementation to verify the interface contract (no real HTTP).

2. Implementation:

    - Implement a base class or protocol in `github_client.py` describing the interface.
    - Implement a `FakeGitHubClient` for tests (in tests or a test helpers module).
    - Do not implement real HTTP yet; focus on interface, types, and docstrings.

## Step 5: Collector: Assembling Full PR Objects (with Fake Client)

1. Tests:

    - `tests/test_collector_with_fake_client.py`:
        - Using `FakeGitHubClient`, simulate:
            - A repository with a few PRs and associated events.
        - Test that `collector.collect_prs(...)`:
            - Returns a list of `PullRequest` objects populated with:
                - Basic PR info (author, created_at, closed_at, merged_at, state).
                - Commits (`CommitInfo`).
                - Comments (`CommentInfo`).
                - Reviews (`ReviewEvent`).
                - Review requests (`ReviewRequestEvent`).
                - Ready-for-review events (`ReadyForReviewEvent` if available).
        - Test filtering by:
            - Repository.
            - Time horizon (based on `created_at`).

2. Implementation:

    - Implement `collector.collect_prs(config, options, client)`:
        - Iterate repositories.
        - For each PR from the client, assemble a `PullRequest` object.
        - Apply time-horizon filtering.
    - Use only the fake client in tests; real HTTP is still unimplemented.

## Step 6: GitHub Client HTTP Implementation (with Mocked Network)

1. Tests:

    - `tests/test_github_client_http.py` using `responses` or `requests-mock`:
        - Test that `HttpGitHubClient`:
            - Requests appropriate endpoints and query parameters for:
                - Listing PRs with pagination.
                - Fetching PR details, files, commits, reviews, review comments, issue comments, and timeline.
            - Respects base URL, token, and `verify_ssl` settings.
            - Handles pagination until exhaustion.
            - Raises or returns meaningful errors on 4xx/5xx.
        - Test that JSON responses are correctly transformed into intermediate Python dictionaries or directly into dataclasses where appropriate.

2. Implementation:

    - Implement `HttpGitHubClient` in `github_client.py` using `requests` or `httpx`.
    - Add helper methods for pagination and media-type headers (for timeline endpoint).
    - Ensure that all HTTP behavior is covered by tests with mocked responses (no real GitHub calls).

## Step 7: Statistics Computation (Core Metrics)

1. Tests:

    - `tests/test_stats_repo_metrics.py`:
        - Use synthetic `PullRequest` objects to test:
            - PR duration distributions for open, closed, and merged PRs.
            - Time to first review.
            - Time between CHANGES_REQUESTED and re-requesting review.
            - Commits per PR distribution.
            - Re-reviews per PR distribution.
            - Comments per 100 LOC distribution.
        - Verify corner cases:
            - PRs without reviews.
            - PRs with zero LOC.
            - Single-element distributions (min=max=median=mean).

    - `tests/test_stats_user_metrics.py`:
        - Test per-user metrics:
            - Time between review request and review submission.
            - Request-for-changes rate and direct-approval rate.
            - LOC per created PR.
            - Comments per 100 LOC as reviewer or author.

2. Implementation:

    - In `stats.py`, implement:
        - Generic `Distribution` dataclass with fields: `count`, `minimum`, `maximum`, `mean`, `median`.
        - Helper functions to compute distributions from lists of numeric values.
        - Repository-level metric functions receiving lists of `PullRequest` objects.
        - User-level metric functions keyed by username.
    - Implement metric logic based on the defined conventions and heuristics; ensure all tests pass.

## Step 8: Heuristic Metrics (Ready-for-Review and Unrequested Commits)

1. Tests:

    - `tests/test_stats_ready_for_review.py`:
        - Construct synthetic PR timelines with:
            - Draft → ready-for-review event.
            - CHANGES_REQUESTED reviews and subsequent review requests.
            - Commits before and after ready-for-review, with varying timing.
        - Test that:
            - Commits after ready-for-review are correctly counted.
            - Commits classified as “requested” vs “not requested” follow the defined state machine.
            - Metrics gracefully handle missing ready-for-review or timeline data.

2. Implementation:

    - In `stats.py`, implement helper:
        - `classify_commits_requested_vs_unrequested(pr: PullRequest) -> Tuple[int, int]`.
    - Implement per-PR and aggregate metrics based on these classifications.
    - Document limitations in docstrings and ensure tests encode the intended semantics.

## Step 9: Markdown Report Generation

1. Tests:

    - `tests/test_report_md.py`:
        - Given synthetic `RepoStats` and `UserStats` objects, test that:
            - `report_md.render_report(...)` returns a Markdown string with:
                - Sections for repositories and users.
                - Correct formatting of numeric values and distributions.
                - Inclusion of time horizon and filter metadata.
            - Missing data (e.g., no PRs, no reviews) is represented clearly (e.g., “no data”).

2. Implementation:

    - In `report_md.py`, implement `render_report(repos_stats, users_stats, options) -> str`.
    - Implement formatting helpers for days, hours, percentages, and distributions.
    - Ensure report is deterministic for tests (e.g., sorted repository and user names).

## Step 10: Wire Everything Together in CLI

1. Tests:

    - `tests/test_cli_end_to_end.py` with mocks:
        - Mock `HttpGitHubClient` to return prepared data.
        - Run `main()` with temporary config file and options.
        - Assert that:
            - The Markdown file is created at the expected path.
            - Its contents include expected values (checked with substring assertions).

2. Implementation:

    - Implement the CLI orchestration in `cli.py`:
        - Load config.
        - Instantiate `HttpGitHubClient`.
        - Call `collector.collect_prs`.
        - Compute stats via `stats.py`.
        - Render report using `report_md.py`.
        - Write Markdown to file.

## Step 11: Polish, Error Handling, and Documentation

1. Tests:

    - `tests/test_error_handling.py`:
        - Invalid config paths produce clear error messages.
        - Missing token env var fails gracefully.
        - HTTP connectivity errors are reported clearly (with a short hint).

2. Implementation:

    - Improve error messages and exit codes in the CLI.
    - Add top-level `README.md` describing installation, configuration, and usage.
    - Document limits and approximations (especially for heuristic metrics).

## Step 12: Continuous Integration and Final Checks

1. Configure CI (e.g., GitHub Actions or internal CI) to:
    - Run tests on Python 3.8, 3.9, 3.10, 3.11+.
    - Optionally run linters and type checkers.

2. Final manual checks:
    - Run `github_statistics` against a small real test repo (if allowed) from within VPN to validate behavior beyond mocked tests.