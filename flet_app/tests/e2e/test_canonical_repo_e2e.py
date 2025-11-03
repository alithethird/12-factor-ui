"""End-to-end tests using real canonical/paas-charm GitHub repository.

This test suite downloads actual Flask examples from the canonical/paas-charm
repository and tests the complete workflow including:
- Project validation
- Rockcraft YAML generation and rock packing
- Charmcraft YAML generation and charm packing
- Bundle creation with rock + charm files
"""

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
from logic.bundler import BundleArtifacts


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


def validate_bundle_zip(zip_path: str) -> dict:
    """Validate bundle ZIP contains both rock and charm files."""
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Bundle ZIP not found at {zip_path}")
    
    if not zipfile.is_zipfile(zip_path):
        raise ValueError(f"File at {zip_path} is not a valid ZIP file")
    
    with zipfile.ZipFile(zip_path, "r") as zf:
        files = zf.namelist()
    
    has_rock = any(f.endswith(".rock") for f in files)
    has_charm = any(f.endswith(".charm") for f in files)
    
    if not has_rock:
        raise ValueError(f"Bundle ZIP does not contain a .rock file. Contents: {files}")
    if not has_charm:
        raise ValueError(f"Bundle ZIP does not contain a .charm file. Contents: {files}")
    
    return {"rock_files": [f for f in files if f.endswith(".rock")],
            "charm_files": [f for f in files if f.endswith(".charm")]}


