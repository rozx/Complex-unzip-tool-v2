"""Main module for the Complex Unzip Tool v2."""

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import List, Union, Dict, Set
import difflib
import re


def validate_paths(paths: List[str]) -> List[Path]:
    """Validate that all provided paths exist.
    
    Args:
        paths: List of file or directory path strings
        
    Returns:
        List of validated Path objects
        
    Raises:
        FileNotFoundError: If any path doesn't exist
    """
    validated_paths = []
    for path_str in paths:
        path = Path(path_str).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist | 路径不存在: {path}")
        validated_paths.append(path)
    return validated_paths


def collect_all_files(paths: List[Path], recursive: bool = False) -> List[Path]:
    """Collect all files from the given paths.
    
    Args:
        paths: List of validated Path objects (files or directories)
        recursive: Whether to recursively search directories
        
    Returns:
        List of all files found
    """
    all_files = []
    
    for path in paths:
        if path.is_file():
            all_files.append(path)
        elif path.is_dir():
            if recursive:
                # Include files in the root directory AND subdirectories
                all_files.extend(path.rglob('*'))
            else:
                # Only files in the immediate directory
                all_files.extend(path.glob('*'))
    
    # Filter to only include files (not directories)
    return [f for f in all_files if f.is_file()]


def group_files_by_subfolder(files: List[Path]) -> Dict[Path, List[Path]]:
    """Group files by their immediate parent directory.
    
    Args:
        files: List of file paths
        
    Returns:
        Dictionary mapping parent directories to lists of files
    """
    groups = defaultdict(list)
    
    for file_path in files:
        parent_dir = file_path.parent
        groups[parent_dir].append(file_path)
    
    return dict(groups)


def normalize_filename(filename: str) -> str:
    """Normalize filename for similarity comparison.
    
    Args:
        filename: Original filename
        
    Returns:
        Normalized filename (lowercase, no extension, alphanumeric only)
    """
    # Remove extension
    name_without_ext = Path(filename).stem
    # Convert to lowercase and keep only alphanumeric characters
    normalized = re.sub(r'[^a-zA-Z0-9]', '', name_without_ext.lower())
    return normalized


