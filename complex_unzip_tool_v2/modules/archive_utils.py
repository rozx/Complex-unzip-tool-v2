import re
import subprocess
import json
import os
import sys
import shutil
import tempfile
import typer
from typing import List, Dict, Optional, Union
from .rich_utils import (
    print_nested_extraction_header, print_extraction_process_header,
    print_extracting_archive, print_password_attempt, print_password_failed,
    print_password_success, print_extraction_summary, print_warning, print_error,
    print_error_summary, print_general, print_empty_line, print_info, 
    print_success
)
from .rich_utils import console
from .file_utils import safe_remove
from .utils import sanitize_path, sanitize_filename

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

def _get_default_7z_path() -> str:
    """
    Get the default path to 7z.exe executable.
    Works for both development and PyInstaller standalone builds.
    """
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        bundle_dir = sys._MEIPASS
        seven_zip_path = os.path.join(bundle_dir, "7z", "7z.exe")
    else:
        # Running in development mode
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(current_dir)
        seven_zip_path = os.path.join(project_root, "7z", "7z.exe")
    
    return seven_zip_path

def readArchiveContentWith7z(
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
        seven_zip_path = _get_default_7z_path()
    
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
        # Execute 7z command with proper encoding handling
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,  # Use bytes to avoid encoding issues
            check=False,  # Don't raise exception on non-zero return code
        )

        # Decode output safely
        try:
            stdout = result.stdout.decode('utf-8', errors='replace')
            stderr = result.stderr.decode('utf-8', errors='replace')
        except (UnicodeDecodeError, AttributeError):
            try:
                stdout = result.stdout.decode('latin-1', errors='replace')
                stderr = result.stderr.decode('latin-1', errors='replace')
            except:
                stdout = str(result.stdout, errors='replace')
                stderr = str(result.stderr, errors='replace')

        if result.returncode != 0:
            raise ArchiveError(f"7z command failed ({result.returncode}): {stderr.strip()}")

        # Parse output
        try:
            files_info = _parse7zListOutput(stdout)
            return files_info
        except Exception as e:
            raise ArchiveParsingError(f"Failed to parse 7z output: {str(e)}")
        
    except subprocess.CalledProcessError as e:
        # This shouldn't happen with check=False, but just in case
        stderr_lower = str(e.stderr).lower()

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


def _parse7zListOutput(output: str) -> List[Dict[str, Union[str, int]]]:
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
                files.append(_formatFileInfo(current_file))
            
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
        files.append(_formatFileInfo(current_file))
    
    return files


def _formatFileInfo(file_data: Dict[str, str]) -> Dict[str, Union[str, int]]:
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


