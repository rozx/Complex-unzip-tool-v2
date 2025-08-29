"""
Complex Unzip Tool v2 - Advanced zip file management
复杂解压工具 v2 - 高级压缩文件管理工具

A sophisticated bilingual tool for analyzing and grouping archive files.
"""

import argparse
from pathlib import Path
from typing import List

from .file_collector import collect_all_files
from .file_grouper import group_files_by_subfolder, group_files_by_priority
from .display_utils import display_file_groups
from .path_validator import validate_paths


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
    
    print(f"📁 Found {len(all_files)} total files | 总共找到 {len(all_files)} 个文件")
    
    if verbose:
        print("\n📋 All files found | 找到的所有文件:")
        for file_path in sorted(all_files):
            print(f"   📄 {file_path}")
    
    # Determine root path for grouping logic
    root_path = paths[0] if len(paths) == 1 and paths[0].is_dir() else Path.cwd()
    
    # Group files by subfolder
    subfolder_groups = group_files_by_subfolder(all_files)
    
    # Group files with root-aware priority logic
    priority_groups = group_files_by_priority(all_files, root_path)
    
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
        help="Output directory for extracted files (optional)\n"
             "解压文件的输出目录（可选）"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output for detailed information\n"
             "启用详细输出以获取详细信息"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        print("Verbose mode enabled | 详细模式已启用")
        print(f"Arguments | 参数: {vars(args)}")
    
    # Validate paths
    try:
        validated_paths = validate_paths(args.paths)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        exit(1)
    
    # Process the paths
    process_paths(validated_paths, args.recursive, args.verbose)


if __name__ == "__main__":
    main()