def calculate_similarity(name1: str, name2: str) -> float:
    """Calculate similarity ratio between two filenames.
    
    Args:
        name1, name2: Filenames to compare
        
    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    norm1 = normalize_filename(name1)
    norm2 = normalize_filename(name2)
    return difflib.SequenceMatcher(None, norm1, norm2).ratio()


def extract_base_name(filename: str) -> str:
    """Extract the base name for precise grouping.
    
    Args:
        filename: Original filename
        
    Returns:
        Base name for grouping (e.g., '12.7z' from '12.7z.001')
    """
    name = Path(filename).name
    
    # Handle multi-part archives like .7z.001, .7z.002, .rar.001, etc.
    if re.search(r'\.(7z|rar|zip)\.\d+$', name, re.IGNORECASE):
        # Remove the .001, .002, etc. part
        base = re.sub(r'\.\d+$', '', name)
        return base.lower()
    
    # Handle other multi-part patterns like .001, .002 (without format extension)
    if re.search(r'\.\d{3}$', name):
        # Remove the .001, .002, etc. part
        base = re.sub(r'\.\d{3}$', '', name)
        return base.lower()
    
    # For regular files, return the full name without extension
    return Path(name).stem.lower()


def group_files_by_priority(files: List[Path]) -> Dict[str, List[Path]]:
    """Group files with subfolder priority - all files in a subfolder are considered one archive.
    
    Priority order:
    1. Subfolder grouping (highest priority - all files in one subfolder = one group)
    2. Multi-part archive detection (for files in the same directory)
    
    Args:
        files: List of file paths
        
    Returns:
        Dictionary mapping group names to lists of files
    """
    groups = {}
    group_counter = 0
    
    # Group by parent directory first
    subfolder_groups = group_files_by_subfolder(files)
    
    for parent_dir, dir_files in subfolder_groups.items():
        folder_name = parent_dir.name if parent_dir.name else "root"
        
        # If all files are in the same subfolder, they are treated as one archive group
        if len(dir_files) > 1:
            # Multiple files in same directory - group them all together as one archive
            group_name = f"{folder_name}_archive"
            groups[group_name] = sorted(dir_files, key=lambda x: x.name)
            group_counter += 1
        else:
            # Single file - check if it's part of a multi-part archive across directories
            single_file = dir_files[0]
            base_name = extract_base_name(single_file.name)
            
            # Look for other parts in other directories
            similar_files = [single_file]
            found_match = False
            
            for other_dir, other_files in subfolder_groups.items():
                if other_dir != parent_dir and len(other_files) == 1:  # Only check single-file directories
                    other_file = other_files[0]
                    other_base = extract_base_name(other_file.name)
                    
                    # Check if they're parts of the same multi-part archive
                    if (base_name == other_base and 
                        (re.search(r'\.(7z|rar|zip)\.\d+$', single_file.name, re.IGNORECASE) or
                         re.search(r'\.\d{3}$', single_file.name))):
                        similar_files.append(other_file)
                        found_match = True
            
            if found_match and len(similar_files) > 1:
                # Multiple parts found across directories - create one group
                group_name = f"{base_name}_multipart"
                groups[group_name] = sorted(similar_files, key=lambda x: x.name)
                
                # Mark these files as processed by removing them from subfolder_groups
                for sim_file in similar_files:
                    for dir_path, dir_file_list in subfolder_groups.items():
                        if sim_file in dir_file_list and len(dir_file_list) == 1:
                            dir_file_list.clear()  # Clear the list to mark as processed
                            break
            else:
                # Single file that doesn't match others - create individual group
                group_name = f"{folder_name}_{normalize_filename(single_file.stem)}"
                groups[group_name] = [single_file]
    
    return groups


def group_files_by_similarity(files: List[Path], threshold: float = 0.9) -> Dict[str, List[Path]]:
    """Group files by precise filename similarity.
    
    Args:
        files: List of file paths
        threshold: Similarity threshold (0.9 for more precise grouping)
        
    Returns:
        Dictionary mapping group names to lists of similar files
    """
    groups = {}
    used_files = set()
    
    # First, group by exact base name matches (for multi-part archives)
    base_name_groups = defaultdict(list)
    
    for file_path in files:
        if file_path in used_files:
            continue
            
        base_name = extract_base_name(file_path.name)
        base_name_groups[base_name].append(file_path)
    
    group_counter = 0
    
    # Process base name groups
    for base_name, group_files in base_name_groups.items():
        if len(group_files) > 1:
            # Multiple files with same base name - create a group
            group_name = f"group_{group_counter}_{base_name}"
            groups[group_name] = sorted(group_files, key=lambda x: x.name)
            used_files.update(group_files)
            group_counter += 1
    
    # Now handle remaining single files with high similarity threshold
    remaining_files = [f for f in files if f not in used_files]
    
    for i, file1 in enumerate(remaining_files):
        if file1 in used_files:
            continue
            
        # Start a new group
        current_group = [file1]
        used_files.add(file1)
        
        # Look for very similar files (higher threshold)
        for j, file2 in enumerate(remaining_files[i+1:], i+1):
            if file2 in used_files:
                continue
                
            similarity = calculate_similarity(file1.name, file2.name)
            if similarity >= threshold:
                current_group.append(file2)
                used_files.add(file2)
        
        # Only create groups with more than one file for similarity matches
        if len(current_group) > 1:
            group_name = f"group_{group_counter}_{normalize_filename(file1.name)}"
            groups[group_name] = sorted(current_group, key=lambda x: x.name)
            group_counter += 1
        else:
            # Single file - create individual group
            group_name = f"single_{normalize_filename(file1.name)}"
            groups[group_name] = current_group
    
    return groups


def display_file_groups(subfolder_groups: Dict[Path, List[Path]], 
                       priority_groups: Dict[str, List[Path]], 
                       verbose: bool = False) -> None:
    """Display the grouped files in a simplified single-layer format.
    
    Args:
        subfolder_groups: Files grouped by subfolder (for reference)
        priority_groups: Files grouped by priority (main display)
        verbose: Whether to show detailed information
    """
    print("\n" + "=" * 60)
    print("📁 GROUPING BY SUBFOLDER | 按子文件夹分组")
    print("=" * 60)
    
    for folder, files in subfolder_groups.items():
        print(f"\n📂 {folder} ({len(files)} files | {len(files)} 个文件)")
        if verbose:
            for file_path in sorted(files):
                print(f"   📄 {file_path.name}")
        else:
            # Show first few files and count if there are more
            displayed_files = sorted(files)[:3]
            for file_path in displayed_files:
                print(f"   📄 {file_path.name}")
            if len(files) > 3:
                print(f"   ... and {len(files) - 3} more files | 还有 {len(files) - 3} 个文件")
    
    print("\n" + "=" * 60)
    print("🎯 ARCHIVE GROUPS | 归档分组")
    print("=" * 60)
    
    # Display all groups in a single layer
    for group_name, files in priority_groups.items():
        # Determine the display name and icon based on group type
        if group_name.endswith("_archive"):
            # Subfolder archive (all files in one subfolder)
            folder_name = group_name.replace("_archive", "")
            icon = "📁"
            display_name = f"{folder_name} (subfolder archive | 子文件夹归档)"
        elif group_name.endswith("_multipart"):
            # Multi-part archive spanning directories
            archive_name = group_name.replace("_multipart", "")
            icon = "�"
            display_name = f"{archive_name} (multi-part archive | 多部分归档)"
        else:
            # Individual file
            parts = group_name.split("_", 1)
            if len(parts) > 1:
                folder_name, file_name = parts
                icon = "📄"
                display_name = f"{file_name} (in {folder_name} | 在 {folder_name} 中)"
            else:
                icon = "📄"
                display_name = group_name
        
        print(f"\n{icon} {display_name} ({len(files)} files | {len(files)} 个文件)")
        
        if verbose:
            for file_path in files:
                print(f"   📄 {file_path.name} ({file_path.parent})")
        else:
            displayed_files = files[:3]
            for file_path in displayed_files:
                print(f"   📄 {file_path.name}")
            if len(files) > 3:
                print(f"   ... and {len(files) - 3} more files | 还有 {len(files) - 3} 个文件")


def process_paths(paths: List[Path], recursive: bool = False, verbose: bool = False) -> None:
    """Process the provided paths for unzipping operations.
    
    Args:
        paths: List of validated Path objects (files or directories)
        recursive: Whether to recursively search directories
        verbose: Whether to show detailed information
    """
    print(f"Complex Unzip Tool v2 - Processing {len(paths)} path(s)")
    print(f"复杂解压工具 v2 - 正在处理 {len(paths)} 个路径")
    print("-" * 50)
    
    # Collect all files from the given paths
    all_files = collect_all_files(paths, recursive)
    
    if not all_files:
        print("❌ No files found | 未找到文件")
        return
    
    print(f"� Found {len(all_files)} total files | 总共找到 {len(all_files)} 个文件")
    
    if verbose:
        print("\n📋 All files found | 找到的所有文件:")
        for file_path in sorted(all_files):
            print(f"   📄 {file_path}")
    
    # Group files by subfolder
    subfolder_groups = group_files_by_subfolder(all_files)
    
    # Group files with subfolder priority (new priority-based grouping)
    priority_groups = group_files_by_priority(all_files)
    
    # Display the groups
    display_file_groups(subfolder_groups, priority_groups, verbose)
    
    print("\n" + "-" * 50)
    print("Processing complete! | 处理完成！")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Complex Unzip Tool v2 - Advanced zip file management\n"
                   "复杂解压工具 v2 - 高级压缩文件管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples | 示例:
  complex-unzip /path/to/file.zip                    # Extract a single zip file | 解压单个zip文件
  complex-unzip /path/to/directory                   # Process all files in directory | 处理目录中的所有文件
  complex-unzip file1.zip file2.zip /path/to/folder  # Process multiple files and folders | 处理多个文件和文件夹
  complex-unzip --recursive /path/to/nested/folders  # Recursively process nested directories | 递归处理嵌套目录
        """
    )
    
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more file paths or directory paths to process\n"
             "一个或多个要处理的文件路径或目录路径"
    )
    
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively search directories for zip files\n"
             "递归搜索目录中的压缩文件"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output directory for extracted files (default: same as source)\n"
             "解压文件的输出目录（默认：与源文件相同位置）"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output\n"
             "启用详细输出模式"
    )
    
    # Parse arguments
    try:
        args = parser.parse_args()
    except SystemExit:
        return
    
    # Validate paths
    try:
        validated_paths = validate_paths(args.paths)
    except FileNotFoundError as e:
        print(f"Error | 错误: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Set verbose mode
    if args.verbose:
        print("Verbose mode enabled | 详细模式已启用")
        print(f"Arguments | 参数: {vars(args)}")
    
    # Process the paths
    try:
        process_paths(validated_paths, args.recursive, args.verbose)
    except Exception as e:
        print(f"Error during processing | 处理过程中出错: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
