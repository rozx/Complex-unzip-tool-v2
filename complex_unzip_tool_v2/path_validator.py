"""Path validation utilities for the Complex Unzip Tool."""

from pathlib import Path
from typing import List


def validate_paths(path_strings: List[str]) -> List[Path]:
    """Validate and convert string paths to Path objects.
    
    Args:
        path_strings: List of path strings from command line arguments
        
    Returns:
        List of validated Path objects
        
    Raises:
        FileNotFoundError: If any path doesn't exist
    """
    valid_paths = []
    
    for path_str in path_strings:
        path = Path(path_str)
        
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist | 路径不存在: {path}")
        
        valid_paths.append(path)
    
    return valid_paths
