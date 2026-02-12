"""
Test that all modules in the project can be imported.
"""


def test_can_import_main_package():
    """Test that the main github_statistics package can be imported."""
    import github_statistics

    assert github_statistics is not None


def test_can_import_cli():
    """Test that the cli module can be imported."""
    import github_statistics.cli

    assert github_statistics.cli is not None
    assert hasattr(github_statistics.cli, "main")


def test_can_import_config():
    """Test that the config module can be imported."""
    import github_statistics.config

    assert github_statistics.config is not None
    assert hasattr(github_statistics.config, "load_config")


def test_can_import_github_client():
    """Test that the github_client module can be imported."""
    import github_statistics.github_client

    assert github_statistics.github_client is not None
    assert hasattr(github_statistics.github_client, "GitHubClient")
    assert hasattr(github_statistics.github_client, "HttpGitHubClient")
    assert hasattr(github_statistics.github_client, "FakeGitHubClient")


def test_can_import_models():
    """Test that the models module can be imported."""
    import github_statistics.models

    assert github_statistics.models is not None


def test_can_import_collector():
    """Test that the collector module can be imported."""
    import github_statistics.collector

    assert github_statistics.collector is not None
    assert hasattr(github_statistics.collector, "collect_prs")


def test_can_import_stats():
    """Test that the stats module can be imported."""
    import github_statistics.stats

    assert github_statistics.stats is not None
    assert hasattr(github_statistics.stats, "compute_repository_stats")
    assert hasattr(github_statistics.stats, "compute_user_stats")


def test_can_import_report_md():
    """Test that the report_md module can be imported."""
    import github_statistics.report_md

    assert github_statistics.report_md is not None
    assert hasattr(github_statistics.report_md, "render_report")
