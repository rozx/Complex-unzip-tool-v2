import os
import re
import shutil
from send2trash import send2trash

from complex_unzip_tool_v2.modules.const import (
    MULTI_PART_PATTERNS,
    IGNORED_FILES,
    OUTPUT_FOLDER,
)
from complex_unzip_tool_v2.classes.ArchiveGroup import ArchiveGroup
from complex_unzip_tool_v2.modules.utils import get_string_similarity
from complex_unzip_tool_v2.modules.archive_extension_utils import (
    detect_archive_extension,
)
from complex_unzip_tool_v2.modules.cloaked_file_detector import CloakedFileDetector
from complex_unzip_tool_v2.modules.regex import multipart_regex


def get_archive_base_name(file_path: str) -> tuple[str, str]:
    """
    Get the base name and archive extension from a file path,
    handling multi-part archives like .7z.001, .rar.part1, etc.
    获取文件路径的基本名称和档案扩展名，处理多部分档案如.7z.001, .rar.part1等
    Returns (base_name, archive_extension)
    """
    base_name = os.path.basename(file_path)

    # Use the multi-part archive patterns from constants
    for pattern in MULTI_PART_PATTERNS:
        match = re.search(pattern, base_name, re.IGNORECASE)
        if match:
            # Remove the part number/suffix to get the base name
            name_without_part = base_name[: match.start()]
            archive_ext = base_name[match.start() + 1 :].split(".")[
                0
            ]  # Get the archive extension
            return name_without_part, archive_ext

    # Fallback to regular splitext if no multi-part pattern found
    name, ext = os.path.splitext(base_name)
    return name, ext.lstrip(".")


def read_dir(file_paths: list[str]) -> list[str]:
    """Read directory contents 读取目录内容"""
    result = []

    # Use ignored files from constants
    for path in file_paths:
        if os.path.isdir(path):
            # Read files from directory
            for root, dirs, files in os.walk(path):
                # Skip the output folder and any subdirectories within it
                dirs[:] = [d for d in dirs if d != OUTPUT_FOLDER]

                for filename in files:
                    if filename not in IGNORED_FILES:
                        result.append(os.path.join(root, filename))
        else:
            # Check if the file is ignored
            if os.path.basename(path) not in IGNORED_FILES:
                result.append(path)

    # make sure the result is unique
    return list(set(result))


def rename_file(old_path: str, new_path: str, error_callback=None) -> bool:
    """
    Rename a file or directory 重命名文件或目录
    For example, "old_name.txt" to "new_name.txt"
    例如："old_name.txt" 到 "new_name.txt"

    Args:
        old_path: Original path
        new_path: New path
        error_callback: Optional callback function to handle errors

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.rename(old_path, new_path)
        return True
    except (OSError, IOError, PermissionError) as e:
        error_msg = f"Error renaming file 重命名文件错误 {old_path} to {new_path}: {e}"
        if error_callback:
            error_callback(error_msg)
        return False


def safe_remove(
    file_path: str, use_recycle_bin: bool = True, error_callback=None
) -> bool:
    """
    Safely remove a file, optionally moving it to recycle bin instead of permanent deletion.
    安全删除文件，可选择移动到回收站而不是永久删除。

    Args:
        file_path (str): Path to the file to remove
        use_recycle_bin (bool): If True, move to recycle bin; if False, permanently delete
        error_callback: Optional callback function to handle errors

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            if use_recycle_bin:
                send2trash(file_path)
                return True
            else:
                os.remove(file_path)
                return True
        return False
    except (OSError, IOError, PermissionError, FileNotFoundError) as e:
        error_msg = f"Error removing file 删除文件错误 {file_path}: {e}"
        if error_callback:
            error_callback(error_msg)
        return False


def _should_group_files(
    group_name1: str, group_name2: str, file_path1: str, file_path2: str
) -> bool:
    """
    Improved logic to determine if two files should be grouped together.
    This addresses the issue of unrelated files being grouped due to high similarity scores.
    改进的逻辑来确定两个文件是否应该分组在一起。
    这解决了不相关文件因高相似度分数而被分组的问题。
    """
    if not file_path2:  # Empty comparison file
        return False

    # Extract file information
    base1, ext1 = get_archive_base_name(file_path1)
    base2, ext2 = get_archive_base_name(file_path2)

    # First check: Are they multipart archives of the same base file?
    if _are_multipart_related(file_path1, file_path2):
        return True

    # Second check: Exact base name match (for files like 1.rar, 1.r00, 1.r01)
    if base1 == base2 and ext1 == ext2:
        return True

    # Third check: Only allow grouping if similarity is very high AND they share exact base name
    similarity = get_string_similarity(group_name1, group_name2)
    if similarity >= 0.95:
        # Extract just the filename parts without directory
        name1_only = group_name1.split("-")[-1] if "-" in group_name1 else group_name1
        name2_only = group_name2.split("-")[-1] if "-" in group_name2 else group_name2

        # Only group if the file base names are identical
        return name1_only == name2_only

    # For all other cases, don't group
    return False


