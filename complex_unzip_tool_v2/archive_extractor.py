"""Archive extraction utilities for the Complex Unzip Tool."""

import os
import subprocess
import shutil
import threading
import time
import signal
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import re


class ExtractionResult:
    """Class to track extraction results."""
    
    def __init__(self):
        self.successful_extractions = []
        self.failed_extractions = []
        self.passwords_used = []
        self.new_passwords = []
        self.processed_files = set()
        self.completed_files = []


def get_7z_executable() -> Path:
    """Get the path to the 7z executable.
    
    Returns:
        Path to 7z.exe
    """
    current_dir = Path(__file__).parent.parent
    seven_z_path = current_dir / "7z" / "7z.exe"
    
    if not seven_z_path.exists():
        raise FileNotFoundError(f"7z.exe not found at {seven_z_path}")
    
    return seven_z_path


def is_archive_file(file_path: Path) -> bool:
    """Check if a file is likely an archive file.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        Always True - treat all files as potential archives for maximum detection
    """
    # Always treat any file as a potential archive to catch all cloaked files
    return True


def is_partial_archive(archive_path: Path) -> Tuple[bool, Optional[str]]:
    """Check if an archive file contains partial/part files that need reassembly.
    
    Args:
        archive_path: Path to the archive file
        
    Returns:
        Tuple of (is_partial, base_name) where base_name is the detected base name for parts
    """
    # Get the 7z executable
    try:
        seven_z = get_7z_executable()
    except Exception:
        return False, None
    
    # Use 7z to list the contents and check for partial file indicators
    try:
        cmd = [str(seven_z), 'l', str(archive_path)]
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=5,  # Very short timeout for listing - just 5 seconds
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            output = result.stdout.lower()
            lines = output.split('\n')
            
            # Look for files with partial extensions
            for line in lines:
                # Check for common partial file patterns
                if re.search(r'\.\d{3}$', line):  # .001, .002, .003, etc.
                    # Extract the base name (everything before .001, .002, etc.)
                    match = re.search(r'(\w+)\.(\d{3})$', line.strip())
                    if match:
                        base_name = match.group(1)
                        return True, base_name
                
                # Check for .part patterns
                if re.search(r'\.part\d+$', line):
                    match = re.search(r'(\w+)\.part(\d+)$', line.strip())
                    if match:
                        base_name = match.group(1)
                        return True, base_name
                        
                # Check for .z patterns        
                if re.search(r'\.z\d{2}$', line):
                    match = re.search(r'(\w+)\.z(\d{2})$', line.strip())
                    if match:
                        base_name = match.group(1)
                        return True, base_name
                    
        return False, None
        
    except subprocess.TimeoutExpired:
        # If listing times out, assume it might be a problematic archive but not partial
        return False, None
    except Exception:
        return False, None


def run_with_timeout(cmd, timeout_seconds=300):
    """Run a command with a robust timeout mechanism that can handle hanging processes."""
    import subprocess
    import threading
    import time
    
    result = {'process': None, 'stdout': '', 'stderr': '', 'returncode': None, 'timed_out': False}
    
    def target():
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            result['process'] = process
            stdout, stderr = process.communicate()
            result['stdout'] = stdout
            result['stderr'] = stderr
            result['returncode'] = process.returncode
        except Exception as e:
            result['stderr'] = str(e)
            result['returncode'] = -1
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        # Thread is still running, process timed out
        result['timed_out'] = True
        if result['process']:
            try:
                # Try to terminate the process gracefully
                result['process'].terminate()
                time.sleep(2)
                if result['process'].poll() is None:
                    # Force kill if still running
                    result['process'].kill()
                    time.sleep(1)
            except Exception:
                pass
        
        # Wait a bit more for thread to finish
        thread.join(5)
    
    return result


def run_with_progress(cmd, timeout_seconds=300, progress_callback=None):
    """Run a command with simple progress indication.
    
    Args:
        cmd: Command to run
        timeout_seconds: Maximum time to wait
        progress_callback: Function to call with progress updates
        
    Returns:
        Same format as run_with_timeout but with progress indication
    """
    import subprocess
    import threading
    import time
    import sys
    
    result = {'process': None, 'stdout': '', 'stderr': '', 'returncode': None, 'timed_out': False}
    progress_active = True
    
    def progress_indicator():
        """Show a simple progress indicator while extraction is running."""
        if not progress_callback:
            return
            
        dots = 0
        while progress_active:
            progress_callback(f"{'.' * (dots % 4):<3}")
            dots += 1
            time.sleep(1)
    
    def target():
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            result['process'] = process
            stdout, stderr = process.communicate()
            result['stdout'] = stdout
            result['stderr'] = stderr
            result['returncode'] = process.returncode
        except Exception as e:
            result['stderr'] = str(e)
            result['returncode'] = -1
    
    # Start progress indicator thread
    if progress_callback:
        progress_thread = threading.Thread(target=progress_indicator)
        progress_thread.daemon = True
        progress_thread.start()
    
    # Start main process thread
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    # Stop progress indicator
    progress_active = False
    
    if thread.is_alive():
        # Thread is still running, process timed out
        result['timed_out'] = True
        if result['process']:
            try:
                # Try to terminate the process gracefully
                result['process'].terminate()
                time.sleep(2)
                if result['process'].poll() is None:
                    # Force kill if still running
                    result['process'].kill()
                    time.sleep(1)
            except Exception:
                pass
        
        # Wait a bit more for thread to finish
        thread.join(5)
    
    return result


