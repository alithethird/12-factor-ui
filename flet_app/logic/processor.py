import os
import json
import re


class ApplicationProcessor:
    def __init__(self, project_path, framework):
        self.project_path = project_path
        self.framework = framework

    def check_project(self):
        """Runs validation checks based on the framework."""
        print(
            f"Validating project at {self.project_path} for {self.framework} framework..."
        )

        match self.framework:
            case "flask":
                self._check_flask()
            case "django":
                self._check_django()
            case "fastapi":
                self._check_fastapi()
            case "expressjs":
                self._check_expressjs()
            case "go":
                self._check_go()
            case "springboot":
                self._check_springboot()
            case _:
                print(f"No specific validation for {self.framework}, assuming success.")

        print("Validation successful.")
        return True

    def _check_flask(self):
        return self._check_requirements("flask")

    def _check_django(self):
        return True
        return self._check_requirements("django")

    def _check_fastapi(self):
        return self._check_requirements("fastapi")

    def _check_requirements(self, package_name: str):
        requirements_path = os.path.join(self.project_path, "requirements.txt")
        if not os.path.exists(requirements_path):
            raise ValueError("Project is missing requirements.txt")
        # Regex to match common package name terminators
        # This will capture the name before '==', '>=', '<=', '>', '~=', '[', or '#'
        package_pattern = re.compile(r"^[a-zA-Z0-9\-_.]+")

        with open(requirements_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Skip empty lines and comments

                match = package_pattern.match(line)
                if match:
                    found_package = match.group(0)
                    if package_name.lower() == found_package.lower():
                        return True  # Found it!

        return False  # Scanned the whole file, not found

    def _check_expressjs(self):
        package_json_path = os.path.join(self.project_path, "package.json")
        if not os.path.exists(package_json_path):
            raise ValueError("Project is missing package.json")
        with open(package_json_path, "r") as f:
            data = json.load(f)
            if "start" not in data.get("scripts", {}):
                raise ValueError("package.json is missing a 'start' script")

    def _check_go(self):
        if not os.path.exists(os.path.join(self.project_path, "go.mod")):
            raise ValueError("Project is missing go.mod")

    def _check_springboot(self):
        if not os.path.exists(os.path.join(self.project_path, "pom.xml")):
            raise ValueError("Project is missing pom.xml")
