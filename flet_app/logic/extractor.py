import os
import tarfile
import zipfile


class ArchiveExtractor:
    def __init__(self, archive_path, original_filename):
        self.archive_path = archive_path
        self.original_filename = original_filename

    def extract(self, target_dir):
        """Extracts an archive to a target directory."""
        if self.original_filename.endswith(".zip"):
            with zipfile.ZipFile(self.archive_path, "r") as zip_ref:
                zip_ref.extractall(target_dir)
        elif self.original_filename.endswith((".tar.gz", ".tar")):
            with tarfile.open(self.archive_path) as tar_ref:
                tar_ref.extractall(target_dir)
        else:
            raise ValueError("Unsupported archive format")

        return self._find_project_root(target_dir)

    def _find_project_root(self, base_path):
        """Finds a nested project root if one exists."""
        items = [
            name
            for name in os.listdir(base_path)
            if not name.startswith(".") and name != "__MACOSX"
        ]
        if len(items) == 1 and os.path.isdir(os.path.join(base_path, items[0])):
            return {
                "root_path": os.path.join(base_path, items[0]),
                "project_name": items[0],
            }

        project_name = (
            self.original_filename.replace(".zip", "")
            .replace(".tar.gz", "")
            .replace(".tar", "")
            .replace("_", "-")
            .lower()
            .replace(" ", "-")
        )
        return {"root_path": base_path, "project_name": project_name}