def get_ascii_multipart_paths(group_files: List[Path], temp_dir: Optional[Path] = None) -> Tuple[List[Path], bool]:
    """Create temporary ASCII-only paths for multi-part archives with Chinese characters.
    
    Args:
        group_files: List of files that make up the multi-part archive
        temp_dir: Directory to create temp files in (optional)
        
    Returns:
        Tuple of (temp_paths, needs_cleanup) where needs_cleanup indicates if temp files were created
    """
    # Check if any path contains non-ASCII characters
    needs_temp = False
    for path in group_files:
        try:
            str(path).encode('ascii')
        except UnicodeEncodeError:
            needs_temp = True
            break
    
    if not needs_temp:
        # All paths are ASCII-safe, no need for temp copies
        return group_files, False
    
    # Create temp directory
    if temp_dir is None:
        temp_dir = Path(tempfile.gettempdir())
    
    # Create a unique base name for the multi-part archive
    base_name = f"temp_multipart_{uuid.uuid4().hex[:8]}"
    temp_paths = []
    
    # Copy all parts with sequential naming
    for i, original_path in enumerate(sorted(group_files, key=lambda p: p.suffix)):
        if original_path.is_file():
            # Preserve the original part number
            part_suffix = original_path.suffix  # e.g., '.001', '.002', '.003'
            temp_name = f"{base_name}{part_suffix}"
            temp_path = temp_dir / temp_name
            
            # Copy the original file to temp location
            shutil.copy2(original_path, temp_path)
            temp_paths.append(temp_path)
    
    return temp_paths, True


def get_ascii_temp_path(original_path: Path, temp_dir: Optional[Path] = None) -> Tuple[Path, bool]:
    """Create a temporary ASCII-only path for files with Chinese characters.
    
    Args:
        original_path: Original file path that may contain Chinese characters
        temp_dir: Directory to create temp file in (optional)
        
    Returns:
        Tuple of (temp_path, needs_cleanup) where needs_cleanup indicates if temp file was created
    """
    # Check if path contains non-ASCII characters
    try:
        str(original_path).encode('ascii')
        # Path is ASCII-safe, no need for temp copy
        return original_path, False
    except UnicodeEncodeError:
        # Path contains non-ASCII characters, create temp copy
        if temp_dir is None:
            temp_dir = Path(tempfile.gettempdir())
        
        if original_path.is_file():
            # Create a unique ASCII filename for files
            # Use .7z extension for archives to avoid suffix issues with Chinese characters
            suffix = original_path.suffix
            try:
                suffix.encode('ascii')
                # Suffix is ASCII-safe
                ascii_suffix = suffix
            except UnicodeEncodeError:
                # Suffix contains non-ASCII characters, use generic .7z
                ascii_suffix = '.7z'
            
            temp_name = f"temp_archive_{uuid.uuid4().hex[:8]}{ascii_suffix}"
            temp_path = temp_dir / temp_name
            
            # Copy the original file to temp location
            shutil.copy2(original_path, temp_path)
            return temp_path, True
        else:
            # Create a unique ASCII directory name for directories
            temp_name = f"temp_extract_{uuid.uuid4().hex[:8]}"
            temp_path = temp_dir / temp_name
            temp_path.mkdir(parents=True, exist_ok=True)
            return temp_path, True


