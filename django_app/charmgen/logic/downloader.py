import subprocess
import os
import shutil
from urllib.parse import urlparse

class GithubDownloader:
    def __init__(self, repo_url):
        self.repo_url = repo_url

    def download(self, target_dir):
        """Clones a repo into the target directory."""
        subprocess.run(
            ['git', 'clone', '--depth', '1', self.repo_url, target_dir],
            check=True,
            capture_output=True
        )
        project_name = os.path.splitext(os.path.basename(urlparse(self.repo_url).path))[0]
        return {'path': target_dir, 'project_name': project_name}
