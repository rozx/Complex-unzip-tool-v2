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

def _should_group_files(group_name1: str, group_name2: str, file_path1: str, file_path2: str) -> bool:
    """
    Improved logic to determine if two files should be grouped together.
    This addresses the issue of unrelated files being grouped due to high similarity scores.
    改进的逻辑来确定两个文件是否应该分组在一起。
    这解决了不相关文件因高相似度分数而被分组的问题。
    """
    if not file_path2:  # Empty comparison file
        return False
    
    # Extract file information
    file1_name = os.path.basename(file_path1)
    file2_name = os.path.basename(file_path2)
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
        name1_only = group_name1.split('-')[-1] if '-' in group_name1 else group_name1
        name2_only = group_name2.split('-')[-1] if '-' in group_name2 else group_name2
        
        # Only group if the file base names are identical
        return name1_only == name2_only
    
    # For all other cases, don't group
    return False


def _are_multipart_related(file_path1: str, file_path2: str) -> bool:
    """Check if two files are related multipart archives."""
    if not file_path2:  # Empty comparison file
        return False
    
    from .regex import multipart_regex
    
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
    
    from .regex import multipart_regex
    
    # Check if both are multipart and have the same base pattern
    file1_name = os.path.basename(file_path1)
    file2_name = os.path.basename(file_path2)
    
    # Extract base names and extensions
    base1, ext1 = get_archive_base_name(file_path1)
    base2, ext2 = get_archive_base_name(file_path2)
    
    # For short names, require exact base name match and same extension type
    if len(base1) <= 3 and len(base2) <= 3:
        return base1 == base2 and ext1 == ext2
    
    return False


def create_groups_by_name(file_paths: list[str]) -> list[ArchiveGroup]:
    """Create Archive Groups by name 按名称创建档案组"""
    groups: list[ArchiveGroup] = []
    for path in file_paths:
        # get base name and directory name using the new function
        name, ext = get_archive_base_name(path)
        dir_name = os.path.dirname(path).split(os.path.sep)[-1]
        group_name = f"{dir_name}-{name}"

        # Check if file belongs to an existing group using improved logic
        found_group = False
        for group in groups:
            if _should_group_files(group_name, group.name, path, group.files[0] if group.files else ""):
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
            original_file = file
            new_path = _uncloak_single_file(file)
            
            if new_path != original_file:
                rename_file(original_file, new_path)
                group.files[i] = new_path
                if group.mainArchiveFile == original_file:
                    group.mainArchiveFile = new_path

def _uncloak_single_file(file_path: str) -> str:
    """
    Uncloak a single file's extension, handling various cloaking patterns.
    Handles cases like "3729457aaa001" -> "3729457aaa.7z.001"
    """
    filename = os.path.basename(file_path)
    dirname = os.path.dirname(file_path)
    
    # Special handling for extensionless files that might be archives with part numbers
    if '.' not in filename:
        # Look for 1-3 digits at the end that could be part numbers
        part_patterns = [
            (r'(\d{3})$', 3),  # 3 digits like 001
            (r'(\d{2})$', 2),  # 2 digits like 01  
            (r'(\d{1})$', 1),  # 1 digit like 1
        ]
        
        for pattern, digit_count in part_patterns:
            part_match = re.search(pattern, filename)
            if part_match:
                part_number = part_match.group(1)
                base_name = filename[:-digit_count]  # Everything except the digits
                
                # Skip if base name is too short (likely not a real filename)
                if len(base_name) < 2:
                    continue
                
                # Try to detect archive type by file signature
                if os.path.exists(file_path):
                    from .archive_extension_utils import detect_archive_info
                    info = detect_archive_info(file_path)
                    if info and info['type']:
                        archive_type = info['type']
                        
                        # Format part number based on original length
                        if digit_count == 3:
                            formatted_part = f"{int(part_number):03d}"
                        elif digit_count == 2:
                            formatted_part = f"{int(part_number):02d}"
                        else:
                            formatted_part = part_number
                        
                        # Reconstruct filename with proper format
                        new_filename = f"{base_name}.{archive_type}.{formatted_part}"
                        return os.path.join(dirname, new_filename)
                    else:
                        # If current file doesn't have signature (likely a split part),
                        # try to find the first part and check its signature
                        current_part_num = int(part_number)
                        if current_part_num > 1:
                            # Look for the first part (001, 01, or 1)
                            if digit_count == 3:
                                first_part_extensionless = f"{base_name}001"
                                first_part_formatted = f"{base_name}.7z.001"  # Try common format
                            elif digit_count == 2:
                                first_part_extensionless = f"{base_name}01"
                                first_part_formatted = f"{base_name}.7z.01"
                            else:
                                first_part_extensionless = f"{base_name}1"
                                first_part_formatted = f"{base_name}.7z.1"
                            
                            # Try both extensionless and formatted versions
                            first_part_candidates = [
                                os.path.join(dirname, first_part_extensionless),
                                os.path.join(dirname, first_part_formatted)
                            ]
                            
                            archive_type = None
                            for first_part_path in first_part_candidates:
                                if os.path.exists(first_part_path):
                                    first_info = detect_archive_info(first_part_path)
                                    if first_info and first_info['type']:
                                        archive_type = first_info['type']
                                        break
                            
                            if archive_type:
                                # Format part number based on original length
                                if digit_count == 3:
                                    formatted_part = f"{int(part_number):03d}"
                                elif digit_count == 2:
                                    formatted_part = f"{int(part_number):02d}"
                                else:
                                    formatted_part = part_number
                                
                                # Reconstruct filename with proper format
                                new_filename = f"{base_name}.{archive_type}.{formatted_part}"
                                return os.path.join(dirname, new_filename)
                
                # Only try the first matching pattern
                break
        
        # For extensionless files that don't match part patterns, 
        # or have too short base names, try existing detection
        true_ext = detect_archive_extension(file_path)
        if true_ext:
            new_filename = f"{filename}.{true_ext}"
            return os.path.join(dirname, new_filename)
    else:
        # Fall back to existing detection method for files with extensions
        true_ext = detect_archive_extension(file_path)
        if true_ext:
            name, current_ext = get_archive_base_name(file_path)
            potential_new_name = f"{name}.{true_ext}"
            potential_new_path = os.path.join(dirname, potential_new_name)
            
            # If this would result in a different filename, use it
            if potential_new_path != file_path:
                return potential_new_path
    
    # If no changes needed, return original path
    return file_path

def uncloak_file_extensions(file_paths: list[str]) -> list[str]:
    """
    Uncloak file extensions for a list of file paths before creating groups.
    为文件路径列表揭示文件扩展名，在创建组之前进行。
    Returns the updated file paths list with proper extensions.
    """
    updated_paths = []
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            new_path = _uncloak_single_file(file_path)
            
            if new_path != file_path:
                # Rename the actual file
                rename_file(file_path, new_path)
                updated_paths.append(new_path)
            else:
                updated_paths.append(file_path)
        else:
            # If file doesn't exist, keep original path
            updated_paths.append(file_path)
    
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
