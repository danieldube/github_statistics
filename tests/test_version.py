"""
Test that the package has a version attribute.
"""
import pytest


def test_package_has_version():
    """Test that the github_statistics package has a __version__ attribute."""
    import github_statistics
    assert hasattr(github_statistics, '__version__')
    assert isinstance(github_statistics.__version__, str)
    assert len(github_statistics.__version__) > 0


def test_version_format():
    """Test that the version follows semantic versioning pattern."""
    import github_statistics
    import re

    # Basic semver pattern: MAJOR.MINOR.PATCH with optional pre-release/build metadata
    version_pattern = r'^\d+\.\d+\.\d+(?:[-+].*)?$'
    assert re.match(version_pattern, github_statistics.__version__), \
        f"Version '{github_statistics.__version__}' does not match semantic versioning pattern"

