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
