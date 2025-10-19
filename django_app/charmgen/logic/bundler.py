import zipfile
import os
import tempfile

def BundleArtifacts(rock_file, charm_file):
    """Creates a zip file containing the rock and charm."""
    tmp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    
    with zipfile.ZipFile(tmp_zip.name, 'w') as zf:
        zf.write(rock_file, os.path.basename(rock_file))
        zf.write(charm_file, os.path.basename(charm_file))

    cleanup = lambda: os.remove(tmp_zip.name)
    return tmp_zip.name, cleanup
