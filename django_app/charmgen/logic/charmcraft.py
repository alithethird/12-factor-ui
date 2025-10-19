import subprocess
import os
import glob
import tempfile
import yaml
import shutil

INTEGRATION_MAP = {
    "postgresql": {"db": {"interface": "postgresql_client"}},
    "prometheus": {"metrics-endpoint": {"interface": "prometheus_scrape"}},
    # Add other integrations here
}

class CharmcraftGenerator:
    def __init__(self, integrations, config_options, project_name):
        self.integrations = integrations
        self.config_options = config_options
        self.project_name = project_name
        self.temp_dir = tempfile.mkdtemp(prefix="charm-")

    def _run_command(self, command, cwd, status_callback=None):
        """Runs a command and streams its output."""
        cmd_path = shutil.which(command[0])
        if not cmd_path:
            raise FileNotFoundError(f"Command not found: {command[0]}")
        
        process = subprocess.Popen(
            [cmd_path] + command[1:],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in iter(process.stdout.readline, ''):
            if status_callback:
                status_callback(line.strip(), is_log=True)

        process.stdout.close()
        return_code = process.wait()

        if return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

    def _get_typed_value(self, value, value_type):
        if value_type == 'int': return int(value)
        if value_type == 'bool': return value.lower() in ['true', '1', 'yes']
        if value_type == 'float': return float(value)
        return value

    def generate(self, status_callback=None):
        """Initializes, updates, and packs the Charm."""
        if status_callback:
            status_callback("Initializing Charmcraft...")
        self._run_command(['mkdir', 'charm'], cwd=self.temp_dir, status_callback=status_callback)
        self._run_command(['charmcraft', 'init', '--name', self.project_name], cwd=f"{self.temp_dir}/charm", status_callback=status_callback)
        charm_project_path = os.path.join(self.temp_dir, "charm")

        # Update charmcraft.yaml (no changes here)
        yaml_path = os.path.join(charm_project_path, 'charmcraft.yaml')
        with open(yaml_path, 'r') as f:
            charm_data = yaml.safe_load(f)
        # ... (logic for relations and options is the same)
        relations = {}
        for i_id in self.integrations:
            if i_id in INTEGRATION_MAP:
                relations.update(INTEGRATION_MAP[i_id])
        charm_data['requires'] = relations
        options = {}
        for opt in self.config_options:
            config = {'type': opt['type'], 'description': 'A custom config.'}
            if opt.get('isOptional'):
                config['default'] = self._get_typed_value(opt['value'], opt['type'])
            options[opt['key']] = config
        # TODO: put the config options in here
        # charm_data["config"]['options'] = options
        with open(yaml_path, 'w') as f:
            yaml.dump(charm_data, f)
        
        if status_callback:
            status_callback("Packing Charm...")
        self._run_command(['ls'], cwd=charm_project_path, status_callback=status_callback)
        self._run_command(['charmcraft', 'pack'], cwd=charm_project_path, status_callback=status_callback)
        
        charm_files = glob.glob(os.path.join(charm_project_path, '*.charm'))
        if not charm_files:
            raise FileNotFoundError("Could not find generated .charm file")
            
        return charm_files[0], self.cleanup

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
