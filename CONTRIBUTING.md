# Contributing to GitHub Statistics

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd insights
```

### 2. Set Up Development Environment

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (REQUIRED)
pre-commit install
```

## Development Workflow

### Test-Driven Development

This project follows a strict test-driven development (TDD) approach:

1. **Write tests first** - Before implementing any feature, write tests that define the expected behavior
2. **Run tests** - Verify that new tests fail (as expected)
3. **Implement feature** - Write the minimal code to make tests pass
4. **Refactor** - Improve code quality while keeping tests passing
5. **Verify** - Run all tests and pre-commit checks

### Making Changes

1. **Create a branch** for your feature or bugfix:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests first** in the appropriate `tests/test_*.py` file

3. **Implement the feature** in the appropriate module under `github_statistics/`

4. **Run tests** to verify your changes:

   ```bash
   pytest
   pytest --cov=github_statistics  # with coverage
   ```

5. **Run pre-commit checks**:

   ```bash
   pre-commit run --all-files
   ```

6. **Commit your changes**:

   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

   Pre-commit hooks will run automatically. If any check fails, fix the issues and commit again.

## Code Quality Standards

### Pre-commit Hooks

All commits must pass the following automated checks:

- **Black** (code formatting, line length: 100)
- **isort** (import sorting)
- **Ruff** (linting)
- **mypy** (type checking)
- **Bandit** (security checks)
- **pydocstyle** (docstring style - Google convention)
- **File checks** (trailing whitespace, file endings, YAML/TOML/JSON validation)

### Code Style Guidelines

- **Line length**: Maximum 100 characters
- **Docstrings**: Use Google-style docstrings for all public functions, classes, and modules
- **Type hints**: Add type hints where beneficial (especially for public APIs)
- **Python version**: Code must be compatible with Python 3.8+
- **Imports**: Sorted automatically by isort (stdlib → third-party → local)

### Example Function with Proper Style

```python
from typing import List, Optional

def process_repositories(repos: List[str], since: Optional[str] = None) -> dict:
    """
    Process a list of repositories and return statistics.

    Args:
        repos: List of repository identifiers in "owner/repo" format.
        since: Optional ISO date string to filter from.

    Returns:
        Dictionary containing repository statistics.

    Raises:
        ValueError: If repository format is invalid.
    """
    # Implementation here
    pass
```

## Testing Guidelines

### Test Organization

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive test names that explain what is being tested

### Test Requirements

- Tests must be **fast** (no network calls to real services)
- Tests must be **deterministic** (same result every time)
- Tests must be **independent** (can run in any order)
- Mock external dependencies (GitHub API, file system when appropriate)
- Aim for high code coverage (>80%)

### Example Test

```python
def test_normalize_repository_url_https():
    """Test that HTTPS repository URLs are normalized to owner/repo."""
    config_data = {
        'github': {'base_url': 'https://github.com/api/v3'},
        'repositories': ['https://github.com/org/repo'],
        'users': ['user1']
    }

    config = load_config_from_dict(config_data)

    assert config.repositories == ['org/repo']
```

## Running Quality Checks

### Before Committing

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run tests
pytest

# Run tests with coverage report
pytest --cov=github_statistics --cov-report=term-missing
```

### Individual Checks

```bash
# Code formatting
black github_statistics/ tests/

# Import sorting
isort github_statistics/ tests/

# Linting
ruff check github_statistics/ tests/

# Type checking
mypy github_statistics/

# Security scanning
bandit -r github_statistics/

# Docstring checking
pydocstyle github_statistics/
```

## Commit Message Guidelines

Use conventional commit format:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:

```text
feat: add support for filtering PRs by label
fix: handle missing timeline events gracefully
docs: update configuration examples in README
test: add tests for date parsing edge cases
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass: `pytest`
2. ✅ All pre-commit checks pass: `pre-commit run --all-files`
3. ✅ Code coverage is maintained or improved
4. ✅ Documentation is updated (README, docstrings, etc.)
5. ✅ TASKS.md updated if implementing a planned step
6. ✅ Commit messages follow guidelines

### Submitting a Pull Request

1. **Push your branch** to the repository
2. **Create a pull request** with a clear description:
   - What changes were made
   - Why the changes were necessary
   - Any relevant issue numbers
   - Testing performed
3. **Wait for review** - Maintainers will review your PR
4. **Address feedback** - Make requested changes and push updates
5. **Merge** - Once approved, your PR will be merged

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for changes
- [ ] Pre-commit checks pass

## Checklist
- [ ] Code follows project style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All CI checks passing
```

## Architecture & Design

- Review `AGENTS.md` for overall architecture and agent responsibilities
- Review `TASKS.md` for the implementation plan and current status
- Follow the modular structure:
  - `cli.py` - Command-line interface
  - `config.py` - Configuration loading and validation
  - `github_client.py` - GitHub API client
  - `models.py` - Data models
  - `collector.py` - Data collection logic
  - `stats.py` - Statistics computation
  - `report_md.py` - Markdown report generation

## Need Help?

- Review existing code and tests for examples
- Check `AGENTS.md` for architecture details
- Check `TASKS.md` for implementation plan
- Open an issue for questions or discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