def extractArchiveWith7z(
    archive_path: str,
    output_path: str,
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
    overwrite: bool = True,
    specific_files: Optional[List[str]] = None
) -> bool:
    """
    Extract archive using 7z.exe with optional password support.
    
    Args:
        archive_path (str): Path to the archive file
        output_path (str): Directory where files will be extracted
        password (str, optional): Password for encrypted archives
        seven_zip_path (str): Path to 7z.exe executable (default: auto-detect)
        overwrite (bool): Whether to overwrite existing files (default: True)
        specific_files (List[str], optional): List of specific files to extract
    
    Returns:
        bool: True if extraction successful
    
    Raises:
        ArchiveNotFoundError: If archive file not found
        SevenZipNotFoundError: If 7z executable not found
        ArchivePasswordError: If password is incorrect or required
        ArchiveCorruptedError: If archive is corrupted
        ArchiveUnsupportedError: If archive format is not supported
        ArchiveError: For other extraction errors
    """
    
    # Set default 7z path if not provided
    if seven_zip_path is None:
        seven_zip_path = _get_default_7z_path()
    
    # Check if archive exists
    if not os.path.exists(archive_path):
        raise ArchiveNotFoundError(f"Archive not found: {archive_path}")
    
    # Check if 7z executable exists
    if not os.path.exists(seven_zip_path):
        raise SevenZipNotFoundError(f"7z executable not found at: {seven_zip_path}")
    
    # Create output directory if it doesn't exist
    try:
        os.makedirs(output_path, exist_ok=True)
    except OSError as e:
        raise ArchiveError(f"Failed to create output directory: {e}")
    
    # Build command - 7z can handle SFX files directly without special flags
    cmd = [seven_zip_path, "x", archive_path, f"-o{output_path}"]
    
    # Add password if provided
    cmd.extend([f"-p{password}"])
    
    # Add overwrite option
    if overwrite:
        cmd.append("-y")  # Yes to all prompts (overwrite)
    else:
        cmd.append("-aos")  # Skip existing files
    
    # Add specific files if provided
    if specific_files:
        cmd.extend(specific_files)
    
    try:
        # Execute 7z command with proper encoding handling
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,  # Use bytes to avoid encoding issues
            check=False,  # Don't raise exception on non-zero return code
        )
        
        # Decode output safely with multiple fallbacks
        stdout = ""
        stderr = ""
        
        try:
            stdout = result.stdout.decode('utf-8', errors='replace')
            stderr = result.stderr.decode('utf-8', errors='replace')
        except (UnicodeDecodeError, AttributeError):
            # Fallback to latin1 if utf-8 fails
            try:
                stdout = result.stdout.decode('latin-1', errors='replace')
                stderr = result.stderr.decode('latin-1', errors='replace')
            except:
                # Final fallback - convert bytes to string representation
                try:
                    stdout = result.stdout.decode('cp1252', errors='replace')
                    stderr = result.stderr.decode('cp1252', errors='replace')
                except:
                    stdout = str(result.stdout)
                    stderr = str(result.stderr)

        if result.returncode != 0:
            raise ArchiveError(f"7z extraction failed ({result.returncode}): {stderr.strip()}")

        return True
        
    except subprocess.CalledProcessError as e:
        # This shouldn't happen since we use check=False, but handle it just in case
        try:
            stderr = e.stderr.decode('utf-8', errors='replace') if hasattr(e, 'stderr') and e.stderr else str(e)
        except:
            stderr = str(e)
        stderr_lower = stderr.lower()

        # Check for Windows path-related errors
        if ("cannot create folder" in stderr_lower or 
            "cannot open output file" in stderr_lower or
            "the system cannot find the path specified" in stderr_lower):
            
            print_warning(f"Path-related extraction error detected, trying alternative extraction method...", 2)
            return _extractWithSanitizedPaths(archive_path, output_path, password, seven_zip_path, overwrite, specific_files)

        elif "wrong password" in stderr_lower or "cannot open encrypted archive" in stderr_lower:
            raise ArchivePasswordError(f"Incorrect password or password required for: {archive_path}")
        elif "data error" in stderr_lower or "crc failed" in stderr_lower:
            raise ArchiveCorruptedError(f"Archive appears to be corrupted: {archive_path}")
        elif "unsupported method" in stderr_lower or "unknown method" in stderr_lower:
            raise ArchiveUnsupportedError(f"Archive format not supported: {archive_path}")
        elif "cannot open file" in stderr_lower:
            raise ArchiveNotFoundError(f"Cannot open archive file: {archive_path}")
        elif "disk full" in stderr_lower or "not enough space" in stderr_lower:
            raise ArchiveError(f"Insufficient disk space for extraction: {archive_path}")
        else:
            # Generic archive error for other cases
            raise ArchiveError(f"7z extraction error ({e.returncode}): {e.stderr.strip()}")
    
    except FileNotFoundError:
        raise SevenZipNotFoundError(f"7z executable not found at: {seven_zip_path}")


