"""Unit tests for RockcraftGenerator."""
from pathlib import Path
from unittest.mock import patch

import pytest

from logic.rockcraft import RockcraftGenerator
from tests.mocks.command_mocker import MockSubprocessPopen, create_status_callback_mock


@pytest.mark.unit
class TestRockcraftGenerator:
    """Test suite for RockcraftGenerator class."""

    def test_init_stores_configuration(self, temp_project_dir):
        """Test that initialization stores project configuration."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock-project",
            framework="python-framework",
        )

        assert generator.project_path == temp_project_dir
        assert generator.framework == "python-framework"
        assert generator.project_name == "test-rock-project"

    def test_project_name_normalization(self, temp_project_dir):
        """Test that project names are normalized correctly."""
        test_cases = [
            ("test_rock", "test-rock"),
            ("Test Rock", "test-rock"),
            ("TEST_ROCK", "test-rock"),
            ("test rock project", "test-rock-project"),
            ("test_Rock_Project", "test-rock-project"),
        ]

        for input_name, expected_name in test_cases:
            generator = RockcraftGenerator(
                project_path=temp_project_dir,
                project_name=input_name,
                framework="python-framework",
            )
            assert generator.project_name == expected_name

    def test_init_rockcraft_creates_yaml(self, temp_project_dir, mock_which, mock_popen):
        """Test that init_rockcraft creates rockcraft.yaml."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        # Mock needs to create the yaml file when init runs
        returned_path = generator.init_rockcraft()

        assert Path(returned_path).exists()
        assert returned_path.endswith("rockcraft.yaml")

    def test_init_rockcraft_removes_existing_yaml(self, temp_project_dir, mock_which, mock_popen):
        """Test that init_rockcraft removes existing rockcraft.yaml."""
        yaml_path = Path(temp_project_dir) / "rockcraft.yaml"
        yaml_path.write_text("old: content\n")

        assert yaml_path.exists()

        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        # After init, yaml file should exist (removed and recreated by mock)
        returned_path = generator.init_rockcraft()

        # File should be recreated
        assert Path(returned_path).exists()

    def test_pack_rockcraft_finds_artifact(self, temp_project_dir, mock_which, mock_popen):
        """Test that pack_rockcraft locates the generated .rock file."""
        # First create the rockcraft.yaml so mock knows the project name
        yaml_path = Path(temp_project_dir) / "rockcraft.yaml"
        yaml_path.write_text("name: test-rock\nversion: 1.0\n")

        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        returned_path = generator.pack_rockcraft()

        assert Path(returned_path).exists()
        assert returned_path.endswith(".rock")

    def test_pack_rockcraft_missing_artifact_raises_error(self, temp_project_dir, mock_which):
        """Test that pack_rockcraft raises error if .rock file not found."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        # Don't use mock_popen here - instead patch it to not create artifacts
        with patch("subprocess.Popen") as mock_popen:
            mock_instance = MockSubprocessPopen(
                ["rockcraft", "pack"],
                cwd=temp_project_dir,
            )
            mock_instance._should_create_artifact = False
            mock_popen.return_value = mock_instance

            with pytest.raises(FileNotFoundError):
                generator.pack_rockcraft()

    def test_run_command_with_status_callback(self, temp_project_dir, mock_which, mock_popen):
        """Test that _run_command calls status callback."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        callback, call_list = create_status_callback_mock()

        generator._run_command(["rockcraft", "pack"], status_callback=callback)

        # Verify callback was called at least once
        assert len(call_list) > 0

    def test_run_command_failure_raises_exception(self, temp_project_dir, mock_which):
        """Test that _run_command raises exception on failure."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_instance = MockSubprocessPopen(
                ["rockcraft", "pack"],
                cwd=temp_project_dir,
            )
            mock_instance.returncode = 1
            mock_popen.return_value = mock_instance

            with pytest.raises(Exception):
                generator._run_command(["rockcraft", "pack"])

    def test_init_rockcraft_exception_handling(self, temp_project_dir, mock_which):
        """Test error handling when init fails."""
        generator = RockcraftGenerator(
            project_path=temp_project_dir,
            project_name="test-rock",
            framework="python-framework",
        )

        with patch("subprocess.Popen") as mock_popen:
            mock_instance = MockSubprocessPopen(
                ["rockcraft", "init"],
                cwd=temp_project_dir,
            )
            mock_instance.returncode = 1
            mock_popen.return_value = mock_instance

            with pytest.raises(Exception):
                generator.init_rockcraft()
