"""Mock artifact creation utilities for testing."""
import os
import zipfile
from pathlib import Path


def create_mock_rock_file(directory: str, rock_name: str) -> str:
    """
    Create a minimal mock .rock file.

    Args:
        directory: Directory where the .rock file should be created
        rock_name: Name of the rock (without .rock extension)

    Returns:
        Path to the created .rock file
    """
    rock_path = Path(directory) / f"{rock_name}.rock"
    # Create a minimal OCI image-like structure (empty file for testing)
    rock_path.write_text("mock-rock-image")
    return str(rock_path)


def create_mock_charm_file(directory: str, charm_name: str) -> str:
    """
    Create a minimal mock .charm file (ZIP archive with required structure).

    Args:
        directory: Directory where the .charm file should be created
        charm_name: Name of the charm (without .charm extension)

    Returns:
        Path to the created .charm file
    """
    charm_path = Path(directory) / f"{charm_name}.charm"

    # Create a minimal valid charm ZIP with required structure
    with zipfile.ZipFile(charm_path, "w") as charm_zip:
        # Add minimal required files for a charm
        charm_zip.writestr("metadata.yaml", "name: test-charm\n")
        charm_zip.writestr("actions.yaml", "{}\n")
        charm_zip.writestr("src/charm.py", "#!/usr/bin/env python3\n")

    return str(charm_path)
