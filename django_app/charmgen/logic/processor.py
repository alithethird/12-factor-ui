import os
import json

class ApplicationProcessor:
    def __init__(self, project_path, framework):
        self.project_path = project_path
        self.framework = framework

    def check_project(self):
        """Runs validation checks based on the framework."""
        if self.framework in ['flask', 'django', 'fastapi']:
            self._check_python()
        elif self.framework == 'expressjs':
            self._check_node()
        else:
            raise ValueError(f"Unsupported framework for validation: {self.framework}")
        return True

    def _check_python(self):
        if not os.path.exists(os.path.join(self.project_path, 'requirements.txt')):
            raise ValueError("Project is missing requirements.txt")

    def _check_node(self):
        package_json_path = os.path.join(self.project_path, 'package.json')
        if not os.path.exists(package_json_path):
            raise ValueError("Project is missing package.json")
        with open(package_json_path, 'r') as f:
            data = json.load(f)
            if 'start' not in data.get('scripts', {}):
                raise ValueError("package.json is missing a 'start' script")