def _are_multipart_related(file_path1: str, file_path2: str) -> bool:
    """Check if two files are related multipart archives."""
    if not file_path2:  # Empty comparison file
        return False

    # Extract base names without part numbers
    base1, ext1 = get_archive_base_name(file_path1)
    base2, ext2 = get_archive_base_name(file_path2)

    # Check if both are multipart archives with identical base names
    file1_is_multipart = re.search(multipart_regex, file_path1)
    file2_is_multipart = re.search(multipart_regex, file_path2)

    if file1_is_multipart and file2_is_multipart:
        # Base names must be exactly the same for multipart grouping
        return base1 == base2 and ext1 == ext2

    return False


def _have_matching_multipart_pattern(file_path1: str, file_path2: str) -> bool:
    """Check if two files follow the same multipart pattern (for short names)."""
    if not file_path2:  # Empty comparison file
        return False

    # Check if both are multipart and have the same base pattern

    # Extract base names and extensions
    base1, ext1 = get_archive_base_name(file_path1)
    base2, ext2 = get_archive_base_name(file_path2)

    # For short names, require exact base name match and same extension type
    if len(base1) <= 3 and len(base2) <= 3:
        return base1 == base2 and ext1 == ext2

    return False


def _is_likely_archive(file_path: str) -> bool:
    """
    Pre-filter to determine if a file is likely to be a valid archive.
    This helps skip obviously non-archive files early to avoid unnecessary processing.
    用于判断文件是否可能是有效档案的预过滤器。
    """
    try:
        filename = os.path.basename(file_path)

        # Check common archive extensions first (fast path)
        common_archive_exts = {
            ".7z",
            ".zip",
            ".rar",
            ".tar",
            ".gz",
            ".bz2",
            ".xz",
            ".cab",
            ".iso",
            ".dmg",
            ".pkg",
            ".deb",
            ".rpm",
        }
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext in common_archive_exts:
            return True

        # Check for multipart archive patterns
        for pattern in MULTI_PART_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return True

        # For files without clear extensions or suspicious files, use signature detection
        # But only for files that might be SFX or cloaked archives
        if not file_ext or file_ext in {".exe", ".bin", ".dat", ".tmp"}:
            # Use the enhanced signature detection
            detected_type = detect_archive_extension(file_path)
            return detected_type is not None

        # For other file types, assume they're not archives
        return False

    except Exception:
        # If there's any error, err on the side of caution and include the file
        return True


def create_groups_by_name(
    file_paths: list[str], warning_callback=None
) -> list[ArchiveGroup]:
    """Create Archive Groups by name 按名称创建档案组"""
    groups: list[ArchiveGroup] = []
    skipped_files_count = 0

    for path in file_paths:
        # Pre-filter: Skip files that are clearly not archives
        if not _is_likely_archive(path):
            skipped_files_count += 1
            continue

        # get base name and directory name using the new function
        name = get_archive_base_name(path)
        dir_name = os.path.dirname(path).split(os.path.sep)[-1]
        group_name = f"{dir_name}-{name}"

        # Check if file belongs to an existing group using improved logic
        found_group = False
        for group in groups[:]:  # Iterate through a copy of the list
            if _should_group_files(
                group_name, group.name, path, group.files[0] if group.files else ""
            ):
                try:
                    group.add_file(path)
                    found_group = True
                    break
                except ValueError:
                    # Archive signature validation failed - remove the group silently
                    groups.remove(group)
                    skipped_files_count += 1
                    break

        if not found_group:
            new_group = ArchiveGroup(group_name)
            try:
                new_group.add_file(path)
                groups.append(new_group)
            except ValueError:
                # Archive signature validation failed - count it silently
                skipped_files_count += 1

    # Show summary of skipped files if any
    if skipped_files_count > 0 and warning_callback:
        warning_callback(
            f"⚠ Skipped {skipped_files_count} file(s) with invalid archive signatures"
        )

    # and finally sort it by name
    for group in groups:
        group.files.sort()

    return groups


