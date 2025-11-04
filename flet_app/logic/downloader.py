import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

# TODO:
# - When it can not find the subfolder in git it doesn't error out here
# it errors in processor and thinks requirements.txt is not there


class GithubDownloader:
    def __init__(self, repo_url: str, branch: str, subfolder: str | None):
        # if not repo_url:
        #     raise ValueError("Repository URL cannot be empty.")
        self.repo_url = repo_url if repo_url else "https://github.com/canonical/paas-charm"
        self.branch = branch
        self.subfolder = subfolder if repo_url else "examples/flask-minimal/flask_minimal_app"

    def download(self, target_dir):
        """
        Clones the entire repo or just a specific directory using sparse checkout.

        Args:
            target_dir (str): The directory where the content will be placed.
            self.subfolder (str, optional): The path within the repo to download.
                                         If None, clones the entire repo.
        """
        # Ensure the target directory exists and is empty
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir)

        if self.subfolder:
            # --- Sparse Checkout ---
            print(f"Performing sparse checkout for directory: {self.subfolder}")

            # 1. Init empty repo
            subprocess.run(
                ["git", "init"], cwd=target_dir, check=True, capture_output=True
            )

            # 2. Add remote
            subprocess.run(
                ["git", "remote", "add", "origin", self.repo_url],
                cwd=target_dir,
                check=True,
                capture_output=True,
            )

            # 3. Enable sparse checkout
            subprocess.run(
                ["git", "config", "core.sparseCheckout", "true"],
                cwd=target_dir,
                check=True,
                capture_output=True,
            )

            # 4. Define the directory to checkout
            sparse_checkout_file = (
                Path(target_dir) / ".git" / "info" / "sparse-checkout"
            )
            # Include both the directory and all its contents recursively
            dir_pattern = self.subfolder.strip("/")
            # Create parent directories if they don't exist
            sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
            with open(sparse_checkout_file, "w") as f:
                # Write the directory pattern and its contents pattern
                f.write(f"{dir_pattern}\n")
                f.write(f"{dir_pattern}/**\n")
            print(f"Wrote patterns to {sparse_checkout_file}")

            # 5. Pull only the specified directory (shallowly)
            # Replace 'main' with the desired branch if needed
            try:
                print("Pulling sparse checkout...")
                subprocess.run(
                    [
                        "git",
                        "pull",
                        "--depth=1",
                        "origin",
                        self.branch,
                    ],
                    cwd=target_dir,
                    check=True,
                    capture_output=True,
                    text=True,  # Capture output as text
                )
            except subprocess.CalledProcessError as e:
                # It's common for the first sparse pull to report an error even if it works
                # Check stderr for common "ignorable" messages
                if (
                    "error: Not possible to fast-forward, aborting." in e.stderr
                    or "fatal: refusing to merge unrelated histories" in e.stderr
                ):
                    print(
                        "Sparse checkout completed with expected non-fatal Git messages."
                    )
                else:
                    # If it's a different error, re-raise it
                    print(
                        f"Sparse checkout failed: STDOUT={e.stdout}, STDERR={e.stderr}"
                    )
                    raise e

            # The files will be inside target_dir/path/to/your/directory
            # We might want to adjust the returned path to point directly to the content
            project_path = os.path.join(target_dir, self.subfolder.strip("/"))

        else:
            # --- Full Clone (Original Behavior) ---
            print("Performing full clone...")
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--branch",
                    self.branch,
                    "--depth",
                    "1",
                    self.repo_url,
                    target_dir,
                ],
                check=True,
                capture_output=True,
            )
            project_path = target_dir  # For full clone, the target is the project path

        project_name = os.path.splitext(os.path.basename(urlparse(self.repo_url).path))[
            0
        ]
        # Adjust project name if only a subdir was downloaded
        if self.subfolder:
            project_name = (
                os.path.basename(self.subfolder.strip("/"))
                .replace("_", "-")
                .lower()
                .replace(" ", "-")
            )

        return {"path": project_path, "project_name": project_name}