def extract_partial_archive_and_reassemble(archive_path: Path, output_dir: Path, passwords: List[str]) -> Tuple[bool, str, Optional[str]]:
    """Extract an archive containing partial files and then reassemble the complete archive.
    
    Args:
        archive_path: Path to the archive containing partial files
        output_dir: Directory to extract to
        passwords: List of passwords to try
        
    Returns:
        Tuple of (success, output_message, password_used)
    """
    from .console_utils import safe_print
    
    # First, let's check what's actually in this archive
    safe_print(f"  🔍 Analyzing partial archive: {archive_path.name}")
    
    # Use a shorter timeout for the container extraction to avoid hanging
    seven_z = get_7z_executable()
    
    # Create temp directory with ASCII name to avoid encoding issues
    temp_extract_dir, needs_cleanup = get_ascii_temp_path(output_dir.parent / f"temp_partial_{archive_path.stem}")
    if not needs_cleanup:
        temp_extract_dir = output_dir.parent / f"temp_partial_{archive_path.stem}"
    temp_extract_dir.mkdir(exist_ok=True)
    
    try:
        # Try to extract with shorter timeout first
        archive_temp, archive_needs_cleanup = get_ascii_temp_path(archive_path)
        
        try:
            # Always use -p with empty password first to avoid interactive prompts
            cmd = [str(seven_z), 'x', str(archive_temp), f'-o{str(temp_extract_dir)}', '-p', '-y']
            result = run_with_timeout(cmd, timeout_seconds=30)  # 30-second timeout for testing
            
            # If extraction failed, check if it's due to password
            if result['returncode'] != 0:
                stderr_text = result.get('stderr', '')
                stdout_text = result.get('stdout', '')
                
                # Check if it's a password issue
                if ("Wrong password" in stderr_text or "password" in stderr_text.lower() or 
                    "Wrong password" in stdout_text or "password" in stdout_text.lower()):
                    # Try with available passwords
                    for password in passwords:
                        cmd = [str(seven_z), 'x', str(archive_temp), f'-o{str(temp_extract_dir)}', f'-p{password}', '-y']
                        result = run_with_timeout(cmd, timeout_seconds=1800)  # 30 minute timeout for password attempts
                        
                        if result['timed_out']:
                            continue
                            
                        if result['returncode'] == 0:
                            safe_print(f"  📦 Extracted partial archive container with password | 使用密码解压部分压缩文件容器")
                            break
                    else:
                        # None of the available passwords worked, ask user
                        safe_print(f"  🔐 Archive requires password. Available passwords failed. | 压缩文件需要密码。可用密码失败。")
                        safe_print(f"  💡 Please add the correct password to passwords.txt file | 请将正确的密码添加到 passwords.txt 文件")
                        return False, f"Archive is password-protected and requires manual password entry", None
                else:
                    return False, f"Failed to extract partial archive: {stderr_text}", None
            
            if result['timed_out']:
                return False, f"Partial archive container extraction timed out (5 minutes). Archive may be corrupted: {archive_path.name}", None
            else:
                safe_print(f"  📦 Extracted partial archive container successfully | 部分压缩文件容器解压成功")
        
        finally:
            # Clean up temp archive copy
            if archive_needs_cleanup and archive_temp.exists():
                try:
                    archive_temp.unlink()
                except Exception:
                    pass
        
        # Find the partial files in the extracted content
        extracted_files = list(temp_extract_dir.rglob("*"))
        partial_files = []
        base_names = set()
        
        for file_path in extracted_files:
            if file_path.is_file():
                # Check for numbered extensions like .001, .002, .003
                if re.match(r'.*\.\d{3}$', file_path.name):
                    partial_files.append(file_path)
                    # Extract base name (everything before .001, .002, etc.)
                    base_name = re.sub(r'\.\d{3}$', '', file_path.name)
                    base_names.add(base_name)
        
        if not partial_files:
            # Maybe the archive itself is the partial file, not a container
            safe_print(f"  ⚠️ No partial files found in container. Treating as direct partial archive. | 容器中未找到部分文件。视为直接部分压缩文件。")
            return False, f"Archive {archive_path.name} appears to be a partial file itself, not a container. Look for other parts (.001, .002, etc.) in the same directory.", None
        
        safe_print(f"  🧩 Found {len(partial_files)} partial files for {len(base_names)} archive(s) | 找到 {len(partial_files)} 个部分文件，共 {len(base_names)} 个压缩文件")
        
        # Check if we have the first part (.001) - we need this to extract multi-part archives
        first_parts = [f for f in partial_files if f.name.endswith('.001')]
        if not first_parts:
            safe_print(f"  ⚠️ Missing .001 (first part) file. Cannot extract multi-part archive without first part. | 缺少 .001（第一部分）文件。没有第一部分无法解压多部分压缩文件。")
            return False, f"Missing first part (.001) for multi-part archive extraction", None
        
        # For each first part, try to extract the complete multi-part archive
        total_extracted = 0
        password_used = None
        
        for first_part in first_parts:
            base_name = re.sub(r'\.001$', '', first_part.name)
            safe_print(f"  🔗 Extracting multi-part archive: {base_name} | 解压多部分压缩文件: {base_name}")
            
            # Create output directory for this archive
            part_output_dir = output_dir / base_name
            part_output_dir.mkdir(exist_ok=True)
            
            # Progress callback for multi-part extraction
            def show_multipart_progress(dots):
                """Display multi-part extraction progress to user."""
                safe_print(f"  ⏳ Extracting {base_name}{dots} | 正在解压 {base_name}{dots}", end='\r')
            
            # Use progress-enabled extraction for multi-part archives
            cmd = [str(seven_z), 'x', str(first_part), f'-o{str(part_output_dir)}', '-y']
            result = run_with_progress(cmd, timeout_seconds=1800, progress_callback=show_multipart_progress)  # 30 minute timeout
            
            if result['timed_out']:
                safe_print(f"  ⏰ Extraction of {base_name} timed out (30 minutes) | {base_name} 解压超时 (30分钟)")
                continue
                
            if result['returncode'] == 0:
                safe_print()  # Clear progress line
                safe_print(f"  ✅ Successfully extracted complete {base_name} archive | 成功解压完整的 {base_name} 压缩文件")
                total_extracted += 1
            else:
                stderr_text = result.get('stderr', '')
                if "Wrong password" in stderr_text or "password" in stderr_text.lower():
                    # Try with passwords
                    for password in passwords:
                        cmd = [str(seven_z), 'x', str(first_part), f'-o{str(part_output_dir)}', f'-p{password}', '-y']
                        result = run_with_progress(cmd, timeout_seconds=1800, progress_callback=show_multipart_progress)
                        
                        if result['timed_out']:
                            continue
                            
                        if result['returncode'] == 0:
                            safe_print()  # Clear progress line
                            safe_print(f"  ✅ Successfully extracted {base_name} with password | 使用密码成功解压 {base_name}")
                            total_extracted += 1
                            password_used = password
                            break
                    else:
                        safe_print(f"  ❌ Failed to extract {base_name} with any password | 使用任何密码解压 {base_name} 失败")
                else:
                    safe_print(f"  ❌ Failed to extract {base_name}: {stderr_text} | 解压失败 {base_name}: {stderr_text}")
        
        if total_extracted > 0:
            return True, f"Successfully extracted {total_extracted} complete archives from partial files", password_used
        else:
            return False, "Failed to extract any complete archives from partial files", None
        
    finally:
        # Clean up temporary extraction directory
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir, ignore_errors=True)


