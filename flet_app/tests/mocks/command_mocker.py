"""Smart command mocking for charmcraft and rockcraft commands."""
import os
import time
import threading
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

from .mock_artifacts import create_mock_charm_file, create_mock_rock_file


class MockStdout:
    """Mock stdout that supports readline() iteration for subprocess output."""

    def __init__(self, output_lines):
        """Initialize with output lines."""
        self.lines = output_lines
        self.line_index = 0

    def readline(self):
        """Return next line or empty string when exhausted."""
        if self.line_index < len(self.lines):
            line = self.lines[self.line_index]
            self.line_index += 1
            return line
        return ""

    def close(self):
        """Close the stream."""
        pass


class MockSubprocessPopen:
    """Mock subprocess.Popen that simulates command execution with artifact creation."""

    def __init__(self, args, cwd=None, stdout=None, stderr=None, text=None, bufsize=None, env=None):
        """Initialize the mock process."""
        self.args = args
        self.cwd = cwd or os.getcwd()
        self.returncode = 0
        self._output_lines = self._generate_output_lines()
        self._process_started = False
        self._should_create_artifact = True
        # Create a custom stdout object that supports iteration
        self.stdout = MockStdout(self._output_lines)

    def _generate_output_lines(self):
        """Generate mock output lines based on command."""
        command = self.args[-1] if isinstance(self.args, list) else str(self.args)

        if "init" in command:
            return [
                "Initializing project...\n",
                "Creating directories...\n",
                "Setting up configuration...\n",
                "Initialization complete.\n",
            ]
        elif "pack" in command:
            return [
                "Packing project...\n",
                "Processing artifacts...\n",
                "Building package...\n",
                "Finalizing...\n",
            ]
        else:
            return ["Processing...\n"]

    def close(self):
        """Close the mock process output."""
        if hasattr(self.stdout, "close"):
            self.stdout.close()

    def wait(self, timeout=None):
        """Wait for the mock process to complete and create artifacts."""
        if not self._process_started:
            self._process_started = True

            # Create artifacts in a background thread to simulate actual command execution
            def create_artifacts():
                time.sleep(0.1)  # Brief delay to simulate work
                if self._should_create_artifact:
                    self._create_mock_artifacts()

            thread = threading.Thread(target=create_artifacts, daemon=True)
            thread.start()
            thread.join(timeout=5)  # Wait up to 5 seconds for artifact creation

        return self.returncode

    def _create_mock_artifacts(self):
        """Create mock .rock or .charm files based on command."""
        command = " ".join(self.args) if isinstance(self.args, list) else str(self.args)

        if "rockcraft" in command and "init" in command:
            # Create a basic rockcraft.yaml file
            yaml_path = Path(self.cwd) / "rockcraft.yaml"
            yaml_content = """name: test-rock
version: 1.0
base: ubuntu@22.04
summary: Test rock
description: A test rock for unit testing.
"""
            yaml_path.write_text(yaml_content)

        elif "rockcraft" in command and "pack" in command:
            # Extract project name from rockcraft.yaml if it exists
            yaml_path = Path(self.cwd) / "rockcraft.yaml"
            if yaml_path.exists():
                with open(yaml_path, "r") as f:
                    content = f.read()
                    # Simple parsing to get name (assumes format: name: <name>)
                    for line in content.split("\n"):
                        if line.startswith("name:"):
                            project_name = line.split(":", 1)[1].strip()
                            create_mock_rock_file(self.cwd, project_name)
                            return

            # Fallback name
            create_mock_rock_file(self.cwd, "test-rock")

        elif "charmcraft" in command and "init" in command:
            # Create a basic charmcraft.yaml file
            yaml_path = Path(self.cwd) / "charmcraft.yaml"
            yaml_content = """name: test-charm
version: 1.0
summary: Test charm
description: A test charm for unit testing.
"""
            yaml_path.write_text(yaml_content)

        elif "charmcraft" in command and "pack" in command:
            # Extract project name from charmcraft.yaml if it exists
            yaml_path = Path(self.cwd) / "charmcraft.yaml"
            if yaml_path.exists():
                with open(yaml_path, "r") as f:
                    content = f.read()
                    # Simple parsing to get name (assumes format: name: <name>)
                    for line in content.split("\n"):
                        if line.startswith("name:"):
                            project_name = line.split(":", 1)[1].strip()
                            create_mock_charm_file(self.cwd, project_name)
                            return

            # Fallback name
            create_mock_charm_file(self.cwd, "test-charm")


def create_mock_popen_factory(should_fail=False, fail_returncode=1):
    """
    Create a factory function for mocking subprocess.Popen.

    Args:
        should_fail: Whether the mock command should fail
        fail_returncode: Return code to use when failing

    Returns:
        A factory function that creates MockSubprocessPopen instances
    """

    def mock_popen_factory(*args, **kwargs):
        mock_popen = MockSubprocessPopen(*args, **kwargs)
        if should_fail:
            mock_popen.returncode = fail_returncode
        return mock_popen

    return mock_popen_factory


def create_status_callback_mock():
    """
    Create a mock status callback that records all calls.

    Returns:
        A tuple of (mock_callback, call_list)
    """
    call_list = []

    def mock_callback(message, is_log=False):
        call_list.append({"message": message, "is_log": is_log})

    return mock_callback, call_list
