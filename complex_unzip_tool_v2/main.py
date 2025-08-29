"""
Complex Unzip Tool v2 - Advanced zip file management
复杂解压工具 v2 - 高级压缩文件管理工具

A sop        if rename_errors:
            for error in rename_errors:
                safe_print(error)
    else:
        safe_print("🔍 No cloaked files detected | 未检测到伪装文件")       safe_print("🔍 No cloaked files detected | 未检测到伪装文件") else:
        safe_print("🔍 No cloaked files detected | 未检测到伪装文件")       safe_print("🔍 No cloaked files detected | 未检测到伪装文件")       safe_print("� No cloaked files detected | 未检测到伪装文件")       safe_print("� No cloaked files detected | 未检测到伪装文件")icated bilingual tool for analyzing and grouping archive files.
"""

import argparse
import shutil
import sys
import os
from pathlib import Path
from typing import List

# Fix Windows console encoding for Unicode characters
if sys.platform.startswith('win'):
    try:
        # Set UTF-8 code page for Windows console
        os.system('chcp 65001 >nul 2>&1')
    except Exception:
        pass

from .file_collector import collect_all_files
from .file_grouper import group_files_by_subfolder, group_files_by_priority
from .display_utils import display_file_groups
from .path_validator import validate_paths
from .password_manager import load_password_book, display_password_info, save_new_passwords
from .file_renamer import detect_cloaked_files, rename_cloaked_files, display_rename_suggestions
from .console_utils import safe_print
from .archive_extractor import (
    ExtractionResult, find_main_archive_in_group, extract_with_7z, 
    extract_nested_archives, create_completed_structure, clean_up_original_files,
    prompt_for_password, display_extraction_results
)


