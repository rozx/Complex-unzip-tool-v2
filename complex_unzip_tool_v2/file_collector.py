"""File collection utilities for the Complex Unzip Tool."""

from pathlib import Path
from typing import List


def collect_all_files(paths: List[Path], recursive: bool = False) -> List[Path]:
    """Collect all files from the given paths.
    
    Args:
        paths: List of file or directory paths
        recursive: Whether to recursively search directories
        
    Returns:
        List of all file paths found
    """
    all_files = []
    
    for path in paths:
        if path.is_file():
            all_files.append(path)
        elif path.is_dir():
            if recursive:
                # Recursive: get all files in directory and subdirectories
                all_files.extend(path.rglob("*"))
                # Also include files directly in the root path
                all_files.extend([f for f in path.iterdir() if f.is_file()])
            else:
                # Non-recursive: only files directly in the directory
                all_files.extend([f for f in path.iterdir() if f.is_file()])
    
    # Filter to only include files (not directories) and remove duplicates
    files_only = [f for f in all_files if f.is_file()]
    return list(set(files_only))  # Remove duplicates
