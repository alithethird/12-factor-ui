"""Integration tests for complete generation workflow."""
from pathlib import Path
from unittest.mock import patch
import yaml

import pytest

from logic.bundler import BundleArtifacts
from logic.charmcraft import CharmcraftGenerator
from logic.rockcraft import RockcraftGenerator
from tests.mocks.command_mocker import MockSubprocessPopen, create_status_callback_mock


@pytest.mark.integration
class TestGenerationWorkflow:
    """Integration tests for the complete rock and charm generation workflow."""

    def test_rockcraft_generation_workflow(self, temp_project_dir, mock_which, mock_popen):
        """Test the complete rockcraft initialization and packing workflow."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        callback, call_list = create_status_callback_mock()

        # Test init workflow
        init_result = generator.init_rockcraft(status_callback=callback)

        assert init_result.endswith("rockcraft.yaml")
        assert Path(init_result).exists()

        # Test pack workflow
        pack_result = generator.pack_rockcraft(status_callback=callback)

        assert pack_result.endswith(".rock")
        assert Path(pack_result).exists()

    def test_charmcraft_generation_workflow(self, temp_project_dir, mock_which, mock_popen):
        """Test the complete charmcraft initialization and packing workflow."""
        generator = CharmcraftGenerator(
            integrations=["postgresql"],
            config_options=[{"key": "port", "type": "int", "value": "8000"}],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        callback, call_list = create_status_callback_mock()

        # Test init workflow
        init_result, temp_dir = generator.init_charmcraft(status_callback=callback)

        assert init_result.endswith("charmcraft.yaml")
        assert Path(init_result).exists()

        # Test YAML update
        generator.update_charmcraft_yaml(init_result, status_callback=callback)

        with open(init_result, "r") as f:
            updated_yaml = yaml.safe_load(f)

        assert "requires" in updated_yaml
        assert "options" in updated_yaml
        assert "port" in updated_yaml["options"]

        # Test pack workflow
        pack_result = generator.pack_charmcraft(status_callback=callback)

        assert pack_result.endswith(".charm")
        assert Path(pack_result).exists()

    def test_full_rock_charm_and_bundle_workflow(self, temp_project_dir, mock_which, mock_popen):
        """Test the complete workflow: rock generation -> charm generation -> bundling."""
        # Step 1: Generate rock
        rock_generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        rock_generator.init_rockcraft()
        rock_path = rock_generator.pack_rockcraft()

        assert Path(rock_path).exists()

        # Step 2: Generate charm
        charm_generator = CharmcraftGenerator(
            integrations=["postgresql"],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        charm_yaml_path, _ = charm_generator.init_charmcraft()
        charm_generator.update_charmcraft_yaml(charm_yaml_path)
        charm_path = charm_generator.pack_charmcraft()

        assert Path(charm_path).exists()

        # Step 3: Bundle both artifacts
        zip_path = BundleArtifacts(rock_path, charm_path)

        assert Path(zip_path).exists()
        assert zip_path.endswith(".zip")

        # Verify bundle contents
        from zipfile import ZipFile

        with ZipFile(zip_path, "r") as zf:
            files = zf.namelist()
            assert any("rock" in f for f in files)
            assert any("charm" in f for f in files)

        # Cleanup
        assert not Path(zip_path).exists()

    def test_error_handling_in_rock_workflow(self, temp_project_dir, mock_which):
        """Test error handling when rock generation fails."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        # Simulate init failure by patching _run_command
        with patch.object(generator, "_run_command", side_effect=Exception("Init failed")):
            with pytest.raises(Exception):
                generator.init_rockcraft()

    def test_error_handling_in_charm_workflow(self, temp_project_dir, mock_which):
        """Test error handling when charm generation fails."""
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        # Simulate init failure
        with patch.object(generator, "_run_command", side_effect=Exception("Init failed")):
            with pytest.raises(Exception):
                generator.init_charmcraft()

    def test_status_callbacks_throughout_workflow(self, temp_project_dir, mock_which, mock_popen):
        """Test that status callbacks are properly invoked throughout the workflow."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        callback, call_list = create_status_callback_mock()

        # First initialize
        generator.init_rockcraft(status_callback=callback)

        # Clear the callback list to check pack callbacks
        call_list.clear()

        # Then pack
        generator.pack_rockcraft(status_callback=callback)

        # Verify callbacks were invoked
        assert len(call_list) > 0
        messages = [call["message"] for call in call_list]
        assert any("rock" in msg.lower() or "Rock" in msg for msg in messages)

    @patch("subprocess.Popen")
    def test_multiple_integrations_in_charm(self, mock_popen, temp_project_dir):
        """Test charm generation with multiple integrations."""
        charm_dir = Path(temp_project_dir) / "charm"
        charm_dir.mkdir()

        integrations = ["postgresql", "prometheus"]
        generator = CharmcraftGenerator(
            integrations=integrations,
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        # Create initial YAML
        yaml_path = charm_dir / "charmcraft.yaml"
        initial_yaml = {"name": "test-charm"}
        with open(yaml_path, "w") as f:
            yaml.dump(initial_yaml, f)

        # Update with integrations
        generator.update_charmcraft_yaml(str(yaml_path))

        with open(yaml_path, "r") as f:
            updated_yaml = yaml.safe_load(f)

        assert "requires" in updated_yaml
        assert len(updated_yaml["requires"]) >= 1

    @patch("subprocess.Popen")
    def test_workflow_with_complex_config_options(self, mock_popen, temp_project_dir):
        """Test charm workflow with complex configuration options."""
        charm_dir = Path(temp_project_dir) / "charm"
        charm_dir.mkdir()

        config_options = [
            {"key": "port", "type": "int", "value": "8080", "isOptional": True},
            {"key": "debug", "type": "bool", "value": "true", "isOptional": True},
            {"key": "app-name", "type": "string", "value": "myapp", "isOptional": False},
            {"key": "timeout", "type": "float", "value": "30.5", "isOptional": True},
        ]

        generator = CharmcraftGenerator(
            integrations=[],
            config_options=config_options,
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        yaml_path = charm_dir / "charmcraft.yaml"
        initial_yaml = {"name": "test-charm"}
        with open(yaml_path, "w") as f:
            yaml.dump(initial_yaml, f)

        generator.update_charmcraft_yaml(str(yaml_path))

        with open(yaml_path, "r") as f:
            updated_yaml = yaml.safe_load(f)

        assert "options" in updated_yaml
        assert updated_yaml["options"]["port"]["default"] == 8080
        assert updated_yaml["options"]["debug"]["default"] is True
        assert updated_yaml["options"]["timeout"]["default"] == 30.5
