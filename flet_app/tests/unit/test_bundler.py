"""Unit tests for BundleArtifacts function."""
from pathlib import Path
from zipfile import ZipFile

import pytest

from logic.bundler import BundleArtifacts


@pytest.mark.unit
class TestBundleArtifacts:
    """Test suite for BundleArtifacts function."""

    def test_creates_zip_file_with_both_artifacts(self, temp_project_dir):
        """Test that BundleArtifacts creates a ZIP containing both rock and charm."""
        # Create mock artifact files
        rock_path = Path(temp_project_dir) / "test.rock"
        charm_path = Path(temp_project_dir) / "test.charm"

        rock_path.write_text("mock-rock-content")
        charm_path.write_text("mock-charm-content")

        # Bundle artifacts
        zip_path, cleanup_func = BundleArtifacts(str(rock_path), str(charm_path))

        # Verify ZIP file was created
        assert Path(zip_path).exists()
        assert zip_path.endswith(".zip")

        # Verify contents
        with ZipFile(zip_path, "r") as zf:
            file_list = zf.namelist()
            assert "test.rock" in file_list
            assert "test.charm" in file_list

            # Verify file contents
            assert zf.read("test.rock") == b"mock-rock-content"
            assert zf.read("test.charm") == b"mock-charm-content"

        # Cleanup
        cleanup_func()
        assert not Path(zip_path).exists()

    def test_cleanup_function_removes_zip(self, temp_project_dir):
        """Test that cleanup function properly removes the ZIP file."""
        rock_path = Path(temp_project_dir) / "test.rock"
        charm_path = Path(temp_project_dir) / "test.charm"

        rock_path.write_text("mock-rock")
        charm_path.write_text("mock-charm")

        zip_path, cleanup_func = BundleArtifacts(str(rock_path), str(charm_path))

        # Verify ZIP exists
        assert Path(zip_path).exists()

        # Call cleanup
        cleanup_func()

        # Verify ZIP is deleted
        assert not Path(zip_path).exists()

    def test_error_with_missing_rock_file(self, temp_project_dir):
        """Test that BundleArtifacts handles missing rock file."""
        rock_path = Path(temp_project_dir) / "nonexistent.rock"
        charm_path = Path(temp_project_dir) / "test.charm"

        charm_path.write_text("mock-charm")

        with pytest.raises(FileNotFoundError):
            BundleArtifacts(str(rock_path), str(charm_path))

    def test_error_with_missing_charm_file(self, temp_project_dir):
        """Test that BundleArtifacts handles missing charm file."""
        rock_path = Path(temp_project_dir) / "test.rock"
        charm_path = Path(temp_project_dir) / "nonexistent.charm"

        rock_path.write_text("mock-rock")

        with pytest.raises(FileNotFoundError):
            BundleArtifacts(str(rock_path), str(charm_path))

    def test_zip_contains_basename_not_full_path(self, temp_project_dir):
        """Test that ZIP entries use basenames, not full paths."""
        # Create artifacts in subdirectories
        subdir1 = Path(temp_project_dir) / "subdir1"
        subdir2 = Path(temp_project_dir) / "subdir2"
        subdir1.mkdir()
        subdir2.mkdir()

        rock_path = subdir1 / "my-rock.rock"
        charm_path = subdir2 / "my-charm.charm"

        rock_path.write_text("rock-content")
        charm_path.write_text("charm-content")

        zip_path, cleanup_func = BundleArtifacts(str(rock_path), str(charm_path))

        # Verify only basenames are in ZIP
        with ZipFile(zip_path, "r") as zf:
            file_list = zf.namelist()
            assert "my-rock.rock" in file_list
            assert "my-charm.charm" in file_list
            # Verify no subdirectory paths are included
            assert not any("subdir" in f for f in file_list)

        cleanup_func()

    def test_multiple_bundlings_create_separate_zips(self, temp_project_dir):
        """Test that multiple bundlings create separate ZIP files."""
        # First bundle
        rock_path1 = Path(temp_project_dir) / "rock1.rock"
        charm_path1 = Path(temp_project_dir) / "charm1.charm"
        rock_path1.write_text("rock1")
        charm_path1.write_text("charm1")

        zip_path1, cleanup_func1 = BundleArtifacts(str(rock_path1), str(charm_path1))

        # Second bundle
        rock_path2 = Path(temp_project_dir) / "rock2.rock"
        charm_path2 = Path(temp_project_dir) / "charm2.charm"
        rock_path2.write_text("rock2")
        charm_path2.write_text("charm2")

        zip_path2, cleanup_func2 = BundleArtifacts(str(rock_path2), str(charm_path2))

        # Verify they're different files
        assert zip_path1 != zip_path2
        assert Path(zip_path1).exists()
        assert Path(zip_path2).exists()

        # Cleanup
        cleanup_func1()
        cleanup_func2()

        assert not Path(zip_path1).exists()
        assert not Path(zip_path2).exists()

    def test_zip_preserves_file_contents(self, temp_project_dir):
        """Test that ZIP preserves exact file contents."""
        rock_path = Path(temp_project_dir) / "test.rock"
        charm_path = Path(temp_project_dir) / "test.charm"

        # Use binary-like content
        rock_content = b"\x89PNG\r\n\x1a\n" + b"mock-rock-data"
        charm_content = "# Charm metadata\nname: test\n".encode()

        rock_path.write_bytes(rock_content)
        charm_path.write_bytes(charm_content)

        zip_path, cleanup_func = BundleArtifacts(str(rock_path), str(charm_path))

        with ZipFile(zip_path, "r") as zf:
            assert zf.read("test.rock") == rock_content
            assert zf.read("test.charm") == charm_content

        cleanup_func()
