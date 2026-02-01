import os
from ..config import settings

def should_review_file(file_path: str) -> bool:
    """
    Determines if a file should be reviewed by the LLM based on semantic filtering rules.
    """
    # 1. Check for ignored extensions
    _, ext = os.path.splitext(file_path)
    ignored_extensions = [e.strip().lower() for e in settings.ignored_extensions.split(",")]
    if ext.lower() in ignored_extensions:
        return False

    # 2. Check for ignored filenames
    filename = os.path.basename(file_path)
    ignored_files = [f.strip().lower() for f in settings.ignored_files.split(",")]
    if filename.lower() in ignored_files:
        return False

    # 3. Check for ignored directories
    path_parts = file_path.split(os.sep)
    # Also handle forward slash for git paths
    if '/' in file_path:
        path_parts = file_path.split('/')
        
    ignored_directories = [d.strip().lower() for d in settings.ignored_directories.split(",")]
    for part in path_parts:
        if part.lower() in ignored_directories:
            return False

    # 4. Filter out binary files (basic check)
    # (Optional: specialized checks can be added here)

    return True