def process_paths(paths: List[Path], recursive: bool = False, verbose: bool = False, 
                 dry_run: bool = False, no_extract: bool = False) -> None:
    """Process the provided paths for unzipping operations.
    
    Args:
        paths: List of validated Path objects (files or directories)
        recursive: Whether to recursively search directories
        verbose: Whether to show detailed information
        dry_run: Whether to simulate renaming without actually doing it
        no_extract: Whether to skip archive extraction (extraction is default)
    """
    safe_print(f"Complex Unzip Tool v2 - Processing {len(paths)} path(s)")
    safe_print(f"复杂解压工具 v2 - 正在处理 {len(paths)} 个路径")
    safe_print("-" * 50)
    
    # Collect all files from the given paths
    all_files = collect_all_files(paths, recursive)
    
    if not all_files:
        safe_print("❌ No files found | 未找到文件")
        return
    
    safe_print(f"📁 Found {len(all_files)} total files | 总共找到 {len(all_files)} 个文件")
    
    # Determine root path for grouping logic
    root_path = paths[0] if len(paths) == 1 and paths[0].is_dir() else Path.cwd()
    
    # Load password book from root directory
    passwords = load_password_book(root_path)
    
    # Automatically detect and rename cloaked files
    rename_suggestions = detect_cloaked_files(all_files)
    
    if rename_suggestions:
        display_rename_suggestions(rename_suggestions)
        
        # Always perform the renaming (unless dry-run mode)
        renamed_files, rename_errors = rename_cloaked_files(rename_suggestions, dry_run=dry_run)
        
        if not dry_run and renamed_files:
            # Update all_files list with new paths
            updated_files = []
            rename_map = {old: new for old, new in rename_suggestions.items()}
            
            for file_path in all_files:
                if file_path in rename_map:
                    updated_files.append(rename_map[file_path])
                else:
                    updated_files.append(file_path)
            
            all_files = updated_files
            safe_print(f"📁 Updated file list after renaming | 重命名后更新文件列表")
        
        if rename_errors:
            for error in rename_errors:
                safe_print(error)
    else:
        print("� No cloaked files detected | 未检测到伪装文件")
    
    if verbose:
        safe_print("\n📋 All files found | 找到的所有文件:")
        for file_path in sorted(all_files):
            safe_print(f"   📄 {file_path}")
        
        # Display password information if verbose
        display_password_info(passwords, verbose=True)
    
    # Group files by subfolder
    subfolder_groups = group_files_by_subfolder(all_files)
    
    # Group files with root-aware priority logic
    priority_groups = group_files_by_priority(all_files, root_path)
    
    # Display the groups
    display_file_groups(subfolder_groups, priority_groups, verbose)
    
    # Perform extraction by default (unless disabled or dry-run)
    if not no_extract and not dry_run:
        safe_print("\n" + "=" * 60)
        safe_print("🚀 STARTING ARCHIVE EXTRACTION | 开始压缩文件解压")
        safe_print("=" * 60)
        
        extraction_result = ExtractionResult()
        completed_dir = root_path / "completed"
        passwords_file = root_path / "passwords.txt"
        
        # Process each group in priority_groups
        for group_name, group_files in priority_groups.items():
            safe_print(f"\n📦 Processing group: {group_name} | 处理组: {group_name}")
            safe_print("-" * 40)
            
            # Find the main archive to extract
            main_archive = find_main_archive_in_group(group_files)
            
            if not main_archive:
                safe_print(f"  ❌ No main archive found in group | 组中未找到主压缩文件")
                extraction_result.failed_extractions.append((group_name, "No main archive found"))
                continue
            
            safe_print(f"  🎯 Main archive: {main_archive.name}")
            
            # Create temporary extraction directory
            temp_extract_dir = main_archive.parent / f"temp_extract_{group_name}"
            
            try:
                # Try extraction with available passwords
                success, message, password_used = extract_with_7z(main_archive, temp_extract_dir, passwords)
                
                # If extraction failed, prompt for password
                if not success and "password" in message.lower():
                    user_password = prompt_for_password(main_archive.name)
                    if user_password:
                        passwords.append(user_password)
                        success, message, password_used = extract_with_7z(main_archive, temp_extract_dir, [user_password])
                        if success:
                            extraction_result.new_passwords.append(user_password)
                
                if success:
                    safe_print(f"  ✅ Extracted main archive successfully")
                    
                    # Extract nested archives recursively
                    safe_print(f"  🔄 Checking for nested archives...")
                    final_files, new_passwords = extract_nested_archives(temp_extract_dir, passwords)
                    extraction_result.new_passwords.extend(new_passwords)
                    
                    # Copy files to completed directory
                    group_completed_dir = create_completed_structure(completed_dir, group_name, final_files)
                    extraction_result.completed_files.extend(final_files)
                    
                    # Clean up original files
                    deleted, failed = clean_up_original_files(group_files)
                    safe_print(f"  🗑️  Cleaned up: {deleted} files deleted, {failed} failed")
                    
                    # Clean up temporary directory
                    if temp_extract_dir.exists():
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                    
                    extraction_result.successful_extractions.append((group_name, len(final_files)))
                    
                else:
                    safe_print(f"  ❌ Extraction failed: {message}")
                    extraction_result.failed_extractions.append((group_name, message))
                    
                    # Clean up failed extraction directory
                    if temp_extract_dir.exists():
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                
            except Exception as e:
                safe_print(f"  ❌ Error processing group: {e}")
                extraction_result.failed_extractions.append((group_name, str(e)))
                
                # Clean up on error
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)
        
        # Save new passwords to password book
        if extraction_result.new_passwords:
            save_new_passwords(passwords_file, extraction_result.new_passwords)
        
        # Display final results
        display_extraction_results(extraction_result)
        
    elif not no_extract and dry_run:
        safe_print("\n💡 Extraction not performed in dry-run mode | 预演模式下不执行解压")
        safe_print("💡 Use without --dry-run to perform actual extraction | 不使用 --dry-run 执行实际解压")
    elif no_extract:
        safe_print("\n💡 Extraction skipped (--no-extract specified) | 跳过解压（指定了 --no-extract）")
    
    # Display password book summary (non-verbose)
    if not verbose and passwords:
        display_password_info(passwords, verbose=False)
    
    safe_print("\n" + "-" * 50)
    safe_print("Processing complete! | 处理完成！")


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="Complex Unzip Tool v2 - Advanced archive extraction and management tool\n"
                   "复杂解压工具 v2 - 高级压缩文件解压和管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Features | 功能:
  * Automatic archive extraction with 7z.exe (default) | 使用7z.exe自动解压（默认）
  * Recursive directory processing (default) | 递归目录处理（默认）
  * Automatic cloaked file renaming (*.001删 → *.001) | 自动伪装文件重命名
  * Password book loading from passwords.txt | 从passwords.txt加载密码本
  * Intelligent multi-part archive detection | 智能多部分压缩文件检测
  * Recursive nested archive extraction | 递归嵌套压缩文件解压
  * Interactive password prompting | 交互式密码提示
  * Automatic file organization to 'completed' folder | 自动文件整理到'completed'文件夹
  * Bilingual interface (English/Chinese) | 双语界面（英文/中文）