def check_multipart_completeness(group_files: List[Path], base_name: str) -> Tuple[bool, List[int], List[int]]:
    """Check if a multi-part archive is complete by attempting extraction test.
    
    Args:
        group_files: List of files in the group
        base_name: Base name of the multi-part archive (without .001, .002, etc.)
        
    Returns:
        Tuple of (is_complete, found_parts, missing_parts)
    """
    found_parts = []
    
    # Look for parts in the current group
    for file_path in group_files:
        # Check for .001, .002, .003 pattern
        if re.match(rf'{re.escape(base_name)}\.(\d{{3}})$', file_path.name, re.IGNORECASE):
            match = re.search(rf'{re.escape(base_name)}\.(\d{{3}})$', file_path.name, re.IGNORECASE)
            if match:
                part_num = int(match.group(1))
                found_parts.append(part_num)
    
    if not found_parts:
        return False, [], []
    
    found_parts.sort()
    
    # Try to test extraction of the first part to see if 7z reports missing parts
    first_part_file = None
    for file_path in group_files:
        if file_path.name.lower().endswith('.001'):
            first_part_file = file_path
            break
    
    if first_part_file:
        try:
            seven_z = get_7z_executable()
            archive_temp, needs_cleanup = get_ascii_temp_path(first_part_file)
            
            try:
                # Test extraction (list files) to see if 7z reports missing volumes
                cmd = [str(seven_z), 'l', str(archive_temp)]
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    encoding='utf-8',
                    errors='replace'
                )
                
                # Check what 7z actually returns
                output_all = (result.stdout + result.stderr).lower()
                
                if result.returncode == 0:
                    # Check if 7z mentions missing volumes in the output
                    if 'missing volume' in output_all or 'cannot find volume' in output_all:
                        # Try to determine which volumes are missing
                        missing_parts = []
                        # Look for volume patterns in the error
                        for i in range(1, 10):  # Check up to part 009
                            volume_pattern = f'.{i:03d}'
                            if volume_pattern in output_all and i not in found_parts:
                                missing_parts.append(i)
                        
                        return False, found_parts, missing_parts
                    else:
                        # No missing volume error - but for Chinese character files, be more conservative
                        try:
                            str(first_part_file).encode('ascii')
                            # ASCII path - assume complete if no errors
                            return True, found_parts, []
                        except UnicodeEncodeError:
                            # Chinese character path - apply heuristic
                            if len(found_parts) == 2 and found_parts == [1, 2]:
                                # Likely incomplete - missing part 3+
                                return False, found_parts, [3]
                            else:
                                # Other patterns - assume complete
                                return True, found_parts, []
                else:
                    # Error in listing - check for various error patterns that indicate incomplete archive
                    
                    # Common patterns that indicate missing parts or incomplete archive
                    error_patterns = [
                        'missing volume',
                        'cannot find volume', 
                        'unexpected end of archive',
                        'cannot open the file as',
                        'data error',
                        'headers error',
                        'crc failed'
                    ]
                    
                    has_incomplete_errors = any(pattern in output_all for pattern in error_patterns)
                    
                    if has_incomplete_errors:
                        # Archive appears to be incomplete - assume missing next sequential part
                        max_part = max(found_parts) if found_parts else 0
                        missing_parts = [max_part + 1]
                        return False, found_parts, missing_parts
                    else:
                        # Unrecognized error - assume incomplete anyway if exit code is non-zero
                        max_part = max(found_parts) if found_parts else 0
                        missing_parts = [max_part + 1]
                        return False, found_parts, missing_parts
                        
            finally:
                if needs_cleanup and archive_temp.exists():
                    try:
                        archive_temp.unlink()
                    except Exception:
                        pass
                        
        except Exception:
            pass
    
    # Fallback: check for gaps in the sequence
    missing_parts = []
    if found_parts:
        for i in range(1, max(found_parts) + 1):
            if i not in found_parts:
                missing_parts.append(i)
    
    is_complete = len(missing_parts) == 0 and 1 in found_parts
    
    # Special heuristic for Chinese character files: if we have parts [1,2] but no gaps,
    # it's likely incomplete (missing part 3+)
    if is_complete and len(found_parts) == 2 and found_parts == [1, 2]:
        try:
            # Check if path contains non-ASCII characters  
            if first_part_file:
                str(first_part_file).encode('ascii')
        except (UnicodeEncodeError, NameError):
            # Path contains Chinese characters or first_part_file not defined - be conservative
            missing_parts = [3]
            is_complete = False
    
    return is_complete, found_parts, missing_parts


