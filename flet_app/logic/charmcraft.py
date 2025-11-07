import glob
import os
import shutil
import subprocess
from pathlib import Path

import yaml

INTEGRATION_MAP = {
    "prometheus": {"type": "provide", "integration":{"metrics-endpoint": {"interface": "prometheus_scrape"}}},
    "grafana": {"type": "provide", "integration":{"grafana-dashboard": {"interface": "grafana_dashboard"}}},
    "ingress": {"type": "require", "integration":{"ingress": {"interface": "ingress", "limit": 1}}},
    "loki": {
        "type": "require", "integration":{"logging": {"interface": "loki_push_api"}}},
    "postgresql": {"type": "require", "integration":{"postgresql": {"interface": "postgresql_client", "limit": 1}}},
    "tracing": {"type": "require", "integration":{"tracing": {"interface": "tracing", "optional": True, "limit": 1}}},
    "smtp": {
        "type": "require", "integration":{"smtp": {"interface": "smtp", "optional": True, "limit": 1}}},
    "openfga": {
        "type": "require", "integration":{"openfga": {"interface": "openfga", "optional": True, "limit": 1}}},
    "oidc": {
        "type": "require", "integration":{"oidc": {"interface": "oauth", "optional": True, "limit": 1}}},
    "http-proxy": {
        "type": "require", "integration":{"http-proxy": {"interface": "http_proxy", "optional": True, "limit": 1}}},
    # Add other integrations here
}


class CharmcraftGenerator:
    def __init__(self, integrations, config_options, project_path, project_name):
        self.integrations = integrations  # Store as IDs
        self.config_options = config_options  # Store as dicts
        self.project_name = project_name
        self.temp_dir = project_path  # tempfile.mkdtemp(prefix="charm-")
        print(f"{project_path=}")
        self.charm_project_path = Path(self.temp_dir) / "charm"
        print(f"{self.charm_project_path=}")
        if not self.charm_project_path.exists():
            self.charm_project_path.mkdir()

    def _run_command(self, command, cwd, status_callback=None):
        """Runs a command and streams its output."""
        cmd_path = shutil.which(command[0])
        if not cmd_path:
            cmd_path_snap = f"/snap/bin/{command[0]}"
            if Path(cmd_path_snap).exists():
                cmd_path = cmd_path_snap
            else:
                raise FileNotFoundError(f"Command not found: {command[0]}")

        process = subprocess.Popen(
            [cmd_path] + command[1:],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in iter(process.stdout.readline, ""):
            if status_callback:
                if "init" in command:
                    status_callback(f"charm-init: {line.strip()}")
                else:
                    status_callback(f"charm-pack: {line.strip()}")

        process.stdout.close()
        return_code = process.wait()
        if return_code != 0:
            raise subprocess.CalledProcessError(
                return_code, command, "Command failed. See logs."
            )

    def _get_typed_value(self, value, value_type):
        if value_type == "int":
            return int(value) if value else 0
        if value_type == "bool":
            return value.lower() in ["true", "1", "yes"]
        if value_type == "float":
            return float(value) if value else 0.0
        return value

    def init_charmcraft(self, status_callback=None) -> str:
        """Initializes the charm project and returns path to charmcraft.yaml."""
        if status_callback:
            status_callback("Initializing Charmcraft...")
        # Init runs in the parent temp dir, creating the project subdir
        self._run_command(
            ["charmcraft", "init", "--name", self.project_name],
            cwd=self.charm_project_path,
            status_callback=print,
        )

        yaml_path = os.path.join(self.charm_project_path, "charmcraft.yaml")
        if not os.path.exists(yaml_path):
            raise FileNotFoundError("charmcraft.yaml not found after init.")

        if status_callback:
            status_callback("Charmcraft initialized.")
        return yaml_path, self.temp_dir

    def update_charmcraft_yaml(self, yaml_path: str, status_callback=None):
        """Reads, modifies, and writes charmcraft.yaml."""
        if status_callback:
            status_callback("Updating charmcraft.yaml...")
        try:
            with open(yaml_path, "r") as f:
                charm_data = yaml.safe_load(f)

            # Add relations
            requirer_relations = {}
            provider_relations = {}
            for i_id in self.integrations:
                if i_id in INTEGRATION_MAP:
                    if INTEGRATION_MAP[i_id]["type"] == "require":
                        requirer_relations.update(INTEGRATION_MAP[i_id]["integration"])
                    elif INTEGRATION_MAP[i_id]["type"] == "provide":
                        provider_relations.update(INTEGRATION_MAP[i_id]["integration"])
            if provider_relations:
                charm_data["provides"] = provider_relations
            if requirer_relations:
                charm_data["requires"] = requirer_relations

            # Add config options
            options = {}
            for opt in self.config_options:
                config = {"type": opt["type"], "description": "A custom config."}
                if opt.get("isOptional"):  # Check key directly from dict
                    config["default"] = self._get_typed_value(opt["value"], opt["type"])
                options[opt["key"]] = config
            if options:
                charm_data["options"] = options

            with open(yaml_path, "w") as f:
                yaml.dump(charm_data, f, sort_keys=False)  # Keep order

            if status_callback:
                status_callback("charmcraft.yaml updated.")
        except Exception as e:
            raise RuntimeError(f"Failed to update charmcraft.yaml: {e}")

    def pack_charmcraft(self, status_callback=None) -> str:
        """Packs the charm and returns the path to the .charm file."""
        if status_callback:
            status_callback("Packing Charm...")
        # Pack runs inside the actual charm project directory
        self._run_command(
            ["charmcraft", "pack"],
            cwd=self.charm_project_path,
            status_callback=print,
        )

        charm_files = glob.glob(os.path.join(self.charm_project_path, "*.charm"))
        if not charm_files:
            raise FileNotFoundError("Could not find generated .charm file")

        if status_callback:
            status_callback("Charm packing complete: " + charm_files[0])
        return charm_files[0]

    def cleanup(self):
        """Cleans up the temporary directory."""
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
            self.temp_dir = None
