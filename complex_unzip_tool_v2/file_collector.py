"""File collection utilities for the Complex Unzip Tool."""

from pathlib import Path
from typing import List


def is_system_file(file_path: Path) -> bool:
    """Check if a file is a system file that should be ignored.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is a system file, False otherwise
    """
    filename = file_path.name.lower()
    
    # Windows system files
    windows_system_files = {
        'thumbs.db', 'desktop.ini', 'folder.jpg', 'folder.gif', 'albumart.jpg',
        'albumartsmall.jpg', 'ntuser.dat', 'ntuser.ini', 'autorun.inf',
        'system volume information', 'recycler', '$recycle.bin', 'pagefile.sys',
        'hiberfil.sys', 'swapfile.sys', 'bootmgr', 'bootmgfw.efi'
    }
    
    # macOS system files
    macos_system_files = {
        '.ds_store', '.appledb', '.applede', '.appledialog', '.spotlight-v100',
        '.trash', '.trashes', '.volumeicon.icns', '.com.apple.timemachine.donotpresent',
        '.documentrevisions-v100', '.pkginfo', '.localized', '.metadata_never_index'
    }
    
    # Linux/Unix system files
    linux_system_files = {
        '.directory', '.trash-1000', '.trash-0', '.gvfs', '.recently-used.xbel',
        '.dmrc', '.face', '.icons', '.themes', '.fonts', 'lost+found'
    }
    
    # General hidden files patterns (start with .)
    if filename.startswith('.'):
        # Allow some common non-system hidden files that might be archives
        allowed_hidden = {'.7z', '.rar', '.zip', '.tar', '.gz', '.bz2', '.xz'}
        if not any(filename.endswith(ext) for ext in allowed_hidden):
            return True
    
    # Check against system file lists
    if filename in windows_system_files or filename in macos_system_files or filename in linux_system_files:
        return True
    
    # Windows file extensions to ignore
    windows_system_extensions = {'.sys', '.ini', '.inf', '.bat', '.cmd', '.scr', '.lnk', '.url'}
    if file_path.suffix.lower() in windows_system_extensions:
        return True
    
    return False


def collect_all_files(paths: List[Path], recursive: bool = False) -> List[Path]:
    """Collect all files from the given paths.
    
    Args:
        paths: List of file or directory paths
        recursive: Whether to recursively search directories
        
    Returns:
        List of all file paths found (excluding passwords.txt and system files)
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
    unique_files = list(set(files_only))  # Remove duplicates
    
    # Filter out passwords.txt and system files
    filtered_files = []
    for f in unique_files:
        # Skip passwords.txt files (used for password management)
        if f.name.lower() == 'passwords.txt':
            continue
        # Skip system files
        if is_system_file(f):
            continue
        filtered_files.append(f)
    
    return filtered_files
