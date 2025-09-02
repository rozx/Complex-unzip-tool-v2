import subprocess
import json
import os
from typing import List, Dict, Optional, Union

# Custom exception classes
class ArchiveError(Exception):
    """Base exception for archive-related errors."""
    pass

class ArchiveNotFoundError(ArchiveError):
    """Raised when the archive file is not found."""
    pass

class SevenZipNotFoundError(ArchiveError):
    """Raised when 7z executable is not found."""
    pass

class ArchivePasswordError(ArchiveError):
    """Raised when password is incorrect or required."""
    pass

class ArchiveCorruptedError(ArchiveError):
    """Raised when archive is corrupted or unreadable."""
    pass

class ArchiveUnsupportedError(ArchiveError):
    """Raised when archive format is not supported."""
    pass

class ArchiveParsingError(ArchiveError):
    """Raised when unable to parse 7z output."""
    pass

def read_archive_content_with_7z(
    archive_path: str, 
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None
) -> List[Dict[str, Union[str, int]]]:
    """
    Read archive content using 7z.exe with optional password support.
    
    Args:
        archive_path (str): Path to the archive file
        password (str, optional): Password for encrypted archives
        seven_zip_path (str): Path to 7z.exe executable (default: auto-detect from program path)
    
    Returns:
        List[Dict]: List of file information dictionaries containing:
            - name: file/folder name
            - size: uncompressed size in bytes
            - packed_size: compressed size in bytes
            - type: file type (File/Folder)
            - modified: modification date
    
    Raises:
        ArchiveNotFoundError: If archive file not found
        SevenZipNotFoundError: If 7z executable not found
        ArchivePasswordError: If password is incorrect or required
        ArchiveCorruptedError: If archive is corrupted
        ArchiveUnsupportedError: If archive format is not supported
        ArchiveParsingError: If unable to parse 7z output
    """
    
    # Set default 7z path if not provided
    if seven_zip_path is None:
        # Get the project root directory (go up one level from complex_unzip_tool_v2)
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(current_dir)
        seven_zip_path = os.path.join(project_root, "7z", "7z.exe")
    
    # Check if archive exists
    if not os.path.exists(archive_path):
        raise ArchiveNotFoundError(f"Archive not found: {archive_path}")
    
    # Check if 7z executable exists
    if not os.path.exists(seven_zip_path):
        raise SevenZipNotFoundError(f"7z executable not found at: {seven_zip_path}")
    
    # Build command
    cmd = [seven_zip_path, "l", "-slt", archive_path]

    cmd.extend([f"-p{password}"])
    
    try:
        # Execute 7z command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        if result.returncode != 0:
            raise ArchiveError(f"7z command failed ({result.returncode}): {result.stderr.strip()}")

        # Parse output
        try:
            files_info = _parse_7z_list_output(result.stdout)
            return files_info
        except Exception as e:
            raise ArchiveParsingError(f"Failed to parse 7z output: {str(e)}")
        
    except subprocess.CalledProcessError as e:
        stderr_lower = e.stderr.lower()

        if "wrong password" in stderr_lower or "cannot open encrypted archive" in stderr_lower:
            raise ArchivePasswordError(f"Incorrect password or password required for: {archive_path}")
        elif "data error" in stderr_lower or "crc failed" in stderr_lower:
            raise ArchiveCorruptedError(f"Archive appears to be corrupted: {archive_path}")
        elif "unsupported method" in stderr_lower or "unknown method" in stderr_lower:
            raise ArchiveUnsupportedError(f"Archive format not supported: {archive_path}")
        elif "cannot open file" in stderr_lower:
            raise ArchiveNotFoundError(f"Cannot open archive file: {archive_path}")
        else:
            # Generic archive error for other cases
            raise ArchiveError(f"7z error ({e.returncode}): {e.stderr.strip()}")
    
    except FileNotFoundError:
        raise SevenZipNotFoundError(f"7z executable not found at: {seven_zip_path}")


def _parse_7z_list_output(output: str) -> List[Dict[str, Union[str, int]]]:
    """
    Parse 7z list command output into structured data.
    
    Args:
        output (str): Raw output from 7z list command
        
    Returns:
        List[Dict]: Parsed file information
    """
    files = []
    current_file = {}
    
    lines = output.split('\n')
    in_file_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Look for the start of file listing section (second ----------)
        if line.startswith('----------'):
            in_file_section = True
            continue
        
        # Skip lines before file section
        if not in_file_section:
            continue
            
        # Skip empty lines
        if not line:
            continue
            
        # Check if this line starts a new file entry (starts with "Path = ")
        if line.startswith('Path = '):
            # Save previous file if it exists
            if current_file and current_file.get('Path'):
                files.append(_format_file_info(current_file))
            
            # Start new file entry
            current_file = {}
            parts = line.split(' = ', 1)
            if len(parts) == 2:
                current_file['Path'] = parts[1]
        
        # Parse other key-value pairs
        elif ' = ' in line and current_file:
            parts = line.split(' = ', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                current_file[key] = value
    
    # Add final file if exists
    if current_file and current_file.get('Path'):
        files.append(_format_file_info(current_file))
    
    return files


def _format_file_info(file_data: Dict[str, str]) -> Dict[str, Union[str, int]]:
    """
    Format raw file data into standardized structure.
    
    Args:
        file_data (Dict): Raw file data from 7z output
        
    Returns:
        Dict: Formatted file information
    """
    try:
        size = int(file_data.get('Size', '0'))
    except (ValueError, TypeError):
        size = 0
        
    try:
        packed_size = int(file_data.get('Packed Size', '0'))
    except (ValueError, TypeError):
        packed_size = 0
    
    return {
        'name': file_data.get('Path', ''),
        'size': size,
        'packed_size': packed_size,
        'type': file_data.get('Folder', 'File').replace('-', 'File').replace('+', 'Folder'),
        'modified': file_data.get('Modified', ''),
        'attributes': file_data.get('Attributes', ''),
        'crc': file_data.get('CRC', ''),
        'method': file_data.get('Method', '')
    }


def test_archive_reading():
    """
    Test function for archive reading functionality.
    """
    try:
        # Example usage
        archive_path = "test_archive.7z"
        password = "mypassword"  # None if no password
        
        files = read_archive_content_with_7z(archive_path, password)
        
        print(f"Archive contains {len(files)} items:")
        for file_info in files:
            print(f"  {file_info['name']} ({file_info['size']} bytes)")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_archive_reading()