def find_missing_parts_in_other_archives(missing_parts: List[int], base_name: str, all_groups: Dict[str, List[Path]]) -> Dict[int, Path]:
    """Find missing parts that might be inside other archives.
    
    Args:
        missing_parts: List of missing part numbers
        base_name: Base name of the archive
        all_groups: All archive groups to search in
        
    Returns:
        Dictionary mapping part numbers to the archives that contain them
    """
    part_locations = {}
    
    for group_name, group_files in all_groups.items():
        for file_path in group_files:
            # All files are treated as potential archives
            # Quick check if this archive might contain the missing parts
            try:
                is_partial, detected_base = is_partial_archive(file_path)
                if is_partial:
                    # Try to determine which parts this archive contains
                    seven_z = get_7z_executable()
                    archive_temp, needs_cleanup = get_ascii_temp_path(file_path)
                    
                    try:
                        cmd = [str(seven_z), 'l', str(archive_temp)]
                        result = subprocess.run(
                            cmd, 
                            capture_output=True, 
                            text=True, 
                            timeout=30,  # Increased timeout for larger archives
                            encoding='utf-8',
                            errors='replace'
                        )
                        
                        if result.returncode == 0:
                            output = result.stdout.lower()
                            # Check if this archive contains any of our missing parts
                            for part_num in missing_parts:
                                # Try multiple pattern matching approaches due to encoding issues
                                part_pattern = f'{base_name.lower()}.{part_num:03d}'
                                extension_pattern = f'.7z.{part_num:03d}'  # More flexible pattern
                                
                                # Check for exact match first
                                if part_pattern in output:
                                    part_locations[part_num] = file_path
                                # Check for extension pattern (more robust for encoding issues)
                                elif extension_pattern in output:
                                    part_locations[part_num] = file_path
                                    
                    except Exception as e:
                        pass
                    finally:
                        if needs_cleanup and archive_temp.exists():
                            try:
                                archive_temp.unlink()
                            except Exception:
                                pass
            except Exception:
                pass
    
    return part_locations


