import subprocess
import os
import sys
import shutil
import tempfile
from typing import List, Dict, Optional, Union, Tuple
import re
from complex_unzip_tool_v2.modules.rich_utils import (
    print_nested_extraction_header,
    print_extraction_process_header,
    print_extracting_archive,
    print_password_failed,
    print_password_success,
    print_extraction_summary,
    print_warning,
    print_error,
    print_error_summary,
    print_empty_line,
    print_info,
    print_success,
    print_password_failed_options,
    print_invalid_choice,
    print_continuing_extraction,
    print_password_incorrect,
    print_invalid_yn_choice,
    clear_console,
)
from complex_unzip_tool_v2.modules.file_utils import safe_remove
from complex_unzip_tool_v2.modules.utils import sanitize_path, sanitize_filename
from complex_unzip_tool_v2.modules.const import PATH_ERROR_KEYWORDS

from complex_unzip_tool_v2.classes.ArchiveTypes import (
    ArchiveError,
    ArchiveNotFoundError,
    SevenZipNotFoundError,
    ArchivePasswordError,
    ArchiveCorruptedError,
    ArchiveUnsupportedError,
    ArchiveParsingError,
    ArchiveFileInfo,
)

# ------------------------------
# 7-Zip helpers
# ------------------------------


def _resolve_seven_zip_path(seven_zip_path: Optional[str]) -> str:
    """Return a valid path to 7z.exe, raising if it doesn't exist."""
    path = seven_zip_path or _get_default_7z_path()
    if not os.path.exists(path):
        raise SevenZipNotFoundError(f"7z executable not found at: {path}")
    return path


def _ensure_archive_exists(archive_path: str) -> None:
    """Raise if the given archive path does not exist."""
    if not os.path.exists(archive_path):
        raise ArchiveNotFoundError(f"Archive not found: {archive_path}")


def _build_password_arg(password: Optional[str]) -> str:
    """Always return a valid -p argument; empty string means no password."""
    return f"-p{password or ''}"


def _build_7z_extract_cmd(
    seven_zip_path: str,
    password: Optional[str],
    output_path: str,
    archive_path: str,
    overwrite: bool = True,
    specific_files: Optional[List[str]] = None,
) -> List[str]:
    """Build a standardized 7z extract command with consistent argument order."""
    cmd = [seven_zip_path, "x", _build_password_arg(password), f"-o{output_path}"]

    if overwrite:
        cmd.append("-y")
    else:
        cmd.append("-aos")

    cmd.append(archive_path)

    if specific_files:
        cmd.extend(specific_files)

    return cmd


