"""Pytest configuration and fixtures."""
import os
import sys
import pytest
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def temp_workspace():
    """Create a temporary workspace for tests."""
    temp_dir = tempfile.mkdtemp(prefix="dtvoice_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clean environment for each test."""
    # Use a fresh temp config dir for each test
    temp_dir = tempfile.mkdtemp(prefix="dtvoice_config_")
    import config
    monkeypatch.setattr(config, "CONFIG_DIR", temp_dir)
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")