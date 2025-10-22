import tempfile
from pathlib import Path

# --- App State Management ---
# Moving these shared variables to their own file breaks the circular import.
JOB_STORE = {}

# Use the system's temporary directory and create a specific folder for our app
TEMP_STORAGE_PATH = Path(tempfile.gettempdir()) / "rock_charm_generator"


