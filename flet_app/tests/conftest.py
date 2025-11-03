"""Pytest configuration and shared fixtures."""
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from tests.mocks.command_mocker import MockSubprocessPopen, create_status_callback_mock


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for test projects."""
    temp_dir = tempfile.mkdtemp(prefix="test_charm_rock_")
    yield temp_dir
    # Cleanup
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def download_canonical_flask_minimal(temp_project_dir):
    """Fixture to download canonical/paas-charm flask-minimal example."""
    def _download() -> dict:
        """Download flask-minimal from canonical/paas-charm GitHub repo."""
        from logic.downloader import GithubDownloader
        
        # Download the entire flask-minimal directory
        downloader = GithubDownloader(
            repo_url="https://github.com/canonical/paas-charm",
            branch="main",
            subfolder="examples/flask-minimal",
        )
        
        result = downloader.download(temp_project_dir)
        
        # The result path will be examples/flask-minimal
        # We need to use examples/flask-minimal/flask_minimal_app for the Flask app
        app_path = os.path.join(result["path"], "flask_minimal_app")
        
        return {
            "path": app_path,
            "project_name": "flask_minimal_app",
        }
    
    return _download



@pytest.fixture
def mock_popen(monkeypatch):
    """Patch subprocess.Popen with mock implementation."""

    def popen_factory(*args, **kwargs):
        return MockSubprocessPopen(*args, **kwargs)

    monkeypatch.setattr("subprocess.Popen", popen_factory)
    return popen_factory


@pytest.fixture
def mock_popen_failing(monkeypatch):
    """Patch subprocess.Popen with failing mock implementation."""

    def popen_factory(*args, **kwargs):
        mock = MockSubprocessPopen(*args, **kwargs)
        mock.returncode = 1
        mock._should_create_artifact = False
        return mock

    monkeypatch.setattr("subprocess.Popen", popen_factory)
    return popen_factory


@pytest.fixture
def status_callback():
    """Create a status callback mock that records calls."""
    callback, call_list = create_status_callback_mock()
    callback.calls = call_list
    return callback


@pytest.fixture
def mock_which(monkeypatch):
    """Mock shutil.which to return a valid command path."""

    def mock_which_impl(command):
        # Return the command itself as a "valid" path for testing
        return f"/usr/bin/{command}"

    monkeypatch.setattr("shutil.which", mock_which_impl)


@pytest.fixture
def rockcraft_generator(temp_project_dir, mock_which):
    """Create a RockcraftGenerator instance for testing."""
    from logic.rockcraft import RockcraftGenerator

    return RockcraftGenerator(temp_project_dir, "test-project", framework="python-framework")


@pytest.fixture
def charmcraft_generator(temp_project_dir, mock_which):
    """Create a CharmcraftGenerator instance for testing."""
    from logic.charmcraft import CharmcraftGenerator

    return CharmcraftGenerator(
        integrations=["postgresql"],
        config_options=[],
        project_path=temp_project_dir,
        project_name="test-charm",
    )


@pytest.fixture
def app_state():
    """Create a mock application state."""
    return {
        "active_step": 1,
        "form_data": {
            "framework": "python-framework",
            "frameworkName": "Python",
            "source": None,
            "jobId": "test-job-123",
            "integrations": [{"id": "postgresql"}],
            "configOptions": [],
            "sourceProjectName": "test-project",
        },
        "set_active_step": lambda step: None,
        "update_form_data": lambda data: None,
        "get_form_data": lambda: {
            "framework": "python-framework",
            "frameworkName": "Python",
            "source": None,
            "jobId": "test-job-123",
            "integrations": [{"id": "postgresql"}],
            "configOptions": [],
            "sourceProjectName": "test-project",
        },
    }