def extract_multipart_with_7z(group_files: List[Path], output_dir: Path, passwords: List[str]) -> Tuple[bool, str, Optional[str]]:
    """Extract a multi-part archive using 7z with proper handling of all parts.
    
    Args:
        group_files: List of files that make up the multi-part archive
        output_dir: Directory to extract to
        passwords: List of passwords to try
        
    Returns:
        Tuple of (success, output_message, password_used)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create ASCII temp paths for all parts if needed
    temp_files, needs_cleanup = get_ascii_multipart_paths(group_files)
    
    try:
        # Use the first file as the main archive (7z will auto-detect the other parts)
        main_temp_file = temp_files[0]
        
        # Call the regular extract_with_7z with the main file
        # 7z will automatically find and use all parts in the same directory
        return extract_with_7z(main_temp_file, output_dir, passwords)
        
    finally:
        # Clean up temp files if created
        if needs_cleanup:
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                except Exception:
                    pass


def extract_with_7z(archive_path: Path, output_dir: Path, passwords: List[str]) -> Tuple[bool, str, Optional[str]]:
    """Extract an archive using 7z.exe with robust timeout handling and Chinese character support.
    
    Args:
        archive_path: Path to the archive file
        output_dir: Directory to extract to
        passwords: List of passwords to try
        
    Returns:
        Tuple of (success, output_message, password_used)
    """
    seven_z = get_7z_executable()
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Handle Chinese character paths by creating ASCII temp copy if needed
    temp_archive, needs_cleanup = get_ascii_temp_path(archive_path)
    temp_output, output_needs_cleanup = get_ascii_temp_path(output_dir)
    
    try:
        # Use the ASCII-safe paths for 7z.exe
        archive_str = str(temp_archive)
        output_str = str(temp_output)
        
        # Try without password first (use -p to avoid interactive prompts)
        cmd = [str(seven_z), 'x', archive_str, f'-o{output_str}', '-p', '-y']
        
        # Progress callback to show extraction progress
        def show_progress(dots):
            """Display extraction progress to user."""
            from .console_utils import safe_print
            safe_print(f"  ⏳ Extracting {archive_path.name}{dots} | 正在解压 {archive_path.name}{dots}", end='\r')
        
        # Use progress-enabled extraction
        result = run_with_progress(cmd, timeout_seconds=1800, progress_callback=show_progress)  # 30 minute timeout for main extraction
        
        if result['timed_out']:
            return False, f"Extraction timed out after 30 minutes. Archive may be corrupted or very large: {archive_path}", None
        
        # Check if we got password errors (especially for multi-part archives)
        stderr_text = result.get('stderr', '')
        stdout_text = result.get('stdout', '')
        
        # For multi-part archives, if we see password errors but returncode is 1 (not 0), 
        # it means the assembly worked but extraction failed due to password
        if (result['returncode'] == 1 and 
            ("Wrong password" in stderr_text or "Wrong password" in stdout_text) and
            ("Sub items Errors:" in stdout_text or "Archives with Errors:" in stdout_text)):
            # This is a multi-part archive that needs password for the final extraction
            # Continue to password attempts below
            pass
        elif result['returncode'] == 0:
            # If we used temp output directory, copy files back to original location
            if output_needs_cleanup and temp_output != output_dir:
                for item in temp_output.iterdir():
                    dest = output_dir / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)
            # Clear progress line and show completion
            from .console_utils import safe_print
            safe_print()  # New line to clear progress
            return True, "Extracted successfully without password", None
        else:
            # Check if it's a password issue or other errors
            stderr_text = result.get('stderr', '')
            stdout_text = result.get('stdout', '')
            error_msg = f"stdout: {stdout_text}\nstderr: {stderr_text}" if stdout_text or stderr_text else "No error details"
            
            # Check for various error conditions that indicate password issues
            password_indicators = [
                "Wrong password", "password", "Data Error in encrypted file", 
                "ERROR: Data Error in encrypted file"
            ]
            
            error_indicators = [
                "Sub items Errors:", "Archives with Errors:", "ERROR:", "Can't open as archive"
            ]
            
            has_password_error = any(indicator in stderr_text or indicator in stdout_text 
                                   for indicator in password_indicators)
            has_other_errors = any(indicator in stderr_text or indicator in stdout_text 
                                 for indicator in error_indicators)
            
            if has_password_error:
                # Continue to try passwords
                pass
            elif has_other_errors:
                return False, f"Extraction failed with errors: {error_msg}", None
            else:
                return False, f"Extraction failed: {error_msg}", None
        
        # Try with each password
        for password in passwords:
            cmd = [str(seven_z), 'x', archive_str, f'-o{output_str}', f'-p{password}', '-y']
            result = run_with_progress(cmd, timeout_seconds=1800, progress_callback=show_progress)  # 30 minute timeout per password
            
            if result['timed_out']:
                continue  # Try next password
                
            if result['returncode'] == 0:
                # Check for success indicators even with return code 0
                stdout_text = result.get('stdout', '')
                stderr_text = result.get('stderr', '')
                
                # Check for error indicators that might indicate partial failure
                error_indicators = [
                    "Sub items Errors:", "Archives with Errors:", "ERROR:", 
                    "Data Error in encrypted file", "Wrong password"
                ]
                
                has_errors = any(indicator in stderr_text or indicator in stdout_text 
                               for indicator in error_indicators)
                
                if not has_errors:
                    # If we used temp output directory, copy files back to original location
                    if output_needs_cleanup and temp_output != output_dir:
                        for item in temp_output.iterdir():
                            dest = output_dir / item.name
                            if item.is_dir():
                                shutil.copytree(item, dest, dirs_exist_ok=True)
                            else:
                                shutil.copy2(item, dest)
                    # Clear progress line and show completion
                    from .console_utils import safe_print
                    safe_print()  # New line to clear progress
                    return True, f"Extracted successfully with password", password
                else:
                    # Even with return code 0, there were errors - continue to next password
                    continue
        
        # If all passwords failed, return error
        return False, f"Failed to extract: All passwords failed or corrupted archive", None
        
    finally:
        # Clean up temporary files
        if needs_cleanup and temp_archive.exists():
            try:
                temp_archive.unlink()
            except Exception:
                pass
        
        if output_needs_cleanup and temp_output.exists() and temp_output != output_dir:
            try:
                shutil.rmtree(temp_output, ignore_errors=True)
            except Exception:
                pass


def prompt_for_password(archive_name: str) -> Optional[str]:
    """Prompt user for a password.
    
    Args:
        archive_name: Name of the archive file
        
    Returns:
        Password entered by user, or None if cancelled
    """
    print(f"\n🔐 Password required for: {archive_name}")
    print(f"🔐 需要密码: {archive_name}")
    
    try:
        password = input("Enter password (or press Enter to skip): ")
        if password.strip():
            return password.strip()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user | 用户取消")
    
    return None


def find_main_archive_in_group(group_files: List[Path]) -> Optional[Path]:
    """Find the main archive file in a group that should be extracted first.
    
    Args:
        group_files: List of files in the group
        
    Returns:
        Path to the main archive file, or None if not found
    """
    # First, check for archives containing partial files - these should be extracted first
    for file_path in group_files:
        is_partial, base_name = is_partial_archive(file_path)
        if is_partial:
            return file_path
    
    # Look for files with different extensions from others
    extensions = [f.suffix.lower() for f in group_files]
    extension_counts = {}
    
    for ext in extensions:
        extension_counts[ext] = extension_counts.get(ext, 0) + 1
    
    # Find files with unique extensions (likely main archives)
    unique_files = []
    for file_path in group_files:
        if extension_counts[file_path.suffix.lower()] == 1:
            unique_files.append(file_path)
    
    # If we found unique files, since all files are treated as archives, just return the first one
    if unique_files:
        return unique_files[0]
    
    # If no unique files, look for .001 files (first part of split archives)
    first_parts = [f for f in group_files if f.suffix.lower() in ['.001', '.part1', '.z01']]
    if first_parts:
        return first_parts[0]
    
    # Fallback: since all files are treated as archives, just return the first file
    if group_files:
        return sorted(group_files)[0]
    
    return None


def extract_nested_archives(extract_dir: Path, passwords: List[str], max_depth: int = 5) -> Tuple[List[Path], List[str]]:
    """Recursively extract nested archives.
    
    Args:
        extract_dir: Directory containing extracted files
        passwords: List of passwords to try
        max_depth: Maximum recursion depth
        
    Returns:
        Tuple of (final_files, new_passwords_found)
    """
    if max_depth <= 0:
        return list(extract_dir.rglob('*')), []
    
    new_passwords = []
    
    # Find potential archive files in the extraction directory (all files treated as potential archives)
    archive_files = []
    for file_path in extract_dir.rglob('*'):
        if file_path.is_file():
            # All files are treated as potential archives
            if is_archive_file(file_path):
                archive_files.append(file_path)
            # Also try files that might be cloaked archives (avoid common non-archive files)
            elif file_path.suffix.lower() not in ['.txt', '.exe', '.dll', '.sys', '.log', '.ini', '.cfg']:
                # Try to extract any other file as it might be a cloaked archive
                archive_files.append(file_path)
    
    if not archive_files:
        # No more archives to extract
        return [f for f in extract_dir.rglob('*') if f.is_file()], new_passwords
    
    # Extract each potential archive found
    for archive_file in archive_files:
        nested_extract_dir = archive_file.parent / f"{archive_file.stem}_extracted"
        
        success, message, password_used = extract_with_7z(archive_file, nested_extract_dir, passwords)
        
        if success:
            print(f"  📦 Extracted nested archive: {archive_file.name} | 解压嵌套压缩文件: {archive_file.name}")
            
            if password_used and password_used not in passwords:
                new_passwords.append(password_used)
            
            # Remove the archive file after successful extraction
            try:
                archive_file.unlink()
            except Exception:
                pass
            
            # Recursively extract any nested archives
            final_files, more_passwords = extract_nested_archives(nested_extract_dir, passwords + new_passwords, max_depth - 1)
            new_passwords.extend(more_passwords)
        else:
            # If extraction failed, check why it failed
            if is_archive_file(archive_file):
                # Check if it's a "Cannot open the file as archive" error
                if "Cannot open the file as archive" in message:
                    # Keep the file as final content rather than trying to extract it (silently)
                    pass
                else:
                    print(f"  ❌ Failed to extract nested archive: {archive_file.name} - {message} | 解压嵌套压缩文件失败: {archive_file.name} - {message}")
            # Silently skip if extraction fails
    
    return [f for f in extract_dir.rglob('*') if f.is_file()], new_passwords


def create_completed_structure(completed_dir: Path, group_name: str, files: List[Path]) -> Path:
    """Create the completed folder structure and copy files while preserving directory structure.
    
    Args:
        completed_dir: Base completed directory
        group_name: Name of the group (subfolder name)
        files: List of files to copy (should be from the same temp extraction directory)
        
    Returns:
        Path to the created group directory
    """
    group_dir = completed_dir / group_name
    group_dir.mkdir(parents=True, exist_ok=True)
    
    copied_count = 0
    failed_count = 0
    
    # Find the common extraction directory to preserve relative paths
    if not files:
        return group_dir
    
    # Get the common parent directory of all files (the temp extraction directory)
    extraction_root = None
    for file_path in files:
        if file_path.is_file():
            # Find the deepest common parent that contains "temp_extract" or similar
            for parent in file_path.parents:
                if "temp_extract" in parent.name or "extract" in parent.name:
                    extraction_root = parent
                    break
            if extraction_root:
                break
    
    # If we couldn't find the extraction root, use the first file's parent as fallback
    if not extraction_root and files:
        extraction_root = files[0].parent
        # Try to find a better root by looking for a common parent
        for file_path in files[1:]:
            if file_path.is_file():
                # Find common parent
                common_parts = []
                file_parts = file_path.parts
                root_parts = extraction_root.parts
                for i, (a, b) in enumerate(zip(root_parts, file_parts)):
                    if a == b:
                        common_parts.append(a)
                    else:
                        break
                if common_parts:
                    extraction_root = Path(*common_parts)
    
    for file_path in files:
        if file_path.is_file():
            try:
                # Calculate relative path from extraction root
                if extraction_root and extraction_root in file_path.parents:
                    relative_path = file_path.relative_to(extraction_root)
                else:
                    # Fallback to just the filename
                    relative_path = Path(file_path.name)
                
                # Handle temp archive files with better naming
                if file_path.name.startswith('temp_archive_'):
                    # Extract the base name from the group name for better naming
                    base_name = group_name.replace('root_multipart_', '').replace('root_single_', '')
                    # Determine appropriate extension based on file size and content
                    if file_path.stat().st_size > 100 * 1024 * 1024:  # Files larger than 100MB
                        file_name = f"{base_name}_extracted_content"
                    else:
                        file_name = f"{base_name}_content"
                    relative_path = Path(file_name)
                
                # Create destination path preserving directory structure
                dest_path = group_dir / relative_path
                
                # Create parent directories if they don't exist
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(file_path, dest_path)
                copied_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed to copy {file_path.name}: {e} | 复制失败 {file_path.name}: {e}")
                failed_count += 1
    
    # Show total copied files instead of individual file names
    if copied_count > 0:
        print(f"  📄 Total files copied: {copied_count} | 总计复制文件: {copied_count}")
    if failed_count > 0:
        print(f"  ❌ Failed to copy: {failed_count} | 复制失败: {failed_count}")
    
    return group_dir


def clean_up_original_files(files_to_delete: List[Path]) -> Tuple[int, int]:
    """Clean up original files after successful processing.
    
    Args:
        files_to_delete: List of file paths to delete
        
    Returns:
        Tuple of (successfully_deleted, failed_to_delete)
    """
    deleted_count = 0
    failed_count = 0
    
    for file_path in files_to_delete:
        try:
            if file_path.exists():
                file_path.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"  ⚠️  Failed to delete {file_path.name}: {e} | 删除失败 {file_path.name}: {e}")
            failed_count += 1
    
    return deleted_count, failed_count


def save_new_passwords(passwords_file: Path, new_passwords: List[str]) -> None:
    """Save new passwords to the password book.
    
    Args:
        passwords_file: Path to passwords.txt file
        new_passwords: List of new passwords to add
    """
    if not new_passwords:
        return
    
    existing_passwords = set()
    
    # Read existing passwords
    if passwords_file.exists():
        try:
            with open(passwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    password = line.strip()
                    if password:
                        existing_passwords.add(password)
        except Exception as e:
            print(f"  ⚠️  Error reading password file: {e} | 读取密码文件错误: {e}")
    
    # Add new passwords
    passwords_to_add = []
    for password in new_passwords:
        if password and password not in existing_passwords:
            passwords_to_add.append(password)
            existing_passwords.add(password)
    
    if passwords_to_add:
        try:
            with open(passwords_file, 'a', encoding='utf-8') as f:
                for password in passwords_to_add:
                    f.write(f"{password}\n")
            print(f"  🔐 Added {len(passwords_to_add)} new passwords to password book | 向密码本添加了 {len(passwords_to_add)} 个新密码")
        except Exception as e:
            print(f"  ⚠️  Error saving passwords: {e} | 保存密码错误: {e}")


def display_extraction_results(result: ExtractionResult) -> None:
    """Display the final extraction results.
    
    Args:
        result: ExtractionResult object containing all results
    """
    print("\n" + "=" * 60)
    print("🎯 EXTRACTION RESULTS | 解压结果")
    print("=" * 60)
    
    if result.successful_extractions:
        print(f"\n✅ Successfully processed {len(result.successful_extractions)} groups: | 成功处理 {len(result.successful_extractions)} 个组:")
        for group_name, files_count in result.successful_extractions:
            print(f"  📁 {group_name}: {files_count} files extracted | {files_count} 个文件已解压")
    
    if result.failed_extractions:
        print(f"\n❌ Failed to process {len(result.failed_extractions)} groups: | 处理失败 {len(result.failed_extractions)} 个组:")
        for group_name, reason in result.failed_extractions:
            print(f"  📁 {group_name}: {reason}")
    
    if result.new_passwords:
        print(f"\n🔐 Added {len(result.new_passwords)} new passwords to password book | 向密码本添加了 {len(result.new_passwords)} 个新密码")
    
    if result.completed_files:
        print(f"\n📦 Files copied to 'completed' folder: {len(result.completed_files)} | 文件已复制到'完成'文件夹: {len(result.completed_files)}")
    
    total_processed = len(result.successful_extractions) + len(result.failed_extractions)
    success_rate = (len(result.successful_extractions) / total_processed * 100) if total_processed > 0 else 0
    
    print(f"\n📊 Overall success rate: {success_rate:.1f}% ({len(result.successful_extractions)}/{total_processed}) | 总体成功率: {success_rate:.1f}% ({len(result.successful_extractions)}/{total_processed})")
    print("=" * 60)