def _extractWithSanitizedPaths(
    archive_path: str,
    output_path: str,
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
    overwrite: bool = True,
    specific_files: Optional[List[str]] = None
) -> bool:
    """
    Extract archive using a temporary directory with sanitized paths.
    
    This is a fallback method when the direct extraction fails due to invalid
    Windows filenames or path length issues.
    """
    temp_dir = None
    
    try:
        # Create a temporary directory for extraction
        temp_dir = tempfile.mkdtemp(prefix="complex_unzip_temp_")
        print_info(f"Using temporary extraction directory: {temp_dir}", 3)
        
        # Try extracting to temp directory first
        temp_cmd = [seven_zip_path, "x", archive_path, f"-o{temp_dir}"]
        temp_cmd.extend([f"-p{password}"])
        if overwrite:
            temp_cmd.append("-y")
        else:
            temp_cmd.append("-aos")
        if specific_files:
            temp_cmd.extend(specific_files)
        
        # Execute extraction to temp directory
        result = subprocess.run(
            temp_cmd,
            capture_output=True,
            text=False,  # Use bytes to avoid encoding issues
            check=False,  # Don't raise exception on non-zero return
        )
        
        # Decode output safely
        try:
            stdout = result.stdout.decode('utf-8', errors='replace')
            stderr = result.stderr.decode('utf-8', errors='replace')
        except (UnicodeDecodeError, AttributeError):
            try:
                stdout = result.stdout.decode('latin-1', errors='replace')
                stderr = result.stderr.decode('latin-1', errors='replace')
            except:
                stdout = str(result.stdout, errors='replace')
                stderr = str(result.stderr, errors='replace')
        
        if result.returncode != 0:
            # If still failing, it's likely a password or corruption issue
            stderr_lower = stderr.lower()
            if "wrong password" in stderr_lower or "cannot open encrypted archive" in stderr_lower:
                raise ArchivePasswordError(f"Incorrect password or password required for: {archive_path}")
            elif "data error" in stderr_lower or "crc failed" in stderr_lower:
                raise ArchiveCorruptedError(f"Archive appears to be corrupted: {archive_path}")
            else:
                raise ArchiveError(f"7z extraction error ({result.returncode}): {stderr.strip()}")
        
        # Now move files from temp directory to final destination with sanitized names
        try:
            _moveAndSanitizeFiles(temp_dir, output_path)
            print_success("Successfully extracted with sanitized file paths", 2)
            return True
        except Exception as e:
            raise ArchiveError(f"Failed to move extracted files: {e}")
        
    except Exception as e:
        # Re-raise specific archive exceptions, wrap others
        if isinstance(e, (ArchivePasswordError, ArchiveCorruptedError, ArchiveUnsupportedError, ArchiveNotFoundError, ArchiveError)):
            raise
        else:
            raise ArchiveError(f"Extraction failed: {e}")
        
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except OSError:
                pass  # Ignore cleanup errors


