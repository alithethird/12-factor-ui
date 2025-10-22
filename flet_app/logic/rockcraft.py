import glob
import os
import shutil
import subprocess


class RockcraftGenerator:
    def __init__(self, project_path, framework):
        self.project_path = project_path
        self.framework = framework

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

    def generate(self, status_callback=None):
        """Initializes and packs the Rock, with an optional callback for status updates."""
        if status_callback:
            status_callback("Initializing Rockcraft...")
        self._run_command(['rockcraft', 'init', f'--profile={self.framework}-framework'], status_callback)
        
        if status_callback:
            status_callback("Rockcraft initialized. Packing Rock...")
        self._run_command(['rockcraft', 'pack'], status_callback)
        
        if status_callback:
            status_callback("Rock packing complete.")

        rock_files = glob.glob(os.path.join(self.project_path, '*.rock'))
        if not rock_files:
            raise FileNotFoundError("Could not find generated .rock file")
        
        return rock_files[0]
