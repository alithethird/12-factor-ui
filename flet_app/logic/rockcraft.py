import glob
import os
import shutil
import subprocess
import time
from pathlib import Path


class RockcraftGenerator:
    def __init__(self, project_path, project_name, framework=""):
        self.project_path = project_path
        self.framework = framework
        self.project_name = project_name.replace("_", "-").lower().replace(" ", "-")

    def _run_command(self, command, status_callback=None, timeout=3600):
        """
        Runs a command and streams its output to the status_callback.

        Args:
            command: List of command arguments
            status_callback: Optional callback function for status updates
            timeout: Maximum time in seconds to allow the process to run (default: 3600s = 1 hour)

        Raises:
            subprocess.TimeoutExpired: If the process exceeds the timeout
            subprocess.CalledProcessError: If the command returns non-zero exit code
            FileNotFoundError: If the command is not found
        """
        cmd_path = shutil.which(command[0])
        if not cmd_path:
            # Try finding in snap path if not in standard PATH
            cmd_path_snap = f"/snap/bin/{command[0]}"
            if Path(cmd_path_snap).exists():
                cmd_path = cmd_path_snap
            else:
                raise FileNotFoundError(f"Command not found: {command[0]}")

        process = None
        start_time = time.time()
        last_output_time = time.time()
        max_silence_time = 300  # 5 minutes of no output = likely hung/crashed

        try:
            process = subprocess.Popen(
                [cmd_path] + command[1:],
                cwd=self.project_path,
                env={"ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS": "true"},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stdout and stderr
                text=True,
                bufsize=1,  # Line-buffered
            )

            try:
                for line in iter(process.stdout.readline, ""):
                    if status_callback:
                        if "init" in command:
                            status_callback(f"rock-init:  {line.strip()}")
                        else:
                            status_callback(f"rock-pack:  {line.strip()}")

                    last_output_time = time.time()

                    # Check if we've exceeded timeout
                    elapsed = time.time() - start_time
                    if elapsed > timeout:
                        raise subprocess.TimeoutExpired(
                            cmd_path,
                            timeout,
                            f"Command exceeded {timeout} seconds timeout.",
                        )

                process.stdout.close()
                return_code = process.wait(
                    timeout=10
                )  # Short timeout to wait for process to finish

                if return_code != 0:
                    raise subprocess.CalledProcessError(
                        return_code, command, "Command failed. See logs for details."
                    )

            except subprocess.TimeoutExpired as e:
                if process and process.poll() is None:
                    process.kill()
                    process.wait()
                raise

        except Exception as e:
            # If process is still running, kill it
            if process and process.poll() is None:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except:
                    pass

            if status_callback:
                status_callback(f"Process error: {str(e)}")
            raise

    def init_rockcraft(self, status_callback=None) -> str:
        """Initializes Rockcraft and returns the path to rockcraft.yaml."""
        if status_callback:
            status_callback("Initializing Rockcraft...")
        if Path(self.project_path + "/rockcraft.yaml").exists():
            os.remove(self.project_path + "/rockcraft.yaml")

        init_command = [
            "rockcraft",
            "init",
            f"--profile={self.framework}-framework",
            f"--name={self.project_name}",
        ]
        # Init typically completes within 5 minutes
        self._run_command(init_command, print, timeout=300)

        yaml_path = os.path.join(self.project_path, "rockcraft.yaml")
        if not os.path.exists(yaml_path):
            raise FileNotFoundError("rockcraft.yaml not found after init.")

        if status_callback:
            status_callback("Rockcraft initialized.")
        return yaml_path

    def pack_rockcraft(self, status_callback=None) -> str:
        """
        Packs the Rock and returns the path to the .rock file.

        WARNING: This operation can be resource-intensive and may take significant time.
        The timeout is set to 1 hour to allow for large projects.
        """
        if status_callback:
            status_callback("Packing Rock... this may take 5-30 minutes depending on project size...")
        # Pack can take a long time for large projects, allow up to 1 hour
        self._run_command(["rockcraft", "pack"], print, timeout=3600)

        rock_files = glob.glob(os.path.join(self.project_path, "*.rock"))
        if not rock_files:
            raise FileNotFoundError("Could not find generated .rock file")

        if status_callback:
            status_callback("Rock packing complete: " + rock_files[0])

        return rock_files[0]