Examples | 示例:
  complex-unzip /path/to/archives                    # Extract all archives recursively (default) | 递归解压所有压缩文件（默认）
  complex-unzip --no-recursive /path/to/directory    # Only process files in the specified directory | 仅处理指定目录中的文件
  complex-unzip --no-extract /path/to/directory      # Only analyze without extraction | 仅分析不解压
  complex-unzip --dry-run /path/to/directory         # Preview renaming without extraction | 预览重命名但不解压
  complex-unzip --verbose /path/to/directory         # Show detailed extraction info | 显示详细解压信息
        """
    )
    
    parser.add_argument(
        "paths",
        nargs="*",
        help="One or more file paths or directory paths to process\n"
             "一个或多个要处理的文件路径或目录路径"
    )
    
    parser.add_argument(
        "-r", "--no-recursive",
        action="store_true",
        help="Disable recursive directory search (recursive is default)\n"
             "禁用递归目录搜索（默认为递归）"
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
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate file renaming without actually renaming files (renaming is automatic)\n"
             "模拟文件重命名而不实际重命名文件（重命名是自动的）"
    )
    
    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Skip archive extraction (extraction is performed by default)\n"
             "跳过压缩文件解压（默认执行解压）"
    )
    
    args = parser.parse_args()
    
    # Handle drag and drop scenario (when used as compiled EXE)
    # If no paths provided, show help but also check for interactive mode
    if not args.paths:
        # Check if running as compiled EXE and suggest drag and drop
        import sys
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            safe_print("🖱️  Drag and Drop Mode | 拖拽模式")
            safe_print("=" * 50)
            safe_print("This tool supports drag and drop!")
            safe_print("此工具支持拖拽操作！")
            safe_print("")
            safe_print("To use:")
            safe_print("使用方法：")
            safe_print("1. Drag files or folders onto this EXE file")
            safe_print("   将文件或文件夹拖拽到此 EXE 文件上")
            safe_print("2. Or run from command line with paths as arguments")
            safe_print("   或从命令行运行并提供路径参数")
            safe_print("")
            safe_print("For command line usage:")
            safe_print("命令行用法：")
            parser.print_help()
            safe_print("")
            input("Press Enter to exit | 按回车键退出...")
        else:
            # Running in development mode
            parser.print_help()
        return
    
    # Show drag and drop confirmation for EXE mode
    import sys
    if getattr(sys, 'frozen', False) and len(args.paths) > 0:
        safe_print("🖱️  Files/folders received via drag and drop!")
        safe_print("🖱️  通过拖拽接收到文件/文件夹！")
        safe_print("=" * 50)
        for i, path in enumerate(args.paths, 1):
            safe_print(f"{i}. {path}")
        safe_print("=" * 50)
        safe_print("")
    
    if args.verbose:
        safe_print("Verbose mode enabled | 详细模式已启用")
        safe_print(f"Arguments | 参数: {vars(args)}")
    
    # Validate paths
    try:
        validated_paths = validate_paths(args.paths)
    except FileNotFoundError as e:
        safe_print(f"❌ Error: {e}")
        exit(1)
    
    # Determine recursive behavior (default is True, disabled by --no-recursive or -r)
    recursive = not args.no_recursive
    
    # Process the paths
    process_paths(validated_paths, recursive, args.verbose, args.dry_run, args.no_extract)
    
    # Pause for EXE mode so users can see results
    import sys
    if getattr(sys, 'frozen', False):
        safe_print("")
        safe_print("=" * 50)
        input("Press Enter to exit | 按回车键退出...")


if __name__ == "__main__":
    main()
