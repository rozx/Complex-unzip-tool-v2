import os
import re
import shutil
import struct
import typer

from click import group

from .rich_utils import print_error, print_success
from .const import MULTI_PART_PATTERNS, IGNORED_FILES
from ..classes.ArchiveGroup import ArchiveGroup
from .utils import get_string_similarity
from .archive_extension_utils import detect_archive_extension


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
            name_without_part = base_name[:match.start()]
            archive_ext = base_name[match.start()+1:].split('.')[0]  # Get the archive extension
            return name_without_part, archive_ext
    
    # Fallback to regular splitext if no multi-part pattern found
    name, ext = os.path.splitext(base_name)
    return name, ext.lstrip('.')

def read_dir(file_paths: list[str]) -> list[str]:
    """Read directory contents 读取目录内容"""
    result = []

    # Use ignored files from constants
    for path in file_paths:
        if os.path.isdir(path):
            # Read files from directory
            for root, dirs, files in os.walk(path):
                for filename in files:
                    if filename not in IGNORED_FILES:
                        result.append(os.path.join(root, filename))
        else:
            # Check if the file is ignored
            if os.path.basename(path) not in IGNORED_FILES:
                result.append(path)

    # make sure the result is unique
    return list(set(result))

def rename_file(old_path: str, new_path: str) -> None:
    """
    Rename a file or directory 重命名文件或目录
    For example, "old_name.txt" to "new_name.txt"
    例如："old_name.txt" 到 "new_name.txt"
    """
    try:
        os.rename(old_path, new_path)
    except Exception as e:
        print_error(f"Error renaming file 重命名文件错误 {old_path} to {new_path}: {e}")

def create_groups_by_name(file_paths: list[str]) -> list[ArchiveGroup]:
    """Create Archive Groups by name 按名称创建档案组"""
    groups: list[ArchiveGroup] = []
    for path in file_paths:
        # get base name and directory name using the new function
        name, ext = get_archive_base_name(path)
        dir_name = os.path.dirname(path).split(os.path.sep)[-1]
        group_name = f"{dir_name}-{name}"

        # Check basename's similarity to a group, it is greater than 0.8 then add it to the group, if not then create a existing group
        found_group = False
        for group in groups:
            # if group's name is similar to the file's base name and it is in the same directory
            if get_string_similarity(group_name, group.name) >= 0.8:
                group.add_file(path)
                found_group = True
                break
                

        if not found_group:
            new_group = ArchiveGroup(group_name)
            new_group.add_file(path)
            groups.append(new_group)

    # and finally sort it by name
    for group in groups:
        group.files.sort()

    return groups

def uncloak_file_extension_for_groups(groups: list[ArchiveGroup]) -> None:
    """Uncloak file extensions for groups 为组揭示文件扩展名"""
    
    for group in groups:
        for i, file in enumerate(group.files):
            true_ext = detect_archive_extension(file)
            if true_ext:
                # rename the file to have the true extension
                name, current_ext = get_archive_base_name(file)
                new_name = f"{name}.{true_ext}"
                new_path = os.path.join(os.path.dirname(file), new_name)

                if new_path != file:
                    rename_file(file, new_path)
                    group.files[i] = new_path
                    if group.mainArchiveFile == file:
                        group.mainArchiveFile = new_path

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
                new_path = os.path.join(os.path.dirname(group.mainArchiveFile), file_basename)
                shutil.move(file, new_path)
                group.add_file(new_path)
                return group

    return None


def move_files_preserving_structure(
    file_paths: list[str], 
    source_root: str, 
    destination_root: str,
    verbose: bool = False,
    progress_callback: callable = None
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
                if verbose: print_success(f"📁 Moved 已移动: {relative_path}")
                
            except Exception as e:
                print_error(f"Error moving 移动错误 {file_path}: {e}")
    
    return moved_files