def _run_7z_cmd(cmd: List[str]) -> Tuple[str, str, int]:
    """Run a 7z command returning decoded stdout, stderr and return code."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=False,
        check=False,
    )
    stdout, stderr = _decode_subprocess_output(result.stdout, result.stderr)
    return stdout, stderr, result.returncode


def _raise_for_7z_error(returncode: int, stderr: str, archive_path: str) -> None:
    """Map 7z return/err output to specific exceptions or no-op if success."""
    if returncode == 0:
        return
    err = (stderr or "").lower()
    # Treat "not an archive" style errors as unsupported/non-archive, not corruption
    if (
        "can not open file as archive" in err
        or "cannot open file as archive" in err
        or "is not archive" in err
    ):
        raise ArchiveUnsupportedError(
            f"Not a supported archive type (likely not an archive): {archive_path}"
        )
    if "wrong password" in err or "cannot open encrypted archive" in err:
        raise ArchivePasswordError(
            f"Incorrect password or password required for: {archive_path}"
        )
    if "data error" in err or "crc failed" in err:
        raise ArchiveCorruptedError(f"Archive appears to be corrupted: {archive_path}")
    if "unsupported method" in err or "unknown method" in err:
        raise ArchiveUnsupportedError(f"Archive format not supported: {archive_path}")
    if "cannot open file" in err:
        raise ArchiveNotFoundError(f"Cannot open archive file: {archive_path}")
    if "disk full" in err or "not enough space" in err:
        raise ArchiveError(f"Insufficient disk space for extraction: {archive_path}")
    # Generic fallback
    raise ArchiveError(f"7z command failed ({returncode}): {stderr.strip()}")


def is_valid_archive(
    file_path: str,
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
) -> bool:
    """Check quickly if a file is a valid archive that 7z can open.

    Returns True for valid (including password-protected) archives.
    Returns False for non-archive/unreadable files.
    """
    try:
        content = readArchiveContentWith7z(
            archive_path=file_path,
            password=password,
            seven_zip_path=seven_zip_path,
        )
        return bool(content)
    except ArchivePasswordError:
        return True
    except (
        ArchiveError,
        ArchiveCorruptedError,
        ArchiveUnsupportedError,
        ArchiveParsingError,
    ):
        return False
    except Exception:
        return False


def _get_default_7z_path() -> str:
    """
    Get the default path to 7z.exe executable.
    Works for both development and PyInstaller standalone builds.
    """
    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle
        bundle_dir = sys._MEIPASS
        seven_zip_path = os.path.join(bundle_dir, "7z", "7z.exe")
    else:
        # Running in development mode
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(current_dir)
        seven_zip_path = os.path.join(project_root, "7z", "7z.exe")

    return seven_zip_path


def _decode_subprocess_output(
    stdout_bytes: bytes, stderr_bytes: bytes
) -> Tuple[str, str]:
    """
    Safely decode subprocess output with multiple encoding fallbacks.

    Args:
        stdout_bytes (bytes): Raw stdout bytes from subprocess
        stderr_bytes (bytes): Raw stderr bytes from subprocess

    Returns:
        tuple[str, str]: Decoded stdout and stderr strings
    """
    stdout = ""
    stderr = ""

    # Try UTF-8 first
    try:
        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        return stdout, stderr
    except (UnicodeDecodeError, AttributeError):
        pass

    # Fallback to gbk
    try:
        stdout = stdout_bytes.decode("gbk", errors="replace")
        stderr = stderr_bytes.decode("gbk", errors="replace")
        return stdout, stderr
    except Exception:
        pass

    # Fallback to gb2312
    try:
        stdout = stdout_bytes.decode("gb2312", errors="replace")
        stderr = stderr_bytes.decode("gb2312", errors="replace")
        return stdout, stderr
    except Exception:
        pass

    # Fallback to cp1252 (Windows-1252)
    try:
        stdout = stdout_bytes.decode("cp1252", errors="replace")
        stderr = stderr_bytes.decode("cp1252", errors="replace")
        return stdout, stderr
    except Exception:
        pass

    # Final fallback - convert bytes to string representation
    try:
        stdout = str(stdout_bytes, errors="replace")
        stderr = str(stderr_bytes, errors="replace")
    except Exception:
        stdout = str(stdout_bytes)
        stderr = str(stderr_bytes)

    return stdout, stderr


def readArchiveContentWith7z(
    archive_path: str,
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
) -> List[ArchiveFileInfo]:
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

    # Resolve paths and validate inputs
    seven_zip_path = _resolve_seven_zip_path(seven_zip_path)
    _ensure_archive_exists(archive_path)

    # Build command
    cmd = [seven_zip_path, "l", "-slt", _build_password_arg(password), archive_path]

    try:
        stdout, stderr, code = _run_7z_cmd(cmd)
        _raise_for_7z_error(code, stderr, archive_path)

        try:
            files_info = _parse7zListOutput(stdout)
            return files_info
        except Exception as e:
            raise ArchiveParsingError(f"Failed to parse 7z output: {str(e)}") from e
    except FileNotFoundError as exc:
        # In case running the binary failed despite path existence checks
        raise SevenZipNotFoundError(
            f"7z executable not found at: {seven_zip_path}"
        ) from exc


def _parse7zListOutput(output: str) -> List[ArchiveFileInfo]:
    """
    Parse 7z list command output into structured data.

    Args:
        output (str): Raw output from 7z list command

    Returns:
        List[Dict]: Parsed file information
    """
    files = []
    current_file = {}

    lines = output.split("\n")
    in_file_section = False
    dash_count = 0

    for i, line in enumerate(lines):
        line = line.strip()

        # The file listing section in `7z l -slt` often starts after a dashed line
        # Accept the first dashed line to maintain compatibility with tests and varied 7z outputs
        if line.startswith("----------"):
            dash_count += 1
            if dash_count >= 1:
                in_file_section = True
            continue

        # Skip lines before file section
        if not in_file_section:
            continue

        # Skip empty lines
        if not line:
            continue

        # Check if this line starts a new file entry (starts with "Path = ")
        if line.startswith("Path = "):
            # Save previous file if it exists
            if current_file and current_file.get("Path"):
                files.append(_formatFileInfo(current_file))

            # Start new file entry
            current_file = {}
            parts = line.split(" = ", 1)
            if len(parts) == 2:
                current_file["Path"] = parts[1]

        # Parse other key-value pairs
        elif " = " in line and current_file:
            parts = line.split(" = ", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                current_file[key] = value

    # Add final file if exists
    if current_file and current_file.get("Path"):
        files.append(_formatFileInfo(current_file))

    return files


def _formatFileInfo(file_data: Dict[str, str]) -> ArchiveFileInfo:
    """
    Format raw file data into standardized structure.

    Args:
        file_data (Dict): Raw file data from 7z output

    Returns:
        Dict: Formatted file information
    """
    try:
        size = int(file_data.get("Size", "0"))
    except (ValueError, TypeError):
        size = 0

    try:
        packed_size = int(file_data.get("Packed Size", "0"))
    except (ValueError, TypeError):
        packed_size = 0

    return {
        "name": file_data.get("Path", ""),
        "size": size,
        "packed_size": packed_size,
        "type": file_data.get("Folder", "File")
        .replace("-", "File")
        .replace("+", "Folder"),
        "modified": file_data.get("Modified", ""),
        "attributes": file_data.get("Attributes", ""),
        "crc": file_data.get("CRC", ""),
        "method": file_data.get("Method", ""),
    }


def extractArchiveWith7z(
    archive_path: str,
    output_path: str,
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
    overwrite: bool = True,
    specific_files: Optional[List[str]] = None,
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

    # Resolve paths and validate inputs
    seven_zip_path = _resolve_seven_zip_path(seven_zip_path)
    _ensure_archive_exists(archive_path)

    # Create output directory if it doesn't exist
    try:
        os.makedirs(output_path, exist_ok=True)
    except OSError as e:
        raise ArchiveError(f"Failed to create output directory: {e}") from e

    # Build command using centralized helper
    cmd = _build_7z_extract_cmd(
        seven_zip_path=seven_zip_path,
        password=password,
        output_path=output_path,
        archive_path=archive_path,
        overwrite=overwrite,
        specific_files=specific_files,
    )

    try:
        stdout, stderr, code = _run_7z_cmd(cmd)
        try:
            _raise_for_7z_error(code, stderr, archive_path)
        except ArchivePasswordError:
            # Re-raise password errors immediately without path checking
            raise
        except ArchiveError as e:
            # Detect path-related issues and fallback to sanitized path extraction
            msg = str(e).lower()
            if any(k in msg for k in PATH_ERROR_KEYWORDS):
                print_warning(
                    "Path-related extraction error detected, trying alternative extraction method...",
                    2,
                )
                return _extractWithSanitizedPaths(
                    archive_path,
                    output_path,
                    password,
                    seven_zip_path,
                    overwrite,
                    specific_files,
                )
            raise
        return True
    except FileNotFoundError:
        raise SevenZipNotFoundError(f"7z executable not found at: {seven_zip_path}")


def _extractWithSanitizedPaths(
    archive_path: str,
    output_path: str,
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
    overwrite: bool = True,
    specific_files: Optional[List[str]] = None,
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
        temp_cmd = _build_7z_extract_cmd(
            seven_zip_path=seven_zip_path,
            password=password,
            output_path=temp_dir,
            archive_path=archive_path,
            overwrite=overwrite,
            specific_files=specific_files,
        )

        # Execute extraction to temp directory
        stdout, stderr, code = _run_7z_cmd(temp_cmd)
        if code != 0:
            _raise_for_7z_error(code, stderr, archive_path)

        # Now move files from temp directory to final destination with sanitized names
        try:
            _moveAndSanitizeFiles(temp_dir, output_path)
            print_success("Successfully extracted with sanitized file paths", 2)
            return True
        except Exception as e:
            raise ArchiveError(f"Failed to move extracted files: {e}")

    except Exception as e:
        # Re-raise specific archive exceptions, wrap others
        if isinstance(
            e,
            (
                ArchivePasswordError,
                ArchiveCorruptedError,
                ArchiveUnsupportedError,
                ArchiveNotFoundError,
                ArchiveError,
            ),
        ):
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
                print_info(
                    f"Directory conflict resolved: {os.path.basename(base_target_subdir)} → {os.path.basename(target_subdir)}",
                    3,
                )

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
                    print_info(
                        f"Moved file: {file} → {os.path.basename(target_file)}", 3
                    )

            except OSError:
                # If copy fails, try a more robust approach
                try:
                    with open(source_file, "rb") as src, open(target_file, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    os.remove(source_file)
                    print_info(
                        f"Moved file (fallback): {file} → {os.path.basename(target_file)}",
                        3,
                    )
                except OSError as e2:
                    print_warning(f"Failed to move file {file}: {e2}", 2)
                    # Don't raise exception, just continue with other files


def extractSpecificFilesWith7z(
    archive_path: str,
    output_path: str,
    file_list: List[str],
    password: Optional[str] = "",
    seven_zip_path: Optional[str] = None,
    overwrite: bool = True,
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
        extractArchiveWith7z(
            archive_path=archive_path,
            output_path=output_path,
            password=password,
            seven_zip_path=seven_zip_path,
            overwrite=overwrite,
            specific_files=file_list,
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
    loading_indicator=None,
    active_progress_bars: Optional[List] = None,
    use_recycle_bin: bool = True,
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
        "success": True,
        "extracted_archives": [],
        "final_files": [],
        "errors": [],
        "password_used": {},
        "user_provided_passwords": [],
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

    # Reuse generic helper for archive validation

    def _promptUserForPassword(
        archive_name: str, active_progress_bars: Optional[List] = None
    ) -> Optional[str]:
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
        if loading_indicator and hasattr(loading_indicator, "stop"):
            loading_indicator.stop()

        # Stop all active progress bars to prevent interference with user input
        stopped_progress_bars = []
        if active_progress_bars:
            for progress_bar in active_progress_bars:
                if (
                    hasattr(progress_bar, "stop")
                    and hasattr(progress_bar, "progress")
                    and progress_bar.progress
                ):
                    progress_bar.stop()
                    stopped_progress_bars.append(progress_bar)

        # Clear any remaining display artifacts and ensure clean terminal state
        clear_console()

        print_password_failed_options(archive_name)

        # Use a simple input loop to ensure compatibility
        while True:
            try:
                choice_input = input(
                    "Choose an option 选择一个选项 (1/2/3) [default: 2]: "
                ).strip()
                if choice_input == "":
                    choice = 2
                    break
                else:
                    choice = int(choice_input)
                    if choice in [1, 2, 3]:
                        break
                    else:
                        print_invalid_choice()
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
            print_continuing_extraction()

        # Note: We don't restart the progress bars here as they will interfere again
        # The extraction process will continue normally without progress display during user input

        # Restart loading indicator if it exists
        if loading_indicator and hasattr(loading_indicator, "start"):
            loading_indicator.start()

        return result

    def _tryExtractWithPasswords(
        archive_file: str, extract_to: str, active_progress_bars: Optional[List] = None
    ) -> tuple[bool, str]:
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
            print_info(
                f"🔐 Trying {len(passwords_to_try)} passwords 尝试 {len(passwords_to_try)} 个密码...",
                1,
            )

        for pwd in passwords_to_try:
            try:
                success = extractArchiveWith7z(
                    archive_path=archive_file,
                    output_path=extract_to,
                    password=pwd,
                    seven_zip_path=seven_zip_path,
                    overwrite=True,
                )

                if success:
                    print_password_success(pwd)
                    return True, pwd

            except ArchivePasswordError:
                password_required = (
                    True  # Mark that this is a valid archive that needs password
                )
                continue

            except (
                ArchiveCorruptedError,
                ArchiveUnsupportedError,
                ArchiveNotFoundError,
            ) as e:
                # These are archive-related errors that should stop password attempts immediately
                print_error(f"Archive error 档案错误: {str(e)}", 1)
                print_info(
                    "Skipping remaining passwords for this archive 跳过此档案的剩余密码",
                    2,
                )
                return False, ""

            except ArchiveError as e:
                # Generic archive errors - check if it's a path-related error that should stop
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in PATH_ERROR_KEYWORDS):
                    print_error(f"File system error 文件系统错误: {str(e)}", 1)
                    print_info(
                        "Skipping remaining passwords for this archive 跳过此档案的剩余密码",
                        2,
                    )
                    return False, ""
                else:
                    # Other archive errors might be password-related, continue with next password
                    continue

            except Exception as e:
                # Unexpected errors - these could be system issues, stop trying passwords
                print_error(f"Unexpected error 意外错误: {str(e)}", 1)
                print_info(
                    "Skipping remaining passwords for this archive 跳过此档案的剩余密码",
                    2,
                )
                return False, ""

        # Only prompt user for passwords if we confirmed this is a valid archive that requires password
        if interactive and not skip_all_prompts and password_required:
            if passwords_to_try:
                print_warning(
                    f"None of the {len(passwords_to_try)} provided passwords worked 提供的 {len(passwords_to_try)} 个密码都无效",
                    1,
                )

            while True:
                user_password = _promptUserForPassword(
                    archive_name, active_progress_bars
                )

                if user_password == "SKIP_ALL":
                    print_info(
                        "Skipping all future password prompts 跳过所有未来的密码提示", 2
                    )
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
                        overwrite=True,
                    )

                    if success:
                        print_success(
                            "Extraction successful with user password 使用用户密码提取成功!",
                            1,
                        )
                        # Add the successful password to the list for future use
                        passwords_to_try.append(user_password)
                        return True, user_password

                except ArchivePasswordError:
                    # Don't count password failures as errors - use warning instead
                    print_password_failed(user_password)

                    # Stop loading indicator for user input
                    if loading_indicator and hasattr(loading_indicator, "stop"):
                        loading_indicator.stop()

                    # Stop all active progress bars to prevent interference with user input
                    if active_progress_bars:
                        for progress_bar in active_progress_bars:
                            if (
                                hasattr(progress_bar, "stop")
                                and hasattr(progress_bar, "progress")
                                and progress_bar.progress
                            ):
                                progress_bar.stop()

                    # Use simple input instead of typer.confirm for better compatibility
                    print_password_incorrect()

                    while True:
                        try:
                            continue_input = (
                                input(
                                    "Try another password 尝试另一个密码? (Y/n) [default: Y]: "
                                )
                                .strip()
                                .lower()
                            )
                            if continue_input == "" or continue_input in [
                                "y",
                                "yes",
                                "是",
                            ]:
                                continue_prompt = True
                                break
                            elif continue_input in ["n", "no", "否"]:
                                continue_prompt = False
                                break
                            else:
                                print_invalid_yn_choice()
                        except KeyboardInterrupt:
                            continue_prompt = False
                            break

                    # Restart loading indicator
                    if loading_indicator and hasattr(loading_indicator, "start"):
                        loading_indicator.start()

                    if not continue_prompt:
                        return False, ""
                    continue

                except (
                    ArchiveCorruptedError,
                    ArchiveUnsupportedError,
                    ArchiveNotFoundError,
                ) as e:
                    # These are archive-related errors that should stop user password attempts
                    print_error(f"Archive error 档案错误: {str(e)}", 1)
                    print_info(
                        "Cannot continue with this archive 无法继续处理此档案", 2
                    )
                    return False, ""

                except ArchiveError as e:
                    # Generic archive errors - check if it's a path-related error that should stop
                    error_msg = str(e).lower()
                    if any(keyword in error_msg for keyword in PATH_ERROR_KEYWORDS):
                        print_error(f"File system error 文件系统错误: {str(e)}", 1)
                        print_info(
                            "Cannot continue with this archive 无法继续处理此档案", 2
                        )
                        return False, ""
                    else:
                        # Other archive errors might be password-related, continue
                        print_error(
                            f"Extraction failed with user password 使用用户密码提取失败: {str(e)}",
                            1,
                        )
                        print_info(
                            "Cannot continue with this archive 无法继续处理此档案", 2
                        )
                        return False, ""

                except Exception as e:
                    print_error(f"Unexpected error 意外错误: {str(e)}", 1)
                    print_info(
                        "Cannot continue with this archive 无法继续处理此档案", 2
                    )
                    return False, ""
        else:
            # If no password was required but extraction still failed, show appropriate message
            if password_required:
                print_warning(
                    f"Archive requires password but user chose to skip 档案需要密码但用户选择跳过: {archive_name}",
                    1,
                )
            else:
                print_warning(
                    f"Failed to extract archive 提取档案失败: {archive_name}", 1
                )

        return False, ""

    def _extractRecursively(
        current_archive: str, current_output: str, depth: int
    ) -> None:
        """Recursively extract archives while preserving folder structure 递归提取档案，同时保持文件夹结构."""

        if depth > max_depth:
            error_msg = f"Maximum recursion depth ({max_depth}) reached for 达到最大递归深度: {current_archive}"
            result["errors"].append(error_msg)
            print_warning(error_msg, 1)
            return

        try:
            # If the file no longer exists (e.g., already processed and cleaned up in a deeper level),
            # skip silently for nested levels. Only the top-level (depth 0) missing input is a hard error.
            if not os.path.exists(current_archive):
                if depth == 0:
                    error_msg = f"Archive not found 档案未找到: {current_archive}"
                    result["errors"].append(error_msg)
                    print_warning(error_msg, 1)
                else:
                    print_info(
                        f"Skipping missing nested archive 跳过缺失的嵌套档案: {os.path.basename(current_archive)}",
                        2,
                    )
                return

            # First, verify that this is actually a valid archive before attempting extraction
            if not is_valid_archive(
                current_archive, password=password, seven_zip_path=seven_zip_path
            ):
                # For nested levels, do not treat non-archives as errors; they can appear
                # due to concurrent processing/cleanup or false positives from signature scans.
                if depth == 0:
                    error_msg = f"File is not a valid archive 文件不是有效档案: {current_archive}"
                    result["errors"].append(error_msg)
                    print_warning(error_msg, 1)
                else:
                    print_info(
                        f"Skipping non-archive at depth {depth} 跳过非档案: {os.path.basename(current_archive)}",
                        2,
                    )
                return

            # Extract directly to the current output directory to preserve structure
            print_extracting_archive(os.path.basename(current_archive), depth)

            extract_success, used_password = _tryExtractWithPasswords(
                current_archive, current_output, active_progress_bars
            )

            if extract_success:
                result["extracted_archives"].append(current_archive)
                result["password_used"][current_archive] = used_password
                result["user_provided_passwords"] = list(set(user_provided_passwords))

                # Find all files in the extracted directory (walk from current_output)
                extracted_files = []

                for root, dirs, files in os.walk(current_output):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Skip the original archive files that we already processed
                        if (
                            file_path != current_archive
                            and file_path not in result["extracted_archives"]
                        ):
                            extracted_files.append(file_path)

                # Find newly extracted archives to process recursively
                nested_archives = []
                regular_files = []

                print_info(
                    f"Testing {len(extracted_files)} extracted files for nested archives",
                    2,
                )
                print_info(
                    f"正在测试 {len(extracted_files)} 个提取的文件是否为嵌套档案...", 3
                )

                for file_path in extracted_files:
                    file_name = os.path.basename(file_path)

                    # Skip files that were already processed
                    if file_path in result["extracted_archives"]:
                        continue

                    # Skip multipart continuation files (.7z.002, .r01, .z02, .part2.rar, etc.)
                    # Only primary parts should be considered for further processing:
                    #   - 7z: .7z.001 is primary
                    #   - TAR.*: .tar.gz/.bz2/.xz.001 is primary
                    #   - RAR: .rar or .part1.rar is primary (NOT .r00)
                    #   - ZIP spanned: .zip is primary (treat .z01+ as continuation)
                    fname = file_name.lower()
                    try:
                        skip_continuation = False
                        # 7z.00N parts: only .001 is primary
                        m = re.search(r"\.7z\.(\d{1,3})$", fname)
                        if m:
                            if int(m.group(1)) != 1:
                                skip_continuation = True

                        # tar.(gz|bz2|xz).00N parts: only .001 is primary
                        if not skip_continuation:
                            m = re.search(r"\.tar\.(gz|bz2|xz)\.(\d{1,3})$", fname)
                            if m and int(m.group(2)) != 1:
                                skip_continuation = True

                        # RAR volumes: .r00, .r01, ... are continuations; primary is .rar or .part1.rar
                        if not skip_continuation:
                            if re.search(r"\.r\d{2}$", fname):
                                skip_continuation = True

                        # ZIP spanned: .z01, .z02, ... are continuations; primary is .zip
                        if not skip_continuation:
                            if re.search(r"\.z\d{2}$", fname):
                                skip_continuation = True

                        # RAR part notation: only part1.rar is primary, others are continuation
                        if not skip_continuation:
                            m = re.search(r"\.part(\d+)\.rar$", fname)
                            if m and int(m.group(1)) != 1:
                                skip_continuation = True

                        if skip_continuation:
                            print_info(
                                f"Skipping multipart continuation file 跳过多部分续档: {file_name}",
                                3,
                            )
                            continue
                    except re.error:
                        # If regex somehow fails, fall back to normal flow
                        pass

                    if is_valid_archive(
                        file_path, password=password, seven_zip_path=seven_zip_path
                    ):
                        print_info(
                            f"📦 Found nested archive 发现嵌套档案: {file_name}", 3
                        )
                        nested_archives.append(file_path)
                    else:
                        regular_files.append(file_path)

                # Add regular files to final files list
                result["final_files"].extend(regular_files)

                if regular_files:
                    print_info(
                        f"Found {len(regular_files)} regular files 发现 {len(regular_files)} 个常规文件",
                        2,
                    )

                # Delete the processed archive file if cleanup is enabled and it's not the original
                if cleanup_archives and current_archive != archive_path:
                    try:
                        success = safe_remove(
                            current_archive,
                            use_recycle_bin=use_recycle_bin,
                            error_callback=print_error,
                        )
                        if success:
                            if use_recycle_bin:
                                print_success(
                                    f"Moved nested archive to recycle bin 已将嵌套档案移至回收站: {os.path.basename(current_archive)}",
                                    2,
                                )
                            else:
                                print_success(
                                    f"Cleaned up archive 已清理档案: {os.path.basename(current_archive)}",
                                    2,
                                )
                    except OSError as e:
                        error_msg = f"Failed to delete 删除失败 {current_archive}: {e}"
                        result["errors"].append(error_msg)
                        print_warning(error_msg, 2)

                # If we found nested archives, extract them recursively in their current location
                if nested_archives:
                    print_info(f"Found {len(nested_archives)} nested archive(s)", 2)
                    print_info(
                        f"在深度 {depth} 发现 {len(nested_archives)} 个嵌套档案", 3
                    )
                    for nested_archive in nested_archives:
                        # Skip if already processed in a deeper recursion step
                        if nested_archive in result["extracted_archives"]:
                            print_info(
                                f"Already processed nested archive 已处理嵌套档案: {os.path.basename(nested_archive)}",
                                3,
                            )
                            continue
                        # Skip if the file no longer exists (likely cleaned up already)
                        if not os.path.exists(nested_archive):
                            print_info(
                                f"Nested archive missing after processing 嵌套档案缺失: {os.path.basename(nested_archive)}",
                                3,
                            )
                            continue
                        # Extract nested archive into its own subfolder to avoid collisions
                        parent_dir = os.path.dirname(nested_archive)
                        base_name = os.path.basename(nested_archive)

                        # Derive folder name by stripping known archive suffixes
                        def _derive_folder_name(filename: str) -> str:

                            name = filename
                            # Iteratively strip extensions like .zip, .7z, .rar, .tar.gz, .001, .z01, .r00, .part1
                            while True:
                                name_no_ext, ext = os.path.splitext(name)
                                ext_low = ext.lower()
                                if not ext_low:
                                    break
                                # Numeric parts like .001
                                if len(ext_low) == 4 and ext_low[1:].isdigit():
                                    name = name_no_ext
                                    continue
                                # multipart like .z01/.r00/.a00/.c00
                                if re.fullmatch(r"\.[zrac][0-9]{2}", ext_low):
                                    name = name_no_ext
                                    continue
                                # .partN
                                if (
                                    ext_low.startswith(".part")
                                    and ext_low[5:].isdigit()
                                ):
                                    name = name_no_ext
                                    continue
                                # common archive extensions
                                if ext_low in (
                                    ".zip",
                                    ".7z",
                                    ".rar",
                                    ".tar",
                                    ".gz",
                                    ".bz2",
                                    ".xz",
                                    ".iso",
                                    ".img",
                                    ".bin",
                                    ".cab",
                                    ".ace",
                                    ".arj",
                                    ".lzh",
                                    ".lha",
                                ):
                                    name = name_no_ext
                                    continue
                                break
                            return name

                        folder_name = _derive_folder_name(base_name)
                        folder_name = sanitize_filename(folder_name) or "archive"
                        nested_output_dir_base = os.path.join(parent_dir, folder_name)

                        # Ensure uniqueness if folder already exists
                        nested_output_dir = nested_output_dir_base
                        counter = 2
                        while os.path.exists(nested_output_dir):
                            nested_output_dir = f"{nested_output_dir_base}_{counter}"
                            counter += 1

                        # Create the directory before extraction
                        try:
                            os.makedirs(nested_output_dir, exist_ok=True)
                        except OSError:
                            # Fallback to parent dir if creation fails
                            nested_output_dir = parent_dir

                        _extractRecursively(
                            nested_archive, nested_output_dir, depth + 1
                        )
                else:
                    print_success(f"No more nested archives found at depth {depth}", 2)
                    print_info(f"在深度 {depth} 未发现更多嵌套档案", 3)

            else:
                # Extraction failed - but this could be due to password issues, which are not "errors"
                # Only add to errors if it's a system/technical error, not password-related
                print_warning(
                    f"Could not extract 无法提取: {current_archive} (tried all available passwords 尝试了所有可用密码)",
                    2,
                )
                # Note: This is not added to errors list as it's likely a password issue, not a system error

        except Exception as e:
            error_msg = f"Error extracting 提取错误 {current_archive}: {e}"
            result["errors"].append(error_msg)
            result["success"] = False
            print_error(error_msg, 2)

    # Start the recursive extraction
    try:
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)

        print_nested_extraction_header(
            archive_path, output_path, len(passwords_to_try), max_depth
        )
        print_extraction_process_header()

        # Begin recursive extraction with the initial archive
        _extractRecursively(archive_path, output_path, 0)

        # Clean up empty directories
        print_empty_line()
        print_info("🧹 Cleaning up empty directories 清理空目录...")
        _cleanupEmptyDirectories(output_path)

        # Update final success status
        # Consider the run unsuccessful if no files/archives were actually extracted
        # even when there are no system errors (e.g., all password attempts failed).
        had_outputs = bool(result["final_files"]) or bool(result["extracted_archives"])
        result["success"] = (
            result["success"] and len(result["errors"]) == 0 and had_outputs
        )

        # Show final summary
        status = "SUCCESS" if result["success"] else "PARTIAL/FAILED"
        print_extraction_summary(
            status,
            len(result["extracted_archives"]),
            len(result["final_files"]),
            len(result["errors"]),
        )

        if result["errors"]:
            print_error_summary(result["errors"])

    except Exception as e:
        error_msg = f"Fatal error during extraction 提取期间发生致命错误: {e}"
        result["errors"].append(error_msg)
        result["success"] = False
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
    except (OSError, FileNotFoundError, PermissionError):
        # Ignore cleanup errors
        pass
