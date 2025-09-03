import re
import subprocess
import json
import os
import typer
from typing import List, Dict, Optional, Union
from .richUtils import (
    print_nested_extraction_header, print_extraction_process_header,
    print_extracting_archive, print_password_attempt, print_password_failed,
    print_password_success, print_extraction_summary
)

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
            files_info = _parse7zListOutput(result.stdout)
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
    
    # Create output directory if it doesn't exist
    try:
        os.makedirs(output_path, exist_ok=True)
    except OSError as e:
        raise ArchiveError(f"Failed to create output directory: {e}")
    
    # Build command
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
        # Execute 7z command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        if result.returncode != 0:
            raise ArchiveError(f"7z extraction failed ({result.returncode}): {result.stderr.strip()}")

        return True
        
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
        elif "disk full" in stderr_lower or "not enough space" in stderr_lower:
            raise ArchiveError(f"Insufficient disk space for extraction: {archive_path}")
        else:
            # Generic archive error for other cases
            raise ArchiveError(f"7z extraction error ({e.returncode}): {e.stderr.strip()}")
    
    except FileNotFoundError:
        raise SevenZipNotFoundError(f"7z executable not found at: {seven_zip_path}")


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

def extractNestedArchives(
    archive_path: str,
    output_path: str,
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
    max_depth: int = 10,
    cleanup_archives: bool = True,
    password_list: Optional[List[str]] = None,
    interactive: bool = True,
    loading_indicator = None
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
            # If password error, try without password for listing
            try:
                content = readArchiveContentWith7z(
                    archive_path=file_path,
                    password="",
                    seven_zip_path=seven_zip_path
                )
                return content is not None and len(content) > 0
            except Exception:
                return False
                
        except (ArchiveError, ArchiveCorruptedError, ArchiveUnsupportedError, ArchiveParsingError):
            # Cannot read as archive
            return False
        except Exception:
            # Any other error, treat as non-archive
            return False
    
    def _promptUserForPassword(archive_name: str) -> Optional[str]:
        """
        Prompt user for password when all automatic attempts fail.
        提示用户输入密码，当所有自动尝试失败时
        
        Returns:
            str: User-provided password or None if user chooses to skip
        """
        if not interactive:
            return None
        
        # Stop loading indicator if it exists
        if loading_indicator and hasattr(loading_indicator, 'stop'):
            loading_indicator.stop()
            
        typer.echo("")
        typer.echo(f"⚠️  All provided passwords failed for archive 所有提供的密码对档案都失败了: {typer.style(archive_name, fg=typer.colors.YELLOW)}")
        typer.echo("Options 选项:")
        typer.echo("  1. Enter a password 输入密码")
        typer.echo("  2. Skip this archive 跳过此档案")
        typer.echo("  3. Skip all remaining password-protected archives 跳过所有剩余的密码保护档案")
        
        choice = typer.prompt("Choose an option 选择一个选项 (1/2/3)", type=int, default=2)
        
        result = None
        if choice == 1:
            password = typer.prompt("Enter password 输入密码")
            user_provided_passwords.append(password)
            result = password
        elif choice == 3:
            # User wants to skip all future password prompts
            result = "SKIP_ALL"
        else:
            # Skip this archive
            result = None
        
        # Restart loading indicator if it exists
        if loading_indicator and hasattr(loading_indicator, 'start'):
            loading_indicator.start()
            
        return result
    
    def _tryExtractWithPasswords(archive_file: str, extract_to: str) -> tuple[bool, str]:
        """
        Try to extract an archive with different passwords.
        
        Returns:
            tuple: (success: bool, password_used: str)
        """
        archive_name = os.path.basename(archive_file)
        skip_all_prompts = False
        
        # Try all provided passwords first
        for pwd in passwords_to_try:
            try:
                print_password_attempt(pwd)
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
                print_password_failed(pwd)
                continue
            except Exception as e:
                typer.echo(f"  ❌ Extraction failed with password 使用密码提取失败 {'(empty)' if pwd == '' else pwd}: {typer.style(str(e), fg=typer.colors.RED)}")
                continue
        
        # If all provided passwords failed, prompt user for new passwords
        if interactive and not skip_all_prompts:
            while True:
                user_password = _promptUserForPassword(archive_name)
                
                if user_password == "SKIP_ALL":
                    typer.echo(f"  ⏭️  Skipping all future password prompts 跳过所有未来的密码提示")
                    return False, ""
                elif user_password is None:
                    typer.echo(f"  ⏭️  Skipping archive 跳过档案: {typer.style(archive_name, fg=typer.colors.YELLOW)}")
                    return False, ""
                
                # Try the user-provided password
                try:
                    typer.echo(f"  🔓 Trying user-provided password 尝试用户提供的密码...")
                    success = extractArchiveWith7z(
                        archive_path=archive_file,
                        output_path=extract_to,
                        password=user_password,
                        seven_zip_path=seven_zip_path,
                        overwrite=True
                    )
                    
                    if success:
                        typer.echo(f"  ✅ Extraction successful with user password 使用用户密码提取成功!")
                        # Add the successful password to the list for future use
                        passwords_to_try.append(user_password)
                        return True, user_password
                        
                except ArchivePasswordError:
                    typer.echo(f"  ❌ User password is incorrect 用户密码不正确")
                    
                    # Stop loading indicator for user input
                    if loading_indicator and hasattr(loading_indicator, 'stop'):
                        loading_indicator.stop()
                    
                    continue_prompt = typer.confirm("Try another password 尝试另一个密码?", default=True)
                    
                    # Restart loading indicator
                    if loading_indicator and hasattr(loading_indicator, 'start'):
                        loading_indicator.start()
                    
                    if not continue_prompt:
                        return False, ""
                    continue
                except Exception as e:
                    typer.echo(f"  ❌ Extraction failed 提取失败: {typer.style(str(e), fg=typer.colors.RED)}")
                    return False, ""
        
        return False, ""
    
    def _extractRecursively(current_archive: str, current_output: str, depth: int) -> None:
        """Recursively extract archives while preserving folder structure 递归提取档案，同时保持文件夹结构."""
        
        if depth > max_depth:
            error_msg = f"Maximum recursion depth ({max_depth}) reached for 达到最大递归深度: {current_archive}"
            result['errors'].append(error_msg)
            typer.echo(f"  ⚠️  {typer.style(error_msg, fg=typer.colors.YELLOW)}")
            return
        
        try:
            # Extract directly to the current output directory to preserve structure
            print_extracting_archive(os.path.basename(current_archive), depth)
            
            extract_success, used_password = _tryExtractWithPasswords(current_archive, current_output)
            
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
                
                typer.echo(f"      🔍 Testing {len(extracted_files)} extracted files for nested archives")
                typer.echo(f"         正在测试 {len(extracted_files)} 个提取的文件是否为嵌套档案...")
                
                for file_path in extracted_files:
                    file_name = os.path.basename(file_path)
                    
                    # Skip files that were already processed
                    if file_path in result['extracted_archives']:
                        continue
                    
                    if _tryOpenAsArchive(file_path):
                        typer.echo(f"         📦 Found nested archive 发现嵌套档案: {file_name}")
                        nested_archives.append(file_path)
                    else:
                        regular_files.append(file_path)
                
                # Add regular files to final files list
                result['final_files'].extend(regular_files)
                
                if regular_files:
                    typer.echo(f"      📄 Found {len(regular_files)} regular files 发现 {len(regular_files)} 个常规文件")
                
                # Delete the processed archive file if cleanup is enabled and it's not the original
                if cleanup_archives and current_archive != archive_path:
                    try:
                        os.remove(current_archive)
                        typer.echo(f"      🗑️  Cleaned up archive 已清理档案: {os.path.basename(current_archive)}")
                    except OSError as e:
                        error_msg = f"Failed to delete 删除失败 {current_archive}: {e}"
                        result['errors'].append(error_msg)
                        typer.echo(f"      ⚠️  {typer.style(error_msg, fg=typer.colors.YELLOW)}")
                
                # If we found nested archives, extract them recursively in their current location
                if nested_archives:
                    typer.echo(f"      🔄 Found {typer.style(str(len(nested_archives)), fg=typer.colors.GREEN)} nested archive(s)")
                    typer.echo(f"         在深度 {depth} 发现 {len(nested_archives)} 个嵌套档案")
                    for nested_archive in nested_archives:
                        # Extract nested archive in the same directory to preserve structure
                        nested_output_dir = os.path.dirname(nested_archive)
                        _extractRecursively(nested_archive, nested_output_dir, depth + 1)
                else:
                    typer.echo(f"      ✅ No more nested archives found at depth {depth}")
                    typer.echo(f"         在深度 {depth} 未发现更多嵌套档案")
            
            else:
                error_msg = f"Failed to extract 提取失败: {current_archive} (tried all passwords 尝试了所有密码)"
                result['errors'].append(error_msg)
                result['success'] = False
                typer.echo(f"      ❌ {typer.style(error_msg, fg=typer.colors.RED)}")
                
        except Exception as e:
            error_msg = f"Error extracting 提取错误 {current_archive}: {e}"
            result['errors'].append(error_msg)
            result['success'] = False
            typer.echo(f"      ❌ {typer.style(error_msg, fg=typer.colors.RED)}")
    
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
        typer.echo()
        typer.echo("🧹 Cleaning up empty directories 清理空目录...")
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
            typer.echo()
            typer.echo("❌ Errors encountered 遇到的错误:")
            typer.echo("   ╭" + "─" * 74 + "╮")
            for i, error in enumerate(result['errors']):
                typer.echo(f"   │ {i+1}. {error[:70]:<70} │")
            typer.echo("   ╰" + "─" * 74 + "╯")
        
    except Exception as e:
        error_msg = f"Fatal error during extraction 提取期间发生致命错误: {e}"
        result['errors'].append(error_msg)
        result['success'] = False
        typer.echo(f"💥 {typer.style(error_msg, fg=typer.colors.RED, bold=True)}")
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