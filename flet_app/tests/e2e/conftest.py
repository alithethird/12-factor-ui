"""Fixtures for end-to-end tests."""

import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest


def _create_mock_flask_project(project_dir: str) -> None:
    """Create a mock Flask project structure."""
    os.makedirs(project_dir, exist_ok=True)
    
    # Create requirements.txt
    requirements = """Flask==2.3.0
Werkzeug==2.3.0
"""
    with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
        f.write(requirements)
    
    # Create main app file
    app_code = """from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World'

if __name__ == '__main__':
    app.run()
"""
    with open(os.path.join(project_dir, "app.py"), "w") as f:
        f.write(app_code)


def _create_mock_django_project(project_dir: str) -> None:
    """Create a mock Django project structure."""
    os.makedirs(project_dir, exist_ok=True)
    
    # Create requirements.txt
    requirements = """Django==4.2.0
asgiref==3.6.0
"""
    with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
        f.write(requirements)
    
    # Create manage.py
    manage_code = """#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        raise ImportError('Failed to import Django')
    execute_from_command_line(sys.argv)
"""
    with open(os.path.join(project_dir, "manage.py"), "w") as f:
        f.write(manage_code)


@pytest.fixture
def download_github_example(temp_project_dir):
    """Fixture to create mock example projects locally."""
    def _download(example_name: str, output_dir: str) -> dict:
        """Create a mock example project."""
        if example_name == "flask-minimal":
            final_path = os.path.join(output_dir, "flask-minimal")
            _create_mock_flask_project(final_path)
            return {
                "path": final_path,
                "project_name": "flask_minimal",
            }
        elif example_name == "django":
            final_path = os.path.join(output_dir, "django")
            _create_mock_django_project(final_path)
            return {
                "path": final_path,
                "project_name": "django",
            }
        else:
            raise ValueError(f"Unknown example: {example_name}")
    
    return _download


@pytest.fixture
def flask_minimal_zip(temp_project_dir):
    """Fixture to provide mock Flask example as ZIP file."""
    def _create_zip() -> dict:
        """Create a ZIP file with mock Flask example."""
        zip_path = os.path.join(temp_project_dir, "flask_minimal.zip")
        
        # Create temporary directory for Flask project
        temp_flask_dir = os.path.join(temp_project_dir, "flask_temp")
        _create_mock_flask_project(temp_flask_dir)
        
        # Create ZIP from temporary directory
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_flask_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_flask_dir)
                    zf.write(file_path, arcname)
        
        # Cleanup temporary directory
        shutil.rmtree(temp_flask_dir)
        
        return {
            "zip_path": zip_path,
            "output_dir": temp_project_dir,
            "project_name": "flask_minimal",
        }
    
    return _create_zip


@pytest.fixture
def django_zip(temp_project_dir):
    """Fixture to provide mock Django example as ZIP file."""
    def _create_zip() -> dict:
        """Create a ZIP file with mock Django example."""
        zip_path = os.path.join(temp_project_dir, "django.zip")
        
        # Create temporary directory for Django project
        temp_django_dir = os.path.join(temp_project_dir, "django_temp")
        _create_mock_django_project(temp_django_dir)
        
        # Create ZIP from temporary directory
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(temp_django_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_django_dir)
                    zf.write(file_path, arcname)
        
        # Cleanup temporary directory
        shutil.rmtree(temp_django_dir)
        
        return {
            "zip_path": zip_path,
            "output_dir": temp_project_dir,
            "project_name": "django",
        }
    
    return _create_zip


@pytest.fixture
def download_canonical_flask_minimal(temp_project_dir):
    """Fixture to download canonical/paas-charm flask-minimal example."""
    def _download() -> dict:
        """Download flask-minimal from canonical/paas-charm GitHub repo.
        
        Downloads the entire examples/flask-minimal directory and extracts
        just the flask_minimal_app subdirectory.
        """
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
        import os
        app_path = os.path.join(result["path"], "flask_minimal_app")
        
        return {
            "path": app_path,
            "project_name": "flask_minimal_app",
        }
    
    return _download


@pytest.fixture
def mock_pack_commands(monkeypatch):
    """Mock subprocess.run for pack commands but allow git to work."""
    from unittest.mock import patch, MagicMock
    from tests.mocks.command_mocker import MockSubprocessPopen
    
    original_run = __import__('subprocess').run
    
    def selective_run(args, *pargs, **kwargs):
        """Run git commands normally, but mock pack commands."""
        # Check if this is a git command
        if isinstance(args, list) and 'git' in args[0]:
            # Use the original subprocess.run for git commands
            return original_run(args, *pargs, **kwargs)
        
        # For rockcraft and charmcraft pack commands, mock them
        if isinstance(args, list) and any(cmd in ' '.join(args) for cmd in ['rockcraft pack', 'charmcraft pack']):
            # Create a mock Popen object that will handle packing
            mock_popen = MockSubprocessPopen(args, cwd=kwargs.get('cwd'), 
                                           stdout=kwargs.get('stdout'),
                                           stderr=kwargs.get('stderr'),
                                           text=kwargs.get('text'))
            # For subprocess.run compatibility, return a CompletedProcess-like object
            class CompletedProcess:
                def __init__(self, popen_obj):
                    self.returncode = popen_obj.returncode
                    self.stdout = ''
                    self.stderr = ''
                    self.args = popen_obj.args
            
            mock_popen.wait()
            return CompletedProcess(mock_popen)
        
        # For other commands, use original
        return original_run(args, *pargs, **kwargs)
    
    monkeypatch.setattr("subprocess.run", selective_run)
    return selective_run


@pytest.fixture
def mock_pack_commands_popen(monkeypatch):
    """Mock subprocess.Popen for pack commands but allow git to work via subprocess.run."""
    from tests.mocks.command_mocker import MockSubprocessPopen
    
    original_popen = __import__('subprocess').Popen
    
    def selective_popen(*args, **kwargs):
        """Use mock Popen for rockcraft/charmcraft, original for git."""
        # If this is a git command, use original Popen
        cmd = args[0] if args else []
        if isinstance(cmd, list) and cmd and 'git' in cmd[0]:
            return original_popen(*args, **kwargs)
        
        # For rockcraft and charmcraft, use the mock
        return MockSubprocessPopen(*args, **kwargs)
    
    monkeypatch.setattr("subprocess.Popen", selective_popen)
    return selective_popen

