"""End-to-end tests using ZIP download method."""

import os
import sys
import yaml
import zipfile
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
class TestZipMethodFlask:
    """E2E tests for Flask example using ZIP method."""

    def test_flask_minimal_zip_validation(self, flask_minimal_zip, mock_popen):
        """Test: Extract and validate flask-minimal from ZIP."""
        result = flask_minimal_zip()
        zip_path = result["zip_path"]
        output_dir = result["output_dir"]
        
        extract_dir = os.path.join(output_dir, "flask_minimal_extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        processor = ApplicationProcessor(extract_dir, "flask")
        assert processor.check_project() is True

    def test_flask_minimal_zip_rockcraft_generation(self, flask_minimal_zip, mock_popen):
        """Test: Generate rockcraft.yaml from Flask ZIP."""
        result = flask_minimal_zip()
        zip_path = result["zip_path"]
        output_dir = result["output_dir"]
        project_name = result["project_name"]
        
        extract_dir = os.path.join(output_dir, "flask_minimal_extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        processor = ApplicationProcessor(extract_dir, "flask")
        processor.check_project()
        
        rock_gen = RockcraftGenerator(extract_dir, project_name, "flask")
        yaml_path = rock_gen.init_rockcraft()
        
        assert os.path.exists(yaml_path)
        validate_rockcraft_yaml(yaml_path)

    def test_flask_minimal_zip_charmcraft_initialization(self, flask_minimal_zip, mock_popen):
        """Test: Initialize charmcraft from Flask ZIP."""
        result = flask_minimal_zip()
        zip_path = result["zip_path"]
        output_dir = result["output_dir"]
        project_name = result["project_name"]
        
        extract_dir = os.path.join(output_dir, "flask_minimal_extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        processor = ApplicationProcessor(extract_dir, "flask")
        processor.check_project()
        
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=extract_dir,
            project_name=project_name,
        )
        yaml_path, temp_dir = charm_gen.init_charmcraft()
        
        assert os.path.exists(yaml_path)
        validate_charmcraft_yaml(yaml_path)

    def test_flask_minimal_zip_full_workflow(self, flask_minimal_zip, mock_popen):
        """Test: Full workflow with Flask ZIP."""
        result = flask_minimal_zip()
        zip_path = result["zip_path"]
        output_dir = result["output_dir"]
        project_name = result["project_name"]
        
        extract_dir = os.path.join(output_dir, "flask_minimal_extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        processor = ApplicationProcessor(extract_dir, "flask")
        assert processor.check_project() is True
        
        rock_gen = RockcraftGenerator(extract_dir, project_name, "flask")
        rock_yaml_path = rock_gen.init_rockcraft()
        assert os.path.exists(rock_yaml_path)
        validate_rockcraft_yaml(rock_yaml_path)
        
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=extract_dir,
            project_name=project_name,
        )
        charm_yaml_path, charm_temp_dir = charm_gen.init_charmcraft()
        assert os.path.exists(charm_yaml_path)
        validate_charmcraft_yaml(charm_yaml_path)
        
        charm_gen.cleanup()


@pytest.mark.e2e
@pytest.mark.slow
class TestZipMethodDjango:
    """E2E tests for Django example using ZIP method."""

    def test_django_zip_validation(self, django_zip, mock_popen):
        """Test: Extract and validate django from ZIP."""
        result = django_zip()
        zip_path = result["zip_path"]
        output_dir = result["output_dir"]
        
        extract_dir = os.path.join(output_dir, "django_extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        processor = ApplicationProcessor(extract_dir, "django")
        assert processor.check_project() is True

    def test_django_zip_rockcraft_generation(self, django_zip, mock_popen):
        """Test: Generate rockcraft.yaml from Django ZIP."""
        result = django_zip()
        zip_path = result["zip_path"]
        output_dir = result["output_dir"]
        project_name = result["project_name"]
        
        extract_dir = os.path.join(output_dir, "django_extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        processor = ApplicationProcessor(extract_dir, "django")
        processor.check_project()
        
        rock_gen = RockcraftGenerator(extract_dir, project_name, "django")
        yaml_path = rock_gen.init_rockcraft()
        
        assert os.path.exists(yaml_path)
        validate_rockcraft_yaml(yaml_path)

    def test_django_zip_charmcraft_initialization(self, django_zip, mock_popen):
        """Test: Initialize charmcraft from Django ZIP."""
        result = django_zip()
        zip_path = result["zip_path"]
        output_dir = result["output_dir"]
        project_name = result["project_name"]
        
        extract_dir = os.path.join(output_dir, "django_extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        processor = ApplicationProcessor(extract_dir, "django")
        processor.check_project()
        
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=extract_dir,
            project_name=project_name,
        )
        yaml_path, temp_dir = charm_gen.init_charmcraft()
        
        assert os.path.exists(yaml_path)
        validate_charmcraft_yaml(yaml_path)

    def test_django_zip_full_workflow(self, django_zip, mock_popen):
        """Test: Full workflow with Django ZIP."""
        result = django_zip()
        zip_path = result["zip_path"]
        output_dir = result["output_dir"]
        project_name = result["project_name"]
        
        extract_dir = os.path.join(output_dir, "django_extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        
        processor = ApplicationProcessor(extract_dir, "django")
        assert processor.check_project() is True
        
        rock_gen = RockcraftGenerator(extract_dir, project_name, "django")
        rock_yaml_path = rock_gen.init_rockcraft()
        assert os.path.exists(rock_yaml_path)
        validate_rockcraft_yaml(rock_yaml_path)
        
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=extract_dir,
            project_name=project_name,
        )
        charm_yaml_path, charm_temp_dir = charm_gen.init_charmcraft()
        assert os.path.exists(charm_yaml_path)
        validate_charmcraft_yaml(charm_yaml_path)
        
        charm_gen.cleanup()
