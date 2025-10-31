import glob
import os
import shutil
import subprocess
from pathlib import Path  # Import Path


class RockcraftGenerator:
    def __init__(self, project_path, project_name, framework=""):
        self.project_path = project_path
        self.framework = framework
        self.project_name = project_name.replace("_", "-").lower().replace(" ", "-")

    def _run_command(self, command, status_callback=None):
        """Runs a command and streams its output to the status_callback."""
        cmd_path = shutil.which(command[0])
        if not cmd_path:
            # Try finding in snap path if not in standard PATH
            cmd_path_snap = f"/snap/bin/{command[0]}"
            if Path(cmd_path_snap).exists():
                cmd_path = cmd_path_snap
            else:
                raise FileNotFoundError(f"Command not found: {command[0]}")

        process = subprocess.Popen(
            [cmd_path] + command[1:],
            cwd=self.project_path,
            env={"ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS": "true"},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stdout and stderr
            text=True,
            bufsize=1,  # Line-buffered
        )

        for line in iter(process.stdout.readline, ""):
            if status_callback:
                if "init" in command:
                    status_callback(f"rock-init: {line.strip()}", is_log=True)
                else:
                    status_callback(f'rock-pack: {line.strip()}', is_log=True)

        process.stdout.close()
        return_code = process.wait()

        if return_code != 0:
            raise subprocess.CalledProcessError(
                return_code, command, "Command failed. See logs for details."
            )

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
        self._run_command(init_command, status_callback)

        yaml_path = os.path.join(self.project_path, "rockcraft.yaml")
        if not os.path.exists(yaml_path):
            raise FileNotFoundError("rockcraft.yaml not found after init.")

        if status_callback:
            status_callback("Rockcraft initialized.")
        return yaml_path

    def pack_rockcraft(self, status_callback=None) -> str:
        """Packs the Rock and returns the path to the .rock file."""
        if status_callback:
            status_callback("Packing Rock...")
        self._run_command(["rockcraft", "pack"], status_callback)

        if status_callback:
            status_callback("Rock packing complete.")

        rock_files = glob.glob(os.path.join(self.project_path, "*.rock"))
        if not rock_files:
            raise FileNotFoundError("Could not find generated .rock file")

        return rock_files[0]
