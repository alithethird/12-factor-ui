import os
import shutil
import tarfile
import zipfile
import tempfile

class ArchiveExtractor:
    def __init__(self, uploaded_file):
        self.uploaded_file = uploaded_file

    def extract(self, target_dir):
        """Extracts an uploaded archive to a target directory."""
        filename = self.uploaded_file.name
        
        # Write the uploaded file to a temporary file on disk
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            for chunk in self.uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_path = tmp_file.name

        try:
            if filename.endswith('.zip'):
                with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
            elif filename.endswith('.tar.gz') or filename.endswith('.tar'):
                with tarfile.open(tmp_path) as tar_ref:
                    tar_ref.extractall(target_dir)
            else:
                raise ValueError("Unsupported archive format")
        finally:
            os.remove(tmp_path)

        return self._find_project_root(target_dir, filename)

    def _find_project_root(self, base_path, original_filename):
        """Finds a nested project root if one exists."""
        items = [name for name in os.listdir(base_path) if not name.startswith('.') and name != '__MACOSX']
        if len(items) == 1 and os.path.isdir(os.path.join(base_path, items[0])):
            return {
                'root_path': os.path.join(base_path, items[0]),
                'project_name': items[0]
            }
        
        project_name = original_filename.replace('.zip', '').replace('.tar.gz', '').replace('.tar', '')
        return {'root_path': base_path, 'project_name': project_name}
