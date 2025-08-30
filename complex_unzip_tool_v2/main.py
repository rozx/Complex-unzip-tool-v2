"""
Complex Unzip Tool v2 - Advanced zip file management
复杂解压工具 v2 - 高级压缩文件管理工具

A sop                    i          safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件") else:
        safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")rename_errors:
            for error in rename_errors:
                safe_print(error)
    else:
        safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")
    
    if verbose:     safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件") else:
        safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")     for error in rename_errors:
                safe_print(error)
    else:
        safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")f rename_errors:
            for error in rename_errors:
                safe_print(error)
    else:
        safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")f rename_errors:
            for error in rename_errors:
                safe_print(error)
    else:
        safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")       safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件") else:
        safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")       safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")       safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")       safe_safe_print("✓ No cloaked files detected | 未检测到伪装文件")icated bilingual tool for analyzing and grouping archive files.
"""

import argparse
import shutil
import sys
import os
import re
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
    prompt_for_password, display_extraction_results, is_partial_archive,
    extract_partial_archive_and_reassemble, is_archive_file, get_ascii_temp_path,
    check_multipart_completeness, find_missing_parts_in_other_archives,
    extract_multipart_with_7z
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
    safe_print("✓ No cloaked files detected | 未检测到伪装文件")
    
    # Determine root path from the first path
    root_path = paths[0].parent if paths[0].is_file() else paths[0]
    
    # Collect all files from paths
    all_files = collect_all_files(paths, recursive)
    
    # Load password book and determine save location
    passwords = load_password_book(root_path)
    
    # Determine best location for saving new passwords
    possible_save_locations = [
        Path.cwd() / "passwords.txt",  # Current working directory (project dir) - preferred
        root_path / "passwords.txt",  # Target directory
    ]
    
    passwords_file = None
    for location in possible_save_locations:
        try:
            # Test if we can write to this location
            if location.exists() or location.parent.exists():
                passwords_file = location
                break
        except Exception:
            continue
    
    if not passwords_file:
        passwords_file = Path.cwd() / "passwords.txt"  # Fallback to current directory
    
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
        
        # Track archives that have been processed to avoid duplicate processing
        processed_archives = set()
        
        # Track container archives that should be cleaned up after successful extraction
        containers_to_cleanup = set()
        
        # Process each group in priority_groups, but prioritize groups with partial archives first
        groups_to_process = list(priority_groups.items())
        
        safe_print(f"\n🔍 Analyzing groups for partial archive priority...")
        
        # Sort groups to prioritize those containing partial archives
        def group_priority(group_item):
            group_name, group_files = group_item
            # Check if any file in this group might contain partial archive content
            for file_path in group_files:
                if is_archive_file(file_path, strict=True):
                    # Quick heuristic checks first
                    file_name = file_path.name.lower()
                    
                    # If filename suggests it might be a single part of something, prioritize it
                    if any(indicator in file_name for indicator in ['11111', 'part', 'vol', 'disc']):
                        safe_print(f"  🧩 Priority: {group_name} might contain partial content: {file_path.name}")
                        return 0
                    
                    # Try actual detection with very short timeout
                    try:
                        # Use ASCII temp path for the detection to avoid encoding issues
                        temp_file, needs_cleanup = get_ascii_temp_path(file_path)
                        try:
                            is_partial, base_name = is_partial_archive(temp_file)
                            if is_partial:
                                safe_print(f"  🧩 Priority: {group_name} contains partial archive: {file_path.name}")
                                return 0  # High priority for partial archives
                        finally:
                            if needs_cleanup and temp_file.exists():
                                try:
                                    temp_file.unlink()
                                except Exception:
                                    pass
                    except Exception as e:
                        safe_print(f"  ⚠️ Error checking {file_path.name}: {e}")
                        # If we can't check, but the name suggests partial content, prioritize anyway
                        if any(indicator in file_name for indicator in ['11111', 'part', 'vol']):
                            return 0
                        continue
            return 1  # Lower priority for regular archives
        
        groups_to_process.sort(key=group_priority)
        
        for group_name, group_files in groups_to_process:
            safe_print(f"\n📦 Processing group: {group_name} | 处理组: {group_name}")
            safe_print("-" * 40)
            
            # Find the main archive to extract
            main_archive = find_main_archive_in_group(group_files)
            
            if not main_archive:
                safe_print(f"  ❌ No main archive found in group | 组中未找到主压缩文件")
                extraction_result.failed_extractions.append((group_name, "No main archive found"))
                continue
            
            # Check if this archive was already processed as a container
            if main_archive in processed_archives:
                safe_print(f"  ⏭️ Archive already processed as container, skipping: {main_archive.name}")
                continue
            
            safe_print(f"  🎯 Main archive: {main_archive.name}")
            
            # Check if this is a multi-part archive and if it's complete
            is_multipart = False
            is_complete = False
            base_name = ""
            if re.match(r'.*\.001$', main_archive.name, re.IGNORECASE):
                is_multipart = True
                base_name = re.sub(r'\.001$', '', main_archive.name, flags=re.IGNORECASE)
                
                safe_print(f"  🧩 Detected multi-part archive: {base_name}")
                
                # Check completeness
                is_complete, found_parts, missing_parts = check_multipart_completeness(group_files, base_name)
                
                if not is_complete:
                    safe_print(f"  ⚠️ Multi-part archive incomplete! Found parts: {found_parts}, Missing: {missing_parts}")
                    
                    # Look for missing parts in other archives
                    part_locations = find_missing_parts_in_other_archives(missing_parts, base_name, priority_groups)
                    
                    if part_locations:
                        safe_print(f"  🔍 Found missing parts in other archives:")
                        for part_num, container_archive in part_locations.items():
                            safe_print(f"     Part {part_num:03d} found in: {container_archive.name}")
                        
                        # Extract the containers first to get the missing parts
                        extracted_any_parts = False
                        for part_num, container_archive in part_locations.items():
                            safe_print(f"  📦 Extracting container for part {part_num:03d}: {container_archive.name}")
                            
                            # Create temp directory for the container extraction
                            container_temp_dir = main_archive.parent / f"temp_container_{container_archive.stem}"
                            
                            try:
                                # For container extraction, always use regular extraction to get individual files
                                # Don't try to reassemble as multi-part archive - just extract contents
                                success, message, password_used = extract_with_7z(
                                    container_archive, container_temp_dir, passwords
                                )
                                
                                if success:
                                    safe_print(f"  ✅ Extracted container successfully")
                                    extracted_any_parts = True
                                    
                                    # Mark this archive as processed to avoid processing it again later
                                    processed_archives.add(container_archive)
                                    
                                    # Mark this container for cleanup when main extraction succeeds
                                    containers_to_cleanup.add(container_archive)
                                    
                                    if password_used and password_used not in passwords:
                                        passwords.append(password_used)
                                        extraction_result.new_passwords.append(password_used)
                                    
                                    # Copy extracted missing parts to the main archive directory
                                    expected_part_name = f"{base_name}.{part_num:03d}"
                                    
                                    for extracted_file in container_temp_dir.rglob("*"):
                                        if extracted_file.is_file() and expected_part_name.lower() in extracted_file.name.lower():
                                            target_path = main_archive.parent / expected_part_name
                                            shutil.copy2(extracted_file, target_path)
                                            safe_print(f"  📄 Copied missing part: {expected_part_name}")
                                            break
                                    else:
                                        safe_print(f"  ⚠️ Missing part {expected_part_name} not found in container")
                                else:
                                    safe_print(f"  ❌ Failed to extract container: {message}")
                                    
                            except Exception as e:
                                safe_print(f"  ❌ Error extracting container: {e}")
                            finally:
                                # Clean up container temp directory
                                if container_temp_dir.exists():
                                    shutil.rmtree(container_temp_dir, ignore_errors=True)
                        
                        if not extracted_any_parts:
                            safe_print(f"  ❌ Failed to extract any missing parts from containers")
                            extraction_result.failed_extractions.append((group_name, "Failed to extract missing parts from containers"))
                            continue
                        
                        # Now re-check if we have all parts after extraction
                        safe_print(f"  🔄 Re-checking completeness after container extraction...")
                        
                        # Rescan the directory to find all parts (including newly copied ones)
                        archive_dir = main_archive.parent
                        all_parts_in_dir = []
                        for file_path in archive_dir.iterdir():
                            if file_path.is_file() and base_name.lower() in file_path.name.lower() and re.search(r'\.\d{3}$', file_path.suffix):
                                all_parts_in_dir.append(file_path)
                        
                        is_complete, found_parts, missing_parts = check_multipart_completeness(all_parts_in_dir, base_name)
                        
                        if is_complete:
                            safe_print(f"  ✅ Multi-part archive is now complete with parts: {found_parts}")
                            # Update the group files to include the newly found parts
                            group_files = all_parts_in_dir
                        else:
                            safe_print(f"  ⚠️ Multi-part archive still incomplete after container extraction. Found parts: {found_parts}, Missing: {missing_parts}")
                            extraction_result.failed_extractions.append((group_name, f"Multi-part archive incomplete after container extraction. Missing parts: {missing_parts}"))
                            continue
                        
                    else:
                        safe_print(f"  ❌ Missing parts not found in any other archives")
                        extraction_result.failed_extractions.append((group_name, f"Multi-part archive incomplete. Missing parts: {missing_parts}"))
                        continue
                else:
                    safe_print(f"  ✅ Multi-part archive is complete with parts: {found_parts}")
            
            # Create temporary extraction directory
            temp_extract_dir = main_archive.parent / f"temp_extract_{group_name}"
            
            try:
                # Check if this is a partial archive that needs special handling
                # But skip partial archive logic if this is a complete multi-part archive
                is_partial, base_name_partial = is_partial_archive(main_archive)
                
                if is_partial and not (is_multipart and is_complete):
                    # This is a partial archive (not a complete multi-part archive)
                    safe_print(f"  🧩 Detected partial archive content, extracting and reassembling...")
                    success, message, password_used = extract_partial_archive_and_reassemble(main_archive, temp_extract_dir, passwords)
                else:
                    # Regular archive extraction (including complete multi-part archives)
                    if is_multipart and is_complete:
                        # For multi-part archives, we need to handle all parts together
                        safe_print(f"  🧩 Multi-part archive detected, handling all {len(group_files)} parts together")
                        success, message, password_used = extract_multipart_with_7z(group_files, temp_extract_dir, passwords)
                    else:
                        # Single archive extraction
                        success, message, password_used = extract_with_7z(main_archive, temp_extract_dir, passwords)
                
                # If extraction failed, prompt for password
                if not success and "password" in message.lower():
                    user_password = prompt_for_password(main_archive.name)
                    if user_password:
                        passwords.append(user_password)
                        if is_partial and not (is_multipart and is_complete):
                            success, message, password_used = extract_partial_archive_and_reassemble(main_archive, temp_extract_dir, [user_password])
                        else:
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
                    
                    # Also clean up container archives that were used for this group
                    containers_deleted = 0
                    containers_failed = 0
                    for container_archive in containers_to_cleanup:
                        try:
                            if container_archive.exists():
                                container_archive.unlink()
                                containers_deleted += 1
                                safe_print(f"  🗑️  Cleaned up container: {container_archive.name}")
                        except Exception as e:
                            containers_failed += 1
                            safe_print(f"  ❌ Failed to clean up container {container_archive.name}: {e}")
                    
                    total_deleted = deleted + containers_deleted
                    total_failed = failed + containers_failed
                    safe_print(f"  🗑️  Cleaned up: {total_deleted} files deleted, {total_failed} failed")
                    
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
