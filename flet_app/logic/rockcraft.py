import glob
import os
import shutil
import subprocess


class RockcraftGenerator:
    def __init__(self, project_path, framework, project_name):
        self.project_path = project_path
        self.framework = framework
        self.project_name = project_name

    def _run_command(self, command, status_callback=None):
        """Runs a command and streams its output to the status_callback."""
        cmd_path = shutil.which(command[0])
        if not cmd_path:
            raise FileNotFoundError(f"Command not found: {command[0]}")
        
        process = subprocess.Popen(
            [cmd_path] + command[1:],
            cwd=self.project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Combine stdout and stderr
            text=True,
            bufsize=1, # Line-buffered
            env={"ROCKCRAFT_ENABLE_EXPERIMENTAL_EXTENSIONS":"true"},
        )

        # Read output line by line in real-time
        for line in iter(process.stdout.readline, ''):
            if status_callback:
                # Send the raw log line, flagging it as a log
                status_callback(line.strip(), is_log=True)
        
        process.stdout.close()
        return_code = process.wait()

        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command, "Command failed. See logs for details.")

    def init_rock(self, status_callback=None) -> str:
        """Packs the Rock, with an optional callback for status updates."""
        if status_callback:
            status_callback("Initializing Rockcraft...")
        self._run_command(['rockcraft', 'init', f'--profile={self.framework}-framework', f'--name={self.project_name}'], status_callback)
        
        if status_callback:
            status_callback("Rockcraft Initialized.")
        
        rockcraft_files = glob.glob(os.path.join(self.project_path, 'rockcraft.yaml'))
        if not rockcraft_files:
            raise FileNotFoundError("Could not find generated rockcraft.yaml file")
        
        return rockcraft_files
        
    def pack_rock(self, status_callback=None) -> str:
        """Initializes the Rock, with an optional callback for status updates."""
        if status_callback:
            status_callback("Packing Rock...")
        self._run_command(['rockcraft', 'pack'], status_callback)
        
        if status_callback:
            status_callback("Rock packing complete.\n")

        rock_files = glob.glob(os.path.join(self.project_path, '*.rock'))
        if not rock_files:
            raise FileNotFoundError("Could not find generated .rock file")
        
        return rock_files[0]
