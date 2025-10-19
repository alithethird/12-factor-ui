import subprocess
import os
import glob
import shutil

class RockcraftGenerator:
    def __init__(self, project_path):
        self.project_path = project_path

    def _run_command(self, command):
        # Using full path to avoid PATH issues
        cmd_path = shutil.which(command[0])
        if not cmd_path:
            raise FileNotFoundError(f"Command not found: {command[0]}")
        
        print(f"{self.project_path=}")
        try:
            result = subprocess.run(
                [cmd_path] + command[1:],
                cwd=self.project_path,
                check=True,
                capture_output=True,
                text=True
            )
        except Exception:
            print(f"{result=}")
        return result

    def generate(self):
        """Initializes and packs the Rock."""
        self._run_command(['rockcraft', 'init', '--profile=flask-framework'])
        self._run_command(['rockcraft', 'pack'])
        
        rock_files = glob.glob(os.path.join(self.project_path, '*.rock'))
        if not rock_files:
            raise FileNotFoundError("Could not find generated .rock file")
        
        return rock_files[0]