@pytest.mark.e2e
@pytest.mark.slow
class TestCanonicalRepoFlaskMinimal:
    """E2E tests using real canonical/paas-charm Flask example.
    
    This test suite downloads the actual Flask example from:
    https://github.com/canonical/paas-charm/tree/main/examples/flask-minimal/flask_minimal_app
    
    Tests verify the complete workflow including packing rock and charm files,
    and creating a bundle.
    """

    def test_flask_minimal_download_and_validate(self, download_canonical_flask_minimal, temp_project_dir):
        """Test: Download canonical Flask example and validate it."""
        result = download_canonical_flask_minimal()
        project_path = result["path"]
        
        assert os.path.exists(project_path), f"Downloaded project not found at {project_path}"
        assert os.path.exists(os.path.join(project_path, "requirements.txt")), \
            "Downloaded project missing requirements.txt"
        
        processor = ApplicationProcessor(project_path, "flask")
        assert processor.check_project() is True, "Flask project validation failed"

    def test_flask_minimal_rockcraft_init(self, download_canonical_flask_minimal, temp_project_dir):
        """Test: Initialize rockcraft.yaml from canonical Flask example."""
        result = download_canonical_flask_minimal()
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "flask")
        processor.check_project()
        
        rock_gen = RockcraftGenerator(project_path, project_name, "flask")
        yaml_path = rock_gen.init_rockcraft()
        
        assert os.path.exists(yaml_path), "rockcraft.yaml not created"
        validate_rockcraft_yaml(yaml_path)

    def test_flask_minimal_rockcraft_pack(self, download_canonical_flask_minimal, temp_project_dir, mock_pack_commands_popen):
        """Test: Pack rock file from canonical Flask example."""
        result = download_canonical_flask_minimal()
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "flask")
        processor.check_project()
        
        rock_gen = RockcraftGenerator(project_path, project_name, "flask")
        rock_gen.init_rockcraft()
        
        rock_file = rock_gen.pack_rockcraft()
        
        assert os.path.exists(rock_file), f"Rock file not created at {rock_file}"
        assert rock_file.endswith(".rock"), f"Invalid rock file name: {rock_file}"

    def test_flask_minimal_charmcraft_init(self, download_canonical_flask_minimal, temp_project_dir, mock_pack_commands_popen):
        """Test: Initialize charmcraft from canonical Flask example."""
        result = download_canonical_flask_minimal()
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
        
        charm_gen.cleanup()

    def test_flask_minimal_charmcraft_pack(self, download_canonical_flask_minimal, temp_project_dir, mock_pack_commands_popen):
        """Test: Pack charm file from canonical Flask example."""
        result = download_canonical_flask_minimal()
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
        charm_gen.init_charmcraft()
        
        charm_file = charm_gen.pack_charmcraft()
        
        assert os.path.exists(charm_file), f"Charm file not created at {charm_file}"
        assert charm_file.endswith(".charm"), f"Invalid charm file name: {charm_file}"
        
        charm_gen.cleanup()

    def test_flask_minimal_full_workflow_with_packing(self, download_canonical_flask_minimal, temp_project_dir, mock_pack_commands_popen):
        """Test: Complete workflow - download, validate, pack rock and charm.
        
        This is the main comprehensive test that verifies:
        1. Download from canonical/paas-charm GitHub repo
        2. Validate the Flask application
        3. Generate and pack the rock file
        4. Generate and pack the charm file
        """
        result = download_canonical_flask_minimal()
        project_path = result["path"]
        project_name = result["project_name"]
        
        # --- Validate Project ---
        processor = ApplicationProcessor(project_path, "flask")
        assert processor.check_project() is True, "Flask project validation failed"
        
        # --- Generate and Pack Rock ---
        rock_gen = RockcraftGenerator(project_path, project_name, "flask")
        rock_yaml_path = rock_gen.init_rockcraft()
        assert os.path.exists(rock_yaml_path), "rockcraft.yaml not created"
        validate_rockcraft_yaml(rock_yaml_path)
        
        rock_file = rock_gen.pack_rockcraft()
        assert os.path.exists(rock_file), f"Rock file not created at {rock_file}"
        assert rock_file.endswith(".rock"), f"Invalid rock file: {rock_file}"
        
        # --- Generate and Pack Charm ---
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=project_path,
            project_name=project_name,
        )
        charm_yaml_path, charm_temp_dir = charm_gen.init_charmcraft()
        assert os.path.exists(charm_yaml_path), "charmcraft.yaml not created"
        validate_charmcraft_yaml(charm_yaml_path)
        
        charm_file = charm_gen.pack_charmcraft()
        assert os.path.exists(charm_file), f"Charm file not created at {charm_file}"
        assert charm_file.endswith(".charm"), f"Invalid charm file: {charm_file}"
        
        # --- Bundle Rock + Charm ---
        bundle_path, cleanup = BundleArtifacts(rock_file, charm_file)
        assert os.path.exists(bundle_path), f"Bundle not created at {bundle_path}"
        assert bundle_path.endswith(".zip"), f"Invalid bundle file: {bundle_path}"
        
        # Validate bundle contents
        bundle_contents = validate_bundle_zip(bundle_path)
        assert len(bundle_contents["rock_files"]) > 0, "Bundle does not contain rock file"
        assert len(bundle_contents["charm_files"]) > 0, "Bundle does not contain charm file"
        
        # Cleanup
        cleanup()
        charm_gen.cleanup()
        
        assert not os.path.exists(bundle_path), "Bundle cleanup failed"

    def test_flask_minimal_bundle_contents(self, download_canonical_flask_minimal, temp_project_dir, mock_pack_commands_popen):
        """Test: Verify bundle ZIP contains correct rock and charm files.
        
        Validates that the bundle has:
        - Exactly one .rock file
        - Exactly one .charm file
        - Correct file names based on project name
        """
        result = download_canonical_flask_minimal()
        project_path = result["path"]
        project_name = result["project_name"]
        
        processor = ApplicationProcessor(project_path, "flask")
        processor.check_project()
        
        # Pack rock
        rock_gen = RockcraftGenerator(project_path, project_name, "flask")
        rock_gen.init_rockcraft()
        rock_file = rock_gen.pack_rockcraft()
        
        # Pack charm
        charm_gen = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=project_path,
            project_name=project_name,
        )
        charm_gen.init_charmcraft()
        charm_file = charm_gen.pack_charmcraft()
        
        # Create bundle
        bundle_path, cleanup = BundleArtifacts(rock_file, charm_file)
        
        # Verify bundle contents
        with zipfile.ZipFile(bundle_path, "r") as zf:
            files = zf.namelist()
            rock_files = [f for f in files if f.endswith(".rock")]
            charm_files = [f for f in files if f.endswith(".charm")]
            
            assert len(rock_files) == 1, f"Expected 1 .rock file, got {len(rock_files)}: {rock_files}"
            assert len(charm_files) == 1, f"Expected 1 .charm file, got {len(charm_files)}: {charm_files}"
            
            # Verify file names are basenames (not full paths)
            assert os.sep not in rock_files[0], f"Rock file should not contain path separators: {rock_files[0]}"
            assert os.sep not in charm_files[0], f"Charm file should not contain path separators: {charm_files[0]}"
        
        # Cleanup
        cleanup()
        charm_gen.cleanup()
