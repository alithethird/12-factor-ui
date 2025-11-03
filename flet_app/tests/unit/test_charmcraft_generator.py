"""Unit tests for CharmcraftGenerator."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from logic.charmcraft import CharmcraftGenerator
from tests.mocks.command_mocker import MockSubprocessPopen, create_status_callback_mock


@pytest.mark.unit
class TestCharmcraftGenerator:
    """Test suite for CharmcraftGenerator class."""

    def test_init_creates_charm_directory(self, temp_project_dir):
        """Test that initialization creates the charm project directory."""
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        assert generator.charm_project_path.exists()
        assert str(generator.charm_project_path).endswith("charm")

    def test_init_with_integrations(self, temp_project_dir):
        """Test initialization with integrations."""
        integrations = ["postgresql", "prometheus"]
        generator = CharmcraftGenerator(
            integrations=integrations,
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        assert generator.integrations == integrations

    def test_init_with_config_options(self, temp_project_dir):
        """Test initialization with configuration options."""
        config_options = [
            {"key": "port", "type": "int", "value": "8000"},
            {"key": "debug", "type": "bool", "value": "false"},
        ]
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=config_options,
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        assert generator.config_options == config_options

    def test_init_charmcraft_creates_yaml(self, temp_project_dir, mock_which, mock_popen):
        """Test that init_charmcraft creates the charmcraft.yaml file."""
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        returned_path, returned_dir = generator.init_charmcraft()

        assert Path(returned_path).exists()
        assert returned_path.endswith("charmcraft.yaml")

    def test_update_charmcraft_yaml_with_integrations(self, temp_project_dir):
        """Test updating charmcraft.yaml with integrations."""
        generator = CharmcraftGenerator(
            integrations=["postgresql", "prometheus"],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        # Create initial YAML
        yaml_path = generator.charm_project_path / "charmcraft.yaml"
        initial_yaml = {"name": "test-charm", "type": "bundle"}
        with open(yaml_path, "w") as f:
            yaml.dump(initial_yaml, f)

        # Update YAML
        generator.update_charmcraft_yaml(str(yaml_path))

        # Verify updates
        with open(yaml_path, "r") as f:
            updated_yaml = yaml.safe_load(f)

        assert "requires" in updated_yaml
        assert "db" in updated_yaml["requires"]
        assert "metrics-endpoint" in updated_yaml["requires"]

    @patch("subprocess.Popen")
    def test_update_charmcraft_yaml_with_config_options(self, mock_popen, temp_project_dir):
        """Test updating charmcraft.yaml with config options."""
        config_options = [
            {"key": "port", "type": "int", "value": "8000", "isOptional": True},
            {"key": "app-name", "type": "string", "value": "myapp", "isOptional": False},
        ]

        generator = CharmcraftGenerator(
            integrations=[],
            config_options=config_options,
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        # Create initial YAML
        yaml_path = generator.charm_project_path / "charmcraft.yaml"
        initial_yaml = {"name": "test-charm", "type": "bundle"}
        with open(yaml_path, "w") as f:
            yaml.dump(initial_yaml, f)

        # Update YAML
        generator.update_charmcraft_yaml(str(yaml_path))

        # Verify updates
        with open(yaml_path, "r") as f:
            updated_yaml = yaml.safe_load(f)

        assert "options" in updated_yaml
        assert "port" in updated_yaml["options"]
        assert updated_yaml["options"]["port"]["type"] == "int"
        assert updated_yaml["options"]["port"]["default"] == 8000

    def test_get_typed_value_int(self, temp_project_dir):
        """Test _get_typed_value conversion to int."""
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        result = generator._get_typed_value("8000", "int")
        assert result == 8000
        assert isinstance(result, int)

    def test_get_typed_value_bool_true(self, temp_project_dir):
        """Test _get_typed_value conversion to bool (true)."""
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        for value in ["true", "1", "yes"]:
            result = generator._get_typed_value(value, "bool")
            assert result is True

    def test_get_typed_value_bool_false(self, temp_project_dir):
        """Test _get_typed_value conversion to bool (false)."""
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        for value in ["false", "0", "no"]:
            result = generator._get_typed_value(value, "bool")
            assert result is False

    def test_cleanup_removes_directory(self, temp_project_dir):
        """Test that cleanup removes the temporary directory."""
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        # Create a file in the temp directory
        test_file = Path(temp_project_dir) / "test.txt"
        test_file.write_text("test content")

        assert Path(temp_project_dir).exists()
        generator.cleanup()
        assert not Path(temp_project_dir).exists()

    @patch("subprocess.Popen")
    def test_run_command_failure_raises_exception(self, mock_popen, temp_project_dir):
        """Test that _run_command raises exception on failure."""
        # Create mock that simulates failure
        mock_instance = MockSubprocessPopen(
            ["charmcraft", "init"],
            cwd=temp_project_dir,
        )
        mock_instance.returncode = 1
        mock_popen.return_value = mock_instance

        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        with pytest.raises(Exception):
            generator._run_command(
                ["charmcraft", "init"],
                cwd=temp_project_dir,
            )

    def test_run_command_with_status_callback(self, temp_project_dir, mock_which, mock_popen):
        """Test that _run_command calls status callback."""
        generator = CharmcraftGenerator(
            integrations=[],
            config_options=[],
            project_path=temp_project_dir,
            project_name="test-charm",
        )

        callback, call_list = create_status_callback_mock()

        generator._run_command(
            ["charmcraft", "init"],
            cwd=temp_project_dir,
            status_callback=callback,
        )

        # Verify callback was called at least once
        assert len(call_list) > 0
