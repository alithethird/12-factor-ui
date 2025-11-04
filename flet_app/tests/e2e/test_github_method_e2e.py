"""End-to-end tests using GitHub download method."""

import os
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from logic.processor import ApplicationProcessor
from logic.rockcraft import RockcraftGenerator
from logic.charmcraft import CharmcraftGenerator


def validate_rockcraft_yaml(yaml_path: str) -> dict:
    """Validate rockcraft.yaml structure."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"rockcraft.yaml not found at {yaml_path}")
    
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, dict):
        raise ValueError("rockcraft.yaml root must be a dictionary")
    
    required_fields = ["name", "summary"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in rockcraft.yaml")
    
    return data


def validate_charmcraft_yaml(yaml_path: str) -> dict:
    """Validate charmcraft.yaml structure."""
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"charmcraft.yaml not found at {yaml_path}")
    
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, dict):
        raise ValueError("charmcraft.yaml root must be a dictionary")
    
    required_fields = ["name", "summary", "type"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in charmcraft.yaml")
    
    return data


@pytest.mark.e2e
@pytest.mark.slow
class TestGitHubMethodFlask:
    """E2E tests for Flask example using GitHub method."""

    def test_flask_minimal_validation(self, download_github_example, temp_project_dir, mock_popen):
        """Test: Download flask-minimal and validate application."""
        result = download_github_example("flask-minimal", temp_project_dir)
        project_path = result["path"]
        
        processor = ApplicationProcessor(project_path, "flask")
        assert processor.check_project() is True

    def test_flask_minimal_rockcraft_generation(self, download_github_example, temp_project_dir, mock_popen):
        """Test: Generate rockcraft.yaml and rock file from flask-minimal."""
        result = download_github_example("flask-minimal", temp_project_dir)
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "flask")
        processor.check_project()
        
        rock_gen = RockcraftGenerator(project_path, project_name, "flask")
        yaml_path = rock_gen.init_rockcraft()
        
        assert os.path.exists(yaml_path), "rockcraft.yaml not created"
        validate_rockcraft_yaml(yaml_path)

    def test_flask_minimal_charmcraft_initialization(self, download_github_example, temp_project_dir, mock_popen):
        """Test: Initialize charmcraft from flask-minimal."""
        result = download_github_example("flask-minimal", temp_project_dir)
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "flask")
        processor.check_project()
        
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=project_path,
            project_name=project_name,
        )
        yaml_path, temp_dir = charm_gen.init_charmcraft()
        
        assert os.path.exists(yaml_path), "charmcraft.yaml not created"
        validate_charmcraft_yaml(yaml_path)

    def test_flask_minimal_full_workflow(self, download_github_example, temp_project_dir, mock_popen):
        """Test: Full workflow - download, validate, generate rock and charm."""
        result = download_github_example("flask-minimal", temp_project_dir)
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "flask")
        assert processor.check_project() is True
        
        rock_gen = RockcraftGenerator(project_path, project_name, "flask")
        rock_yaml_path = rock_gen.init_rockcraft()
        assert os.path.exists(rock_yaml_path)
        validate_rockcraft_yaml(rock_yaml_path)
        
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=project_path,
            project_name=project_name,
        )
        charm_yaml_path, charm_temp_dir = charm_gen.init_charmcraft()
        assert os.path.exists(charm_yaml_path)
        validate_charmcraft_yaml(charm_yaml_path)
        
        charm_gen.cleanup()


@pytest.mark.e2e
@pytest.mark.slow
class TestGitHubMethodDjango:
    """E2E tests for Django example using GitHub method."""

    def test_django_validation(self, download_github_example, temp_project_dir, mock_popen):
        """Test: Download django and validate application."""
        result = download_github_example("django", temp_project_dir)
        project_path = result["path"]
        
        processor = ApplicationProcessor(project_path, "django")
        assert processor.check_project() is True

    def test_django_rockcraft_generation(self, download_github_example, temp_project_dir, mock_popen):
        """Test: Generate rockcraft.yaml from django example."""
        result = download_github_example("django", temp_project_dir)
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "django")
        processor.check_project()
        
        rock_gen = RockcraftGenerator(project_path, project_name, "django")
        yaml_path = rock_gen.init_rockcraft()
        
        assert os.path.exists(yaml_path)
        validate_rockcraft_yaml(yaml_path)

    def test_django_charmcraft_initialization(self, download_github_example, temp_project_dir, mock_popen):
        """Test: Initialize charmcraft from django example."""
        result = download_github_example("django", temp_project_dir)
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "django")
        processor.check_project()
        
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=project_path,
            project_name=project_name,
        )
        yaml_path, temp_dir = charm_gen.init_charmcraft()
        
        assert os.path.exists(yaml_path)
        validate_charmcraft_yaml(yaml_path)

    def test_django_full_workflow(self, download_github_example, temp_project_dir, mock_popen):
        """Test: Full workflow for django."""
        result = download_github_example("django", temp_project_dir)
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "django")
        assert processor.check_project() is True
        
        rock_gen = RockcraftGenerator(project_path, project_name, "django")
        rock_yaml_path = rock_gen.init_rockcraft()
        assert os.path.exists(rock_yaml_path)
        validate_rockcraft_yaml(rock_yaml_path)
        
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=project_path,
            project_name=project_name,
        )
        charm_yaml_path, charm_temp_dir = charm_gen.init_charmcraft()
        assert os.path.exists(charm_yaml_path)
        validate_charmcraft_yaml(charm_yaml_path)
        
        charm_gen.cleanup()