def _moveAndSanitizeFiles(source_dir: str, target_dir: str) -> None:
    """
    Move files from source to target directory, sanitizing names as needed.
    """
    if not os.path.exists(source_dir):
        return
    
    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)
    
    # Process all files and directories
    for root, dirs, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)
        
        # Determine target subdirectory
        if rel_path != ".":
            sanitized_rel_path = sanitize_path(rel_path)
            target_subdir = os.path.join(target_dir, sanitized_rel_path)
        else:
            target_subdir = target_dir
        
        # Handle directory conflicts by adding counter if needed
        if target_subdir != target_dir and os.path.exists(target_subdir):
            counter = 1
            base_target_subdir = target_subdir
            while os.path.exists(target_subdir):
                parent_dir = os.path.dirname(base_target_subdir)
                dir_name = os.path.basename(base_target_subdir)
                target_subdir = os.path.join(parent_dir, f"{dir_name}_{counter}")
                counter += 1
            
            if counter > 1:
                print_info(f"Directory conflict resolved: {os.path.basename(base_target_subdir)} → {os.path.basename(target_subdir)}", 3)
        
        # Create target directory
        os.makedirs(target_subdir, exist_ok=True)
        
        # Move files with sanitized names
        for file in files:
            source_file = os.path.join(root, file)
            sanitized_filename = sanitize_filename(file)
            target_file = os.path.join(target_subdir, sanitized_filename)
            
            # Handle file name conflicts by adding counter
            counter = 1
            base_target = target_file
            while os.path.exists(target_file):
                name, ext = os.path.splitext(base_target)
                target_file = f"{name}_{counter}{ext}"
                counter += 1
            
            try:
                # Use copy2 + remove instead of move to avoid cross-device issues
                shutil.copy2(source_file, target_file)
                os.remove(source_file)
                
                if sanitized_filename != file or counter > 1:
                    print_info(f"Moved file: {file} → {os.path.basename(target_file)}", 3)
                    
            except OSError as e:
                # If copy fails, try a more robust approach
                try:
                    with open(source_file, 'rb') as src, open(target_file, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    os.remove(source_file)
                    print_info(f"Moved file (fallback): {file} → {os.path.basename(target_file)}", 3)
                except OSError as e2:
                    print_warning(f"Failed to move file {file}: {e2}", 2)
                    # Don't raise exception, just continue with other files


def extractSpecificFilesWith7z(
    archive_path: str,
    output_path: str,
    file_list: List[str],
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
    overwrite: bool = True
) -> Dict[str, bool]:
    """
    Extract specific files from archive using 7z.exe.
    
    Args:
        archive_path (str): Path to the archive file
        output_path (str): Directory where files will be extracted
        file_list (List[str]): List of file paths to extract
        password (str, optional): Password for encrypted archives
        seven_zip_path (str): Path to 7z.exe executable (default: auto-detect)
        overwrite (bool): Whether to overwrite existing files
    
    Returns:
        Dict[str, bool]: Dictionary mapping file paths to extraction success status
    
    Raises:
        Same exceptions as extract_archive_with_7z
    """
    
    results = {}
    
    # Extract all specified files in one operation for efficiency
    try:
        success = extractArchiveWith7z(
            archive_path=archive_path,
            output_path=output_path,
            password=password,
            seven_zip_path=seven_zip_path,
            overwrite=overwrite,
            specific_files=file_list
        )
        
        # If extraction succeeded, check which files were actually extracted
        for file_path in file_list:
            extracted_path = os.path.join(output_path, file_path)
            results[file_path] = os.path.exists(extracted_path)
            
    except Exception as e:
        # If extraction failed, mark all files as failed
        for file_path in file_list:
            results[file_path] = False
        raise e
    
    return results

def extract_nested_archives(
    archive_path: str,
    output_path: str,
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
    max_depth: int = 10,
    cleanup_archives: bool = True,
    password_list: Optional[List[str]] = None,
    interactive: bool = True,
    loading_indicator = None,
    active_progress_bars: Optional[List] = None,
    use_recycle_bin: bool = True
) -> Dict[str, Union[bool, List[str]]]:
    """
    Recursively extract archives within archives until no more archives are found.
    
    Args:
        archive_path (str): Path to the initial archive file
        output_path (str): Directory where files will be extracted
        password (str, optional): Primary password for encrypted archives
        seven_zip_path (str): Path to 7z.exe executable (default: auto-detect)
        max_depth (int): Maximum recursion depth to prevent infinite loops (default: 10)
        cleanup_archives (bool): Whether to delete extracted archive files after processing
        password_list (List[str], optional): List of passwords to try for extraction
        interactive (bool): Whether to prompt user for passwords when all fail (default: True)
        loading_indicator: Loading indicator instance to stop/start during user prompts
    
    Returns:
        Dict containing:
            - 'success': bool - Overall extraction success
            - 'extracted_archives': List[str] - List of all archives that were extracted
            - 'final_files': List[str] - List of final non-archive files
            - 'errors': List[str] - List of errors encountered
            - 'password_used': Dict[str, str] - Mapping of archives to passwords that worked
            - 'user_provided_passwords': List[str] - List of passwords provided by the user

    Raises:
        Same exceptions as extractArchiveWith7z for the initial archive
    """
    
    result = {
        'success': True,
        'extracted_archives': [],
        'final_files': [],
        'errors': [],
        'password_used': {},
        'user_provided_passwords': []
    }

    # Build user provided passwords
    user_provided_passwords = []

    # Build password list to try
    passwords_to_try = []
    if password:
        passwords_to_try.append(password)
    if password_list:
        passwords_to_try.extend([p for p in password_list if p not in passwords_to_try])
    
    # Always try empty password (no password) first
    if "" not in passwords_to_try:
        passwords_to_try.insert(0, "")
    
    def _tryOpenAsArchive(file_path: str) -> bool:
        """Try to open a file as an archive. Returns True if successful."""
        try:
            # Try to read the file as an archive with primary password
            content = readArchiveContentWith7z(
                archive_path=file_path,
                password=password,
                seven_zip_path=seven_zip_path
            )
            # If we can read content and it's not empty, it's a valid archive
            return content is not None and len(content) > 0
            
        except (ArchivePasswordError):
            # If password error, it means 7z recognized this as a valid archive format
            # but couldn't access the content due to encryption - still a valid archive
            return True
                
        except (ArchiveError, ArchiveCorruptedError, ArchiveUnsupportedError, ArchiveParsingError):
            # Cannot read as archive
            return False
        except Exception:
            # Any other error, treat as non-archive
            return False
    
    def _promptUserForPassword(archive_name: str, active_progress_bars: Optional[List] = None) -> Optional[str]:
        """
        Prompt user for password when all automatic attempts fail.
        提示用户输入密码，当所有自动尝试失败时
        
        Args:
            archive_name (str): Name of the archive requiring password
            active_progress_bars (List, optional): List of active progress bars to temporarily stop
        
        Returns:
            str: User-provided password or None if user chooses to skip
        """
        if not interactive:
            return None
        
        # Stop loading indicator if it exists
        if loading_indicator and hasattr(loading_indicator, 'stop'):
            loading_indicator.stop()
        
        # Stop all active progress bars to prevent interference with user input
        stopped_progress_bars = []
        if active_progress_bars:
            for progress_bar in active_progress_bars:
                if hasattr(progress_bar, 'stop') and hasattr(progress_bar, 'progress') and progress_bar.progress:
                    progress_bar.stop()
                    stopped_progress_bars.append(progress_bar)
        
        
        
        # Clear any remaining display artifacts and ensure clean terminal state
        console.clear()
        
        console.print()
        console.print(f"[bold yellow]⚠️  All provided passwords failed for archive: {archive_name}[/bold yellow]")
        console.print(f"[dim yellow]   所有提供的密码对档案都失败了: {archive_name}[/dim yellow]")
        console.print()
        console.print("[bold bright_blue]Options 选项:[/bold bright_blue]")
        console.print("  [bold cyan]1.[/bold cyan] Enter a password 输入密码")
        console.print("  [bold cyan]2.[/bold cyan] Skip this archive 跳过此档案")
        console.print("  [bold cyan]3.[/bold cyan] Skip all remaining password-protected archives 跳过所有剩余的密码保护档案")
        console.print()
        
        # Use a simple input loop to ensure compatibility
        while True:
            try:
                choice_input = input("Choose an option 选择一个选项 (1/2/3) [default: 2]: ").strip()
                if choice_input == "":
                    choice = 2
                    break
                else:
                    choice = int(choice_input)
                    if choice in [1, 2, 3]:
                        break
                    else:
                        console.print("[red]Please enter 1, 2, or 3 请输入 1、2 或 3[/red]")
            except (ValueError, KeyboardInterrupt):
                choice = 2
                break
        
        result = None
        if choice == 1:
            try:
                password = input("Enter password 输入密码: ")
                user_provided_passwords.append(password)
                result = password
            except KeyboardInterrupt:
                result = None
        elif choice == 3:
            # User wants to skip all future password prompts
            result = "SKIP_ALL"
        else:
            # Skip this archive
            result = None
        
        # Show user that processing is continuing
        if result is not None and result != "SKIP_ALL":
            console.print()
            console.print("[bold green]✓ Continuing with extraction... 继续提取...[/bold green]")
        
        # Note: We don't restart the progress bars here as they will interfere again
        # The extraction process will continue normally without progress display during user input
        
        # Restart loading indicator if it exists
        if loading_indicator and hasattr(loading_indicator, 'start'):
            loading_indicator.start()
            
        return result
    
    def _tryExtractWithPasswords(archive_file: str, extract_to: str, active_progress_bars: Optional[List] = None) -> tuple[bool, str]:
        """
        Try to extract an archive with different passwords.
        Note: This function assumes the file has already been verified as a valid archive.
        
        Returns:
            tuple: (success: bool, password_used: str)
        """
        archive_name = os.path.basename(archive_file)
        skip_all_prompts = False
        password_required = False
        
        # Try all provided passwords first
        if passwords_to_try:
            print_info(f"🔐 Trying {len(passwords_to_try)} passwords 尝试 {len(passwords_to_try)} 个密码...", 1)
        
        for pwd in passwords_to_try:
            try:
                success = extractArchiveWith7z(
                    archive_path=archive_file,
                    output_path=extract_to,
                    password=pwd,
                    seven_zip_path=seven_zip_path,
                    overwrite=True
                )
                
                if success:
                    print_password_success(pwd)
                    return True, pwd
                    
            except ArchivePasswordError:
                password_required = True  # Mark that this is a valid archive that needs password
                continue
                
            except (ArchiveCorruptedError, ArchiveUnsupportedError, ArchiveNotFoundError) as e:
                # These are archive-related errors that should stop password attempts immediately
                print_error(f"Archive error 档案错误: {str(e)}", 1)
                print_info(f"Skipping remaining passwords for this archive 跳过此档案的剩余密码", 2)
                return False, ""
                
            except ArchiveError as e:
                # Generic archive errors - check if it's a path-related error that should stop
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in [
                    "path", "file name", "directory", "cannot create", 
                    "access denied", "permission", "disk full", "not enough space"
                ]):
                    print_error(f"File system error 文件系统错误: {str(e)}", 1)
                    print_info(f"Skipping remaining passwords for this archive 跳过此档案的剩余密码", 2)
                    return False, ""
                else:
                    # Other archive errors might be password-related, continue with next password
                    continue
                    
            except Exception as e:
                # Unexpected errors - these could be system issues, stop trying passwords
                print_error(f"Unexpected error 意外错误: {str(e)}", 1)
                print_info(f"Skipping remaining passwords for this archive 跳过此档案的剩余密码", 2)
                return False, ""
        
        # Only prompt user for passwords if we confirmed this is a valid archive that requires password
        if interactive and not skip_all_prompts and password_required:
            if passwords_to_try:
                print_warning(f"None of the {len(passwords_to_try)} provided passwords worked 提供的 {len(passwords_to_try)} 个密码都无效", 1)
                
            while True:
                user_password = _promptUserForPassword(archive_name, active_progress_bars)
                
                if user_password == "SKIP_ALL":
                    print_info("Skipping all future password prompts 跳过所有未来的密码提示", 2)
                    return False, ""
                elif user_password is None:
                    print_info(f"Skipping archive 跳过档案: {archive_name}", 2)
                    return False, ""
                
                # Try the user-provided password
                try:
                    print_info("Trying user-provided password 尝试用户提供的密码...", 2)
                    success = extractArchiveWith7z(
                        archive_path=archive_file,
                        output_path=extract_to,
                        password=user_password,
                        seven_zip_path=seven_zip_path,
                        overwrite=True
                    )
                    
                    if success:
                        print_success("Extraction successful with user password 使用用户密码提取成功!", 1)
                        # Add the successful password to the list for future use
                        passwords_to_try.append(user_password)
                        return True, user_password
                        
                except ArchivePasswordError:
                    # Don't count password failures as errors - use warning instead
                    print_password_failed(user_password)
                    
                    # Stop loading indicator for user input
                    if loading_indicator and hasattr(loading_indicator, 'stop'):
                        loading_indicator.stop()
                    
                    # Stop all active progress bars to prevent interference with user input
                    if active_progress_bars:
                        for progress_bar in active_progress_bars:
                            if hasattr(progress_bar, 'stop') and hasattr(progress_bar, 'progress') and progress_bar.progress:
                                progress_bar.stop()
                    
                    # Use simple input instead of typer.confirm for better compatibility
                    from .rich_utils import console
                    console.print()
                    console.print("[bold yellow]Password incorrect 密码不正确[/bold yellow]")
                    
                    while True:
                        try:
                            continue_input = input("Try another password 尝试另一个密码? (Y/n) [default: Y]: ").strip().lower()
                            if continue_input == "" or continue_input in ['y', 'yes', '是']:
                                continue_prompt = True
                                break
                            elif continue_input in ['n', 'no', '否']:
                                continue_prompt = False
                                break
                            else:
                                console.print("[red]Please enter Y or N 请输入 Y 或 N[/red]")
                        except KeyboardInterrupt:
                            continue_prompt = False
                            break
                    
                    # Restart loading indicator
                    if loading_indicator and hasattr(loading_indicator, 'start'):
                        loading_indicator.start()
                    
                    if not continue_prompt:
                        return False, ""
                    continue
                    
                except (ArchiveCorruptedError, ArchiveUnsupportedError, ArchiveNotFoundError) as e:
                    # These are archive-related errors that should stop user password attempts
                    print_error(f"Archive error 档案错误: {str(e)}", 1)
                    print_info(f"Cannot continue with this archive 无法继续处理此档案", 2)
                    return False, ""
                    
                except ArchiveError as e:
                    # Generic archive errors - check if it's a path-related error that should stop
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in [
                        "path", "file name", "directory", "cannot create", 
                        "access denied", "permission", "disk full", "not enough space"
                    ]):
                        print_error(f"File system error 文件系统错误: {str(e)}", 1)
                        print_info(f"Cannot continue with this archive 无法继续处理此档案", 2)
                        return False, ""
                    else:
                        # Other archive errors might be password-related, continue
                        print_error(f"Extraction failed with user password 使用用户密码提取失败: {str(e)}", 1)
                        print_info(f"Cannot continue with this archive 无法继续处理此档案", 2)
                        return False, ""
                        
                except Exception as e:
                    print_error(f"Unexpected error 意外错误: {str(e)}", 1)
                    print_info(f"Cannot continue with this archive 无法继续处理此档案", 2)
                    return False, ""
        else:
            # If no password was required but extraction still failed, show appropriate message
            if password_required:
                print_warning(f"Archive requires password but user chose to skip 档案需要密码但用户选择跳过: {archive_name}", 1)
            else:
                print_warning(f"Failed to extract archive 提取档案失败: {archive_name}", 1)
        
        return False, ""
    
    def _extractRecursively(current_archive: str, current_output: str, depth: int) -> None:
        """Recursively extract archives while preserving folder structure 递归提取档案，同时保持文件夹结构."""
        
        if depth > max_depth:
            error_msg = f"Maximum recursion depth ({max_depth}) reached for 达到最大递归深度: {current_archive}"
            result['errors'].append(error_msg)
            print_warning(error_msg, 1)
            return
        
        try:
            # First, verify that this is actually a valid archive before attempting extraction
            if not _tryOpenAsArchive(current_archive):
                error_msg = f"File is not a valid archive 文件不是有效档案: {current_archive}"
                result['errors'].append(error_msg)
                print_warning(error_msg, 2)
                return
            
            # Extract directly to the current output directory to preserve structure
            print_extracting_archive(os.path.basename(current_archive), depth)
            
            extract_success, used_password = _tryExtractWithPasswords(current_archive, current_output, active_progress_bars)
            
            if extract_success:
                result['extracted_archives'].append(current_archive)
                result['password_used'][current_archive] = used_password
                result['user_provided_passwords'] = list(set(user_provided_passwords))
                
                # Find all files in the extracted directory (walk from current_output)
                extracted_files = []
                
                for root, dirs, files in os.walk(current_output):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Skip the original archive files that we already processed
                        if file_path != current_archive and file_path not in result['extracted_archives']:
                            extracted_files.append(file_path)
                
                # Find newly extracted archives to process recursively
                nested_archives = []
                regular_files = []
                
                print_info(f"Testing {len(extracted_files)} extracted files for nested archives", 2)
                print_info(f"正在测试 {len(extracted_files)} 个提取的文件是否为嵌套档案...", 3)
                
                for file_path in extracted_files:
                    file_name = os.path.basename(file_path)
                    
                    # Skip files that were already processed
                    if file_path in result['extracted_archives']:
                        continue
                    
                    if _tryOpenAsArchive(file_path):
                        print_info(f"📦 Found nested archive 发现嵌套档案: {file_name}", 3)
                        nested_archives.append(file_path)
                    else:
                        regular_files.append(file_path)
                
                # Add regular files to final files list
                result['final_files'].extend(regular_files)
                
                if regular_files:
                    print_info(f"Found {len(regular_files)} regular files 发现 {len(regular_files)} 个常规文件", 2)
                
                # Delete the processed archive file if cleanup is enabled and it's not the original
                if cleanup_archives and current_archive != archive_path:
                    try:
                        
                        safe_remove(current_archive, use_recycle_bin=use_recycle_bin)
                        if use_recycle_bin:
                            print_success(f"Moved nested archive to recycle bin 已将嵌套档案移至回收站: {os.path.basename(current_archive)}", 2)
                        else:
                            print_success(f"Cleaned up archive 已清理档案: {os.path.basename(current_archive)}", 2)
                    except OSError as e:
                        error_msg = f"Failed to delete 删除失败 {current_archive}: {e}"
                        result['errors'].append(error_msg)
                        print_warning(error_msg, 2)
                
                # If we found nested archives, extract them recursively in their current location
                if nested_archives:
                    print_info(f"Found {len(nested_archives)} nested archive(s)", 2)
                    print_info(f"在深度 {depth} 发现 {len(nested_archives)} 个嵌套档案", 3)
                    for nested_archive in nested_archives:
                        # Extract nested archive in the same directory to preserve structure
                        nested_output_dir = os.path.dirname(nested_archive)
                        _extractRecursively(nested_archive, nested_output_dir, depth + 1)
                else:
                    print_success(f"No more nested archives found at depth {depth}", 2)
                    print_info(f"在深度 {depth} 未发现更多嵌套档案", 3)
            
            else:
                # Extraction failed - but this could be due to password issues, which are not "errors"
                # Only add to errors if it's a system/technical error, not password-related
                print_warning(f"Could not extract 无法提取: {current_archive} (tried all available passwords 尝试了所有可用密码)", 2)
                # Note: This is not added to errors list as it's likely a password issue, not a system error
                
        except Exception as e:
            error_msg = f"Error extracting 提取错误 {current_archive}: {e}"
            result['errors'].append(error_msg)
            result['success'] = False
            print_error(error_msg, 2)
    
    # Start the recursive extraction
    try:
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
        
        print_nested_extraction_header(
            archive_path, 
            output_path, 
            len(passwords_to_try), 
            max_depth
        )
        print_extraction_process_header()
        
        # Begin recursive extraction with the initial archive
        _extractRecursively(archive_path, output_path, 0)
        
        # Clean up empty directories
        print_empty_line()
        print_info("🧹 Cleaning up empty directories 清理空目录...")
        _cleanupEmptyDirectories(output_path)
        
        # Update final success status
        result['success'] = result['success'] and len(result['errors']) == 0
        
        # Show final summary
        status = "SUCCESS" if result['success'] else "PARTIAL/FAILED"
        print_extraction_summary(
            status,
            len(result['extracted_archives']),
            len(result['final_files']),
            len(result['errors'])
        )
        
        if result['errors']:
            print_error_summary(result['errors'])
        
    except Exception as e:
        error_msg = f"Fatal error during extraction 提取期间发生致命错误: {e}"
        result['errors'].append(error_msg)
        result['success'] = False
        print_error(f"💥 {error_msg}", 0)
        raise
    
    return result

def _cleanupEmptyDirectories(root_path: str) -> None:
    """
    Remove empty directories recursively.
    
    Args:
        root_path (str): Root directory to clean up
    """
    try:
        for root, dirs, files in os.walk(root_path, topdown=False):
            for directory in dirs:
                dir_path = os.path.join(root, directory)
                try:
                    # Try to remove directory if it's empty
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except OSError:
                    # Directory not empty or other error, skip
                    pass
    except Exception:
        # Ignore cleanup errors
        pass