import zipfile
import os
import tempfile

def BundleArtifacts(rock_file, charm_file):
    """Creates a zip file containing the rock and charm."""
    # Create the temp file in the system's temp directory
    tmp_zip_file, tmp_zip_path = tempfile.mkstemp(suffix=".zip")
    os.close(tmp_zip_file) # Close the file handle

    with zipfile.ZipFile(tmp_zip_path, 'w') as zf:
        zf.write(rock_file, os.path.basename(rock_file))
        zf.write(charm_file, os.path.basename(charm_file))


    return tmp_zip_path