def uncloak_file_extension_for_groups(
    groups: list[ArchiveGroup], rules_file_path: str = None, warning_callback=None
) -> None:
    """
    Uncloak file extensions for groups using rule-based detection.
    使用基于规则的检测为组揭示文件扩展名。

    Args:
        groups: List of ArchiveGroup objects to process
        rules_file_path: Path to JSON rules file (optional, uses default if not provided)
        warning_callback: Optional callback function to handle warnings
    """
    # Use default rules file if not provided
    if rules_file_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(os.path.dirname(current_dir), "config")
        rules_file_path = os.path.join(config_dir, "cloaked_file_rules.json")

    # Initialize the detector
    detector = CloakedFileDetector(rules_file_path)

    for group in groups:
        for i, file in enumerate(group.files):
            original_file = file
            new_path = detector.uncloak_file(file)

            if new_path != original_file:
                if os.path.exists(new_path):
                    group.files[i] = new_path
                    if group.mainArchiveFile == original_file:
                        group.mainArchiveFile = new_path
                else:
                    warning_msg = (
                        f"⚠ Failed to rename file '{original_file}' to '{new_path}'. "
                        "File does not exist. Group not updated."
                    )
                    if warning_callback:
                        warning_callback(warning_msg)


def uncloak_file_extensions(
    file_paths: list[str], rules_file_path: str = None
) -> list[str]:
    """
    Uncloak file extensions for a list of file paths using rule-based detection.
    使用基于规则的检测为文件路径列表解除文件扩展名隐藏。

    Args:
        file_paths: List of file paths to process
        rules_file_path: Path to JSON rules file (optional, uses default if not provided)

    Returns:
        The updated file paths list with proper extensions.
    """
    # Use default rules file if not provided
    if rules_file_path is None:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(os.path.dirname(current_dir), "config")
        rules_file_path = os.path.join(config_dir, "cloaked_file_rules.json")

    # Initialize the detector
    detector = CloakedFileDetector(rules_file_path)

    # Process all files
    updated_paths = detector.uncloak_files(file_paths)

    return updated_paths


def add_file_to_groups(file: str, groups: list[ArchiveGroup]) -> ArchiveGroup | None:
    """
    Check if a file belongs to a specific multi-part archive group, then add it to the group.
    检查文件是否属于特定的多部分档案组，然后将其添加到组中
    """

    file_basename = os.path.basename(file)

    for group in groups:
        if group.isMultiPart:
            main_archive_basename = os.path.basename(group.mainArchiveFile)

            if get_string_similarity(file_basename, main_archive_basename) >= 0.8:
                # move file to group's main archive's location
                new_path = os.path.join(
                    os.path.dirname(group.mainArchiveFile), file_basename
                )
                shutil.move(file, new_path)
                group.add_file(new_path)
                return group

    return None


def move_files_preserving_structure(
    file_paths: list[str],
    source_root: str,
    destination_root: str,
    verbose: bool = False,
    progress_callback: callable = None,
    success_callback: callable = None,
    error_callback: callable = None,
) -> list[str]:
    """
    Move files from source to destination while preserving directory structure.
    在保持目录结构的同时将文件从源移动到目标

    Args:
        file_paths: List of file paths to move 要移动的文件路径列表
        source_root: Root directory to calculate relative paths from 计算相对路径的根目录
        destination_root: Root directory to move files to 移动文件到的根目录
        verbose: Print verbose output 打印详细输出
        progress_callback: Optional callback function for progress updates 可选的进度更新回调函数
        success_callback: Optional callback function for success messages 可选的成功消息回调函数
        error_callback: Optional callback function for error messages 可选的错误消息回调函数

    Returns:
        List of relative paths that were successfully moved 成功移动的相对路径列表
    """
    moved_files = []

    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                # Calculate relative path from source root to preserve structure
                relative_path = os.path.relpath(file_path, source_root)
                destination = os.path.join(destination_root, relative_path)

                # Create destination directory if it doesn't exist
                destination_dir = os.path.dirname(destination)
                os.makedirs(destination_dir, exist_ok=True)

                # Handle duplicate filenames while preserving directory structure
                counter = 1
                original_destination = destination
                while os.path.exists(destination):
                    name, ext = os.path.splitext(original_destination)
                    destination = f"{name}_{counter}{ext}"
                    counter += 1

                shutil.move(file_path, destination)
                moved_files.append(relative_path)

                # Call progress callback if provided
                if progress_callback:
                    progress_callback()
                if verbose and success_callback:
                    success_callback(f"📁 Moved 已移动: {relative_path}")

            except (OSError, IOError, PermissionError) as e:
                error_msg = f"Error moving 移动错误 {file_path}: {e}"
                if error_callback:
                    error_callback(error_msg)

    return moved_files
