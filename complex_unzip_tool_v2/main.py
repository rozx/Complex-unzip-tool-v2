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
from typing import List, Optional

# Fix Windows console encoding for Unicode characters
if sys.platform.startswith('win'):
    try:
        # Set UTF-8 code page for Windows console
        os.system('chcp 65001 >nul 2>&1')
    except Exception:
        pass

from .file_collector import collect_all_files
from .file_grouper import group_files_by_priority
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
from .multipart_detector import check_archive_completeness, prioritize_extraction_order
from .file_organizer import organize_and_cleanup, create_extraction_summary


import re
import shutil


def process_subfolder_group(group_name: str, group_files: List[Path], completed_dir: Path, 
                           extraction_result: ExtractionResult, processed_archives: set, 
                           passwords: List[str], root_path: Path, 
                           containers_to_cleanup: Optional[set] = None, extracted_parts_to_cleanup: Optional[set] = None) -> bool:
    """Process all files in a subfolder as a coordinated group.
    
    This function handles all files in a subfolder together, looking for multi-part archives
    and container files that may contain missing parts.
    
    Args:
        group_name: Name of the group
        group_files: List of files in the subfolder
        completed_dir: Directory for completed extractions (not used for subfolder groups)
        extraction_result: Result tracking object
        processed_archives: Set of already processed archives
        passwords: List of passwords to try
        root_path: Root path being processed
        
    Returns:
        True if any extraction was successful
    """
    # Initialize tracking sets if not provided
    if containers_to_cleanup is None:
        containers_to_cleanup = set()
    if extracted_parts_to_cleanup is None:
        extracted_parts_to_cleanup = set()
        
    safe_print(f"  📁 Processing subfolder group with {len(group_files)} files | 处理包含 {len(group_files)} 个文件的子文件夹组")
    
    # Analyze files in the subfolder to identify multi-part archives and containers
    multipart_archives = {}  # base_name -> list of part files
    container_files = []  # potential container files like 11111.7z
    other_files = []
    
    # Group by archive patterns
    for file_path in group_files:
        file_name = file_path.name
        
        # Check for multi-part archive pattern (*.001, *.002, etc.)
        multipart_match = re.match(r'^(.+?)\.(\d{3})$', file_name, re.IGNORECASE)
        if multipart_match:
            base_name = multipart_match.group(1)
            part_num = int(multipart_match.group(2))
            
            if base_name not in multipart_archives:
                multipart_archives[base_name] = []
            multipart_archives[base_name].append((part_num, file_path))
        else:
            # Check if it might be a container file (common name patterns)
            if any(pattern in file_name.lower() for pattern in ['11111', 'container', 'parts']):
                container_files.append(file_path)
            else:
                other_files.append(file_path)
    
    total_extracted = 0
    successful_extractions = []
    
    # Process multi-part archives first
    for base_name, parts_list in multipart_archives.items():
        parts_list.sort()  # Sort by part number
        part_files = [path for _, path in parts_list]
        part_numbers = [num for num, _ in parts_list]
        
        safe_print(f"  🧩 Found multi-part archive: {base_name} with parts {part_numbers} | 发现多部分压缩文件: {base_name}，部分 {part_numbers}")
        
        # Helper function for part number extraction
        def extract_part_number(path):
            match = re.search(r'\.(\d{3})$', path.name)
            return int(match.group(1)) if match else 999
        
        # Use proper completeness checking function
        is_complete, found_parts, missing_parts = check_multipart_completeness(part_files, base_name)
        
        if not is_complete:
            safe_print(f"  ⚠️ Multi-part archive incomplete! Found parts: {found_parts}, Missing: {missing_parts} | 多部分压缩文件不完整！找到部分: {found_parts}，缺少: {missing_parts}")
            
            # First, search for missing parts in the same group (same subfolder)
            safe_print(f"  🔍 Searching for missing parts in same subfolder | 在同一子文件夹中搜索缺少的部分")
            
            # Look for missing parts in container files within the same subfolder
            for missing_part in missing_parts[:]:  # Use slice to allow modification during iteration
                missing_file_name = f"{base_name}.{missing_part:03d}"
                
                # Check if the missing part might be in a container file
                for container_file in container_files:
                    if container_file in processed_archives:
                        continue
                        
                    safe_print(f"  📦 Checking container file for missing part {missing_part:03d}: {container_file.name}")
                    
                    # Extract container to current path (same directory as the container)
                    container_extract_dir = container_file.parent
                    
                    try:
                        success, message, password_used = extract_with_7z(container_file, container_extract_dir, passwords)
                        
                        if success:
                            # Track successfully processed archive
                            extraction_result.successfully_processed_archives.append(container_file)
                            processed_archives.add(container_file)
                            
                            safe_print(f"  ✅ Extracted container successfully | 容器解压成功")
                            
                            # Look for the missing part in the extracted content
                            potential_part_path = container_extract_dir / missing_file_name
                            if potential_part_path.exists():
                                safe_print(f"  📄 Found missing part: {missing_file_name} | 找到缺少的部分: {missing_file_name}")
                                part_files.append(potential_part_path)
                                part_numbers.append(missing_part)
                                # Track this extracted part for cleanup
                                extracted_parts_to_cleanup.add(potential_part_path)
                                missing_parts.remove(missing_part)
                                break
                            else:
                                # Search in any subdirectories that might have been created
                                for extracted_file in container_extract_dir.rglob(missing_file_name):
                                    if extracted_file.is_file():
                                        # Move the file to the correct location
                                        dest_path = container_extract_dir / missing_file_name
                                        if extracted_file != dest_path:
                                            shutil.move(str(extracted_file), str(dest_path))
                                        safe_print(f"  📄 Found and moved missing part: {missing_file_name}")
                                        part_files.append(dest_path)
                                        part_numbers.append(missing_part)
                                        # Track this extracted part for cleanup
                                        extracted_parts_to_cleanup.add(dest_path)
                                        missing_parts.remove(missing_part)
                                        break
                            
                            # Mark container as processed
                            processed_archives.add(container_file)
                            
                            if password_used:
                                extraction_result.passwords_used.append(password_used)
                        else:
                            safe_print(f"  ❌ Failed to extract container: {message}")
                            
                    except Exception as e:
                        safe_print(f"  ❌ Error extracting container: {e}")
            
            # Re-check completeness after searching in containers
            # Create a list of all files (original + found parts) to check completeness
            all_available_files = part_files.copy()
            
            # Scan the directory for any new parts that might have been extracted
            if part_files:
                current_dir = part_files[0].parent
                for file_path in current_dir.iterdir():
                    if file_path.is_file() and base_name.lower() in file_path.name.lower() and re.search(r'\.\d{3}$', file_path.suffix):
                        if file_path not in all_available_files:
                            all_available_files.append(file_path)
            
            is_complete, found_parts, missing_parts = check_multipart_completeness(all_available_files, base_name)
            
            if is_complete:
                safe_print(f"  ✅ Multi-part archive is now complete with parts: {found_parts} | 多部分压缩文件现在完整，包含部分: {found_parts}")
                part_files = all_available_files  # Update part_files with all found parts
        else:
            safe_print(f"  ✅ Multi-part archive is complete with parts: {found_parts} | 多部分压缩文件完整，包含部分: {found_parts}")
        
        # Now try to extract the multi-part archive only if complete
        # Now try to extract the multi-part archive only if complete
        if not is_complete:
            safe_print(f"  ⚠️ Still missing parts: {missing_parts}, cannot extract | 仍缺少部分: {missing_parts}，无法解压")
            extraction_result.failed_extractions.append((f"{group_name}_{base_name}", f"Missing parts: {missing_parts}"))
        else:
            # We have all parts, try extraction
            part_files.sort(key=extract_part_number)
            if part_files and part_files[0].name.endswith('.001'):
                try:
                    # Extract to current path (same directory as the parts)
                    current_extract_dir = part_files[0].parent
                    success, message, password_used = extract_multipart_with_7z(part_files, current_extract_dir, passwords)
                    
                    if success:
                        safe_print(f"  ✅ Successfully extracted multi-part archive: {base_name} | 成功解压多部分压缩文件: {base_name}")
                        total_extracted += 1
                        successful_extractions.append(f"{base_name}: multi-part archive")
                        
                        # Check if extracted content contains partial archive files
                        extracted_files = list(current_extract_dir.rglob('*'))
                        extracted_files = [f for f in extracted_files if f.is_file() and f.parent != current_extract_dir]  # Exclude original archive files
                        
                        contains_partial_archives = any(
                            re.search(r'\.\d{3}$', f.name) or 'part' in f.name.lower() 
                            for f in extracted_files
                        )
                        
                        if not contains_partial_archives and extracted_files:
                            # Move extracted content to _Unzipped folder
                            safe_print(f"  📁 Moving final extracted content to _Unzipped folder | 将最终解压内容移动到 _Unzipped 文件夹")
                            unzipped_dir = root_path / "_Unzipped"
                            unzipped_dir.mkdir(parents=True, exist_ok=True)
                            
                            moved_count = 0
                            for extracted_file in extracted_files:
                                try:
                                    # Calculate relative path from extraction directory, skipping intermediate folders
                                    rel_path = extracted_file.relative_to(current_extract_dir)
                                    
                                    # Skip the first part if it looks like an archive name
                                    if len(rel_path.parts) > 1:
                                        first_part = rel_path.parts[0]
                                        # If the first part looks like an archive name, skip it
                                        if any(ext in first_part.lower() for ext in ['.7z', '.zip', '.rar']) or first_part.endswith('.7z'):
                                            dest_rel_path = Path(*rel_path.parts[1:]) if len(rel_path.parts) > 1 else Path(rel_path.name)
                                        else:
                                            dest_rel_path = rel_path
                                    else:
                                        dest_rel_path = rel_path
                                    
                                    dest_path = unzipped_dir / dest_rel_path
                                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.move(str(extracted_file), str(dest_path))
                                    moved_count += 1
                                except Exception as e:
                                    safe_print(f"  ⚠️ Failed to move {extracted_file.name}: {e}")
                            
                            safe_print(f"  ✅ Moved {moved_count} files to _Unzipped | 移动了 {moved_count} 个文件到 _Unzipped")
                        
                        # Mark all parts as processed
                        for part_file in part_files:
                            processed_archives.add(part_file)
                            
                        if password_used:
                            extraction_result.passwords_used.append(password_used)
                    else:
                        safe_print(f"  ❌ Failed to extract multi-part archive: {message}")
                        extraction_result.failed_extractions.append((f"{group_name}_{base_name}", message))
                        
                except Exception as e:
                    safe_print(f"  ❌ Error extracting multi-part archive: {e}")
                    extraction_result.failed_extractions.append((f"{group_name}_{base_name}", str(e)))
    
    # Process remaining individual files (excluding already processed containers)
    for file_path in other_files + container_files:
        if file_path in processed_archives:
            continue
            
        if is_archive_file(file_path):
            try:
                # Extract to current path (same directory as the archive)
                current_extract_dir = file_path.parent
                success, message, password_used = extract_with_7z(file_path, current_extract_dir, passwords)
                
                if success:
                    # Track successfully processed archive
                    extraction_result.successfully_processed_archives.append(file_path)
                    
                    safe_print(f"  ✅ Successfully extracted individual archive: {file_path.name}")
                    total_extracted += 1
                    successful_extractions.append(f"{file_path.name}: individual archive")
                    processed_archives.add(file_path)
                    
                    # Check if extracted content contains partial archive files
                    extracted_files = list(current_extract_dir.rglob('*'))
                    extracted_files = [f for f in extracted_files if f.is_file() and f.parent != current_extract_dir]  # Exclude original archive files
                    
                    contains_partial_archives = any(
                        re.search(r'\.\d{3}$', f.name) or 'part' in f.name.lower() 
                        for f in extracted_files
                    )
                    
                    if not contains_partial_archives and extracted_files:
                        # Move extracted content to _Unzipped folder
                        safe_print(f"  📁 Moving final extracted content to _Unzipped folder | 将最终解压内容移动到 _Unzipped 文件夹")
                        unzipped_dir = root_path / "_Unzipped" / group_name / file_path.stem
                        unzipped_dir.mkdir(parents=True, exist_ok=True)
                        
                        moved_count = 0
                        for extracted_file in extracted_files:
                            try:
                                # Calculate relative path from extraction directory
                                rel_path = extracted_file.relative_to(current_extract_dir)
                                dest_path = unzipped_dir / rel_path
                                dest_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.move(str(extracted_file), str(dest_path))
                                moved_count += 1
                            except Exception as e:
                                safe_print(f"  ⚠️ Failed to move {extracted_file.name}: {e}")
                        
                        safe_print(f"  ✅ Moved {moved_count} files to _Unzipped | 移动了 {moved_count} 个文件到 _Unzipped")
                    
                    if password_used:
                        extraction_result.passwords_used.append(password_used)
                else:
                    safe_print(f"  ❌ Failed to extract individual archive: {message}")
                    extraction_result.failed_extractions.append((f"{group_name}_{file_path.name}", message))
                    
            except Exception as e:
                safe_print(f"  ❌ Error extracting individual archive: {e}")
                extraction_result.failed_extractions.append((f"{group_name}_{file_path.name}", str(e)))
    
    if successful_extractions:
        extraction_result.successful_extractions.append((group_name, f"{total_extracted} files extracted from {len(successful_extractions)} archives"))
        safe_print(f"  ✅ Subfolder group completed: {total_extracted} extractions | 子文件夹组完成: {total_extracted} 个解压")
        
        # Clean up original files after successful extraction
        safe_print(f"  🗑️ Cleaning up original files | 清理原始文件")
        cleaned_count = 0
        failed_count = 0
        
        for file_path in group_files:
            if file_path in processed_archives:
                try:
                    if file_path.exists():
                        file_path.unlink()
                        cleaned_count += 1
                        safe_print(f"    🗑️ Deleted: {file_path.name}")
                except Exception as e:
                    failed_count += 1
                    safe_print(f"    ❌ Failed to delete {file_path.name}: {e}")
        
        # Debug: Show what we're tracking for cleanup
        if containers_to_cleanup or extracted_parts_to_cleanup:
            safe_print(f"  🔍 Debug: Containers to cleanup: {len(containers_to_cleanup)} | 容器清理追踪: {len(containers_to_cleanup)}")
            safe_print(f"  🔍 Debug: Extracted parts to cleanup: {len(extracted_parts_to_cleanup)} | 解压部分清理追踪: {len(extracted_parts_to_cleanup)}")
        
        # Clean up container archives that were used for this group
        containers_deleted = 0
        containers_failed = 0
        for container_archive in containers_to_cleanup:
            try:
                if container_archive.exists():
                    container_archive.unlink()
                    containers_deleted += 1
                    safe_print(f"    🗑️ Cleaned up container: {container_archive.name} | 清理容器: {container_archive.name}")
            except Exception as e:
                containers_failed += 1
                safe_print(f"    ❌ Failed to clean up container {container_archive.name}: {e} | 清理容器失败 {container_archive.name}: {e}")
        
        # Clean up extracted parts that were found in containers
        extracted_parts_deleted = 0
        extracted_parts_failed = 0
        for extracted_part in extracted_parts_to_cleanup:
            try:
                if extracted_part.exists():
                    extracted_part.unlink()
                    extracted_parts_deleted += 1
                    safe_print(f"    🗑️ Cleaned up extracted part: {extracted_part.name} | 清理解压的部分: {extracted_part.name}")
            except Exception as e:
                extracted_parts_failed += 1
                safe_print(f"    ❌ Failed to clean up extracted part {extracted_part.name}: {e} | 清理解压部分失败 {extracted_part.name}: {e}")
        
        # Clean up extracted content folders and temp files in the subfolder
        subfolder_cleanup_deleted = 0
        subfolder_cleanup_failed = 0
        
        # Get the subfolder path
        subfolder_path = group_files[0].parent if group_files else None
        if subfolder_path and subfolder_path.exists():
            # Clean up temp multipart files
            for temp_file in subfolder_path.glob("temp_multipart_*"):
                try:
                    if temp_file.is_file():
                        temp_file.unlink()
                        subfolder_cleanup_deleted += 1
                        safe_print(f"    🗑️ Cleaned up temp file: {temp_file.name} | 清理临时文件: {temp_file.name}")
                except Exception as e:
                    subfolder_cleanup_failed += 1
                    safe_print(f"    ❌ Failed to clean up temp file {temp_file.name}: {e} | 清理临时文件失败 {temp_file.name}: {e}")
            
            # Clean up remaining archive parts that weren't processed
            for archive_file in subfolder_path.glob("*.7z.*"):
                try:
                    if archive_file.is_file() and re.search(r'\.\d{3}$', archive_file.suffix):
                        archive_file.unlink()
                        subfolder_cleanup_deleted += 1
                        safe_print(f"    🗑️ Cleaned up unused archive part: {archive_file.name} | 清理未使用的压缩文件部分: {archive_file.name}")
                except Exception as e:
                    subfolder_cleanup_failed += 1
                    safe_print(f"    ❌ Failed to clean up archive part {archive_file.name}: {e} | 清理压缩文件部分失败 {archive_file.name}: {e}")
            
            # Clean up extracted content folders (folders that were created by extraction)
            for item in subfolder_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if this is likely an extracted content folder
                    # Since we've already moved content to _Unzipped, we can remove extracted folders
                    try:
                        # Remove any folder that looks like extracted content or is empty
                        item_files = list(item.rglob('*'))
                        item_files = [f for f in item_files if f.is_file()]
                        
                        # Remove if it's an extracted content folder (has many files) or is empty
                        should_remove = (
                            len(item_files) == 0 or  # Empty folder
                            len(item_files) > 5 or   # Likely extracted content
                            any(keyword in item.name.lower() for keyword in ['xiuren', '秀人', '鱼子酱', 'p+', 'g]', '【', '】'])  # Content folder patterns
                        )
                        
                        if should_remove:
                            shutil.rmtree(item, ignore_errors=True)
                            if not item.exists():
                                subfolder_cleanup_deleted += 1
                                safe_print(f"    🗑️ Cleaned up extracted folder: {item.name} | 清理解压文件夹: {item.name}")
                            else:
                                subfolder_cleanup_failed += 1
                                safe_print(f"    ⚠️ Failed to fully clean up folder: {item.name} | 无法完全清理文件夹: {item.name}")
                    except Exception as e:
                        subfolder_cleanup_failed += 1
                        safe_print(f"    ❌ Failed to clean up folder {item.name}: {e} | 清理文件夹失败 {item.name}: {e}")
        
        # Update totals
        cleaned_count += containers_deleted + extracted_parts_deleted + subfolder_cleanup_deleted
        failed_count += containers_failed + extracted_parts_failed + subfolder_cleanup_failed
        
        # Try to remove the subfolder if it's empty
        subfolder_path = group_files[0].parent if group_files else None
        if subfolder_path and subfolder_path.exists():
            try:
                remaining_files = list(subfolder_path.rglob('*'))
                remaining_files = [f for f in remaining_files if f.is_file()]
                
                if not remaining_files:
                    subfolder_path.rmdir()
                    safe_print(f"  🗑️ Deleted empty subfolder: {subfolder_path.name} | 删除空子文件夹: {subfolder_path.name}")
                else:
                    safe_print(f"  ⚠️ Subfolder {subfolder_path.name} still contains {len(remaining_files)} files - keeping | 子文件夹 {subfolder_path.name} 仍包含 {len(remaining_files)} 个文件 - 保留")
            except Exception as e:
                safe_print(f"  ❌ Failed to delete subfolder {subfolder_path.name}: {e}")
        
        safe_print(f"  🗑️ Cleanup completed: {cleaned_count} files deleted, {failed_count} failed | 清理完成: {cleaned_count} 个文件已删除，{failed_count} 个失败")
        return True
    else:
        safe_print(f"  ❌ No successful extractions in subfolder group | 子文件夹组中无成功解压")
        return False


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
    
    # Determine root path from the first path
    root_path = paths[0].parent if paths[0].is_file() else paths[0]
    
    # Collect all files from paths
    all_files = collect_all_files(paths, recursive)
    
    # Detect and rename cloaked files
    cloaked_files = detect_cloaked_files(all_files)
    if cloaked_files:
        safe_print(f"\n🔍 Detected {len(cloaked_files)} cloaked files | 检测到 {len(cloaked_files)} 个伪装文件")
        if verbose:
            display_rename_suggestions(cloaked_files)
        
        # Automatically rename cloaked files
        successful_renames, rename_errors = rename_cloaked_files(cloaked_files, dry_run=False)
        if rename_errors:
            safe_print("⚠️ Some files could not be renamed | 部分文件无法重命名:")
            for error in rename_errors:
                safe_print(f"  ❌ {error}")
        elif successful_renames:
            safe_print("✅ All cloaked files renamed successfully | 所有伪装文件重命名成功")
        
        # Re-collect files after renaming
        all_files = collect_all_files(paths, recursive)
    else:
        safe_print("✓ No cloaked files detected | 未检测到伪装文件")
    
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
    
    # Group files with root-aware priority logic
    priority_groups = group_files_by_priority(all_files, root_path)
    
    # Display the groups
    display_file_groups(priority_groups, verbose)
    
    # Perform extraction by default (unless disabled or dry-run)
    if not no_extract and not dry_run:
        safe_print("\n" + "=" * 60)
        safe_print("🚀 STARTING ARCHIVE EXTRACTION | 开始压缩文件解压")
        safe_print("=" * 60)
        
        # Step 1: Check multi-part archive completeness
        multipart_archives, potential_missing_containers = check_archive_completeness(all_files, verbose)
        
        extraction_result = ExtractionResult()
        
        # Track archives that have been processed to avoid duplicate processing
        processed_archives = set()
        
        # Track container archives that should be cleaned up after successful extraction
        containers_to_cleanup = set()
        
        # Track extracted parts that should be cleaned up after successful extraction
        extracted_parts_to_cleanup = set()
        
        # Track successfully extracted files for organization
        extracted_files = []
        
        # Track successfully processed archive files for cleanup
        successfully_processed_archives = []
        
        # Add back variables needed by existing code
        completed_dir = root_path / "_Unzipped"
        passwords_file = root_path / "passwords.txt"
        processed_subfolders = set()
        
        # Step 2: Prioritize extraction order based on multi-part analysis
        if multipart_archives or potential_missing_containers:
            # Get files from all groups for prioritization
            all_group_files = []
            for group_files in priority_groups.values():
                all_group_files.extend(group_files)
            
            # Prioritize extraction order
            prioritized_files = prioritize_extraction_order(multipart_archives, all_group_files)
            
            safe_print(f"\n📋 Extraction order optimized based on multi-part analysis | 基于多部分分析优化解压顺序")
            if verbose and prioritized_files:
                safe_print("🔄 Optimized extraction order:")
                for i, file_path in enumerate(prioritized_files[:10], 1):  # Show first 10
                    safe_print(f"   {i}. {file_path.name}")
                if len(prioritized_files) > 10:
                    safe_print(f"   ... and {len(prioritized_files) - 10} more files")
        else:
            # Use original group-based processing
            prioritized_files = []
            for group_files in priority_groups.values():
                prioritized_files.extend(group_files)
        
        # Process each group in priority_groups, but prioritize groups with partial archives first
        groups_to_process = list(priority_groups.items())
        
        safe_print(f"\n🔍 Analyzing groups for partial archive priority... | 分析组以确定部分压缩文件优先级...")
        
        # Sort groups to prioritize those containing partial archives
        def group_priority(group_item):
            group_name, group_files = group_item
            # Check if any file in this group might contain partial archive content
            for file_path in group_files:
                if is_archive_file(file_path):
                    # Quick heuristic checks first
                    file_name = file_path.name.lower()
                    
                    # If filename suggests it might be a single part of something, prioritize it
                    if any(indicator in file_name for indicator in ['11111', 'part', 'vol', 'disc']):
                        safe_print(f"  🧩 Priority: {group_name} might contain partial content: {file_path.name} | 优先级: {group_name} 可能包含部分内容: {file_path.name}")
                        return 0
                    
                    # Try actual detection with very short timeout
                    try:
                        # Use ASCII temp path for the detection to avoid encoding issues
                        temp_file, needs_cleanup = get_ascii_temp_path(file_path)
                        try:
                            is_partial, base_name = is_partial_archive(temp_file)
                            if is_partial:
                                safe_print(f"  🧩 Priority: {group_name} contains partial archive: {file_path.name} | 优先级: {group_name} 包含部分压缩文件: {file_path.name}")
                                return 0  # High priority for partial archives
                        finally:
                            if needs_cleanup and temp_file.exists():
                                try:
                                    temp_file.unlink()
                                except Exception:
                                    pass
                    except Exception as e:
                        safe_print(f"  ⚠️ Error checking {file_path.name}: {e} | 检查时出错 {file_path.name}: {e}")
                        # If we can't check, but the name suggests partial content, prioritize anyway
                        if any(indicator in file_name for indicator in ['11111', 'part', 'vol']):
                            return 0
                        continue
            return 1  # Lower priority for regular archives
        
        groups_to_process.sort(key=group_priority)
        
        for group_name, group_files in groups_to_process:
            safe_print(f"\n📦 Processing group: {group_name} | 处理组: {group_name}")
            safe_print("-" * 40)
            
            # Check if this is a subfolder group (all files in same subfolder)
            if "_subfolder_all" in group_name:
                # This is a subfolder group - process all files together
                if process_subfolder_group(group_name, group_files, completed_dir, extraction_result, processed_archives, passwords, root_path, containers_to_cleanup, extracted_parts_to_cleanup):
                    # Subfolder group processed successfully
                    continue
                else:
                    # Subfolder group processing failed, but continue with other groups
                    continue
            
            # Find the main archive to extract
            main_archive = find_main_archive_in_group(group_files)
            
            if not main_archive:
                safe_print(f"  ❌ No main archive found in group | 组中未找到主压缩文件")
                extraction_result.failed_extractions.append((group_name, "No main archive found"))
                continue
            
            # Check if this archive was already processed as a container
            if main_archive in processed_archives:
                safe_print(f"  ⏭️ Archive already processed as container, skipping: {main_archive.name} | 压缩文件已作为容器处理，跳过: {main_archive.name}")
                continue
            
            safe_print(f"  🎯 Main archive: {main_archive.name} | 主压缩文件: {main_archive.name}")
            
            # Check if this is a multi-part archive and if it's complete
            is_multipart = False
            is_complete = False
            base_name = ""
            if re.match(r'.*\.001$', main_archive.name, re.IGNORECASE):
                is_multipart = True
                base_name = re.sub(r'\.001$', '', main_archive.name, flags=re.IGNORECASE)
                
                safe_print(f"  🧩 Detected multi-part archive: {base_name} | 检测到多部分压缩文件: {base_name}")
                
                # Check completeness by scanning the actual directory for all parts
                # This is important because other groups might have extracted additional parts
                archive_dir = main_archive.parent
                all_parts_in_dir = []
                for file_path in archive_dir.iterdir():
                    if file_path.is_file() and base_name.lower() in file_path.name.lower() and re.search(r'\.\d{3}$', file_path.suffix):
                        all_parts_in_dir.append(file_path)
                
                safe_print(f"  🔍 Scanning directory for all parts of {base_name} | 扫描目录中 {base_name} 的所有部分")
                for part_file in all_parts_in_dir:
                    safe_print(f"     Found part: {part_file.name} | 找到部分: {part_file.name}")
                
                # Check completeness using all parts found in directory
                is_complete, found_parts, missing_parts = check_multipart_completeness(all_parts_in_dir, base_name)
                
                if not is_complete:
                    safe_print(f"  ⚠️ Multi-part archive incomplete! Found parts: {found_parts}, Missing: {missing_parts} | 多部分压缩文件不完整！找到部分: {found_parts}，缺少: {missing_parts}")
                    
                    # First, look for missing parts in the same group/path
                    safe_print(f"  🔍 Searching for missing parts in same group first | 首先在同组中搜索缺少的部分")
                    found_in_group = {}
                    
                    for missing_part in missing_parts:
                        expected_name = f"{base_name}.{missing_part:03d}"
                        # Look in the current group files first
                        for group_file in group_files:
                            if group_file.name.lower() == expected_name.lower():
                                found_in_group[missing_part] = group_file
                                safe_print(f"    📄 Found missing part {missing_part:03d} in same group: {group_file.name}")
                                break
                    
                    # Remove parts found in the same group from missing list
                    for found_part in found_in_group.keys():
                        if found_part in missing_parts:
                            missing_parts.remove(found_part)
                    
                    # Update found_parts list
                    found_parts.extend(found_in_group.keys())
                    
                    # If still missing parts, look for them in other archives
                    if missing_parts:
                        safe_print(f"  🔍 Still missing parts: {missing_parts}, searching in other archives | 仍缺少部分: {missing_parts}，在其他压缩文件中搜索")
                        
                        # Look for missing parts in other archives
                        part_locations = find_missing_parts_in_other_archives(missing_parts, base_name, priority_groups)
                        
                        if part_locations:
                            safe_print(f"  🔍 Found missing parts in other archives: | 在其他压缩文件中找到缺少的部分:")
                            for part_num, container_archive in part_locations.items():
                                safe_print(f"     Part {part_num:03d} found in: {container_archive.name} | 部分 {part_num:03d} 在此找到: {container_archive.name}")
                            
                            # Extract the containers to current path to get the missing parts
                            extracted_any_parts = False
                            for part_num, container_archive in part_locations.items():
                                safe_print(f"  📦 Extracting container for part {part_num:03d}: {container_archive.name} | 为部分 {part_num:03d} 解压容器: {container_archive.name}")
                                
                                # Extract container to current path (same directory as main archive)
                                container_extract_dir = main_archive.parent
                                
                                try:
                                    # For container extraction, extract to current path
                                    success, message, password_used = extract_with_7z(
                                        container_archive, container_extract_dir, passwords
                                    )
                                    
                                    if success:
                                        # Track successfully processed archive
                                        extraction_result.successfully_processed_archives.append(container_archive)
                                        
                                        safe_print(f"  ✅ Extracted container successfully to current path | 容器成功解压到当前路径")
                                        extracted_any_parts = True
                                        
                                        # Mark this archive as processed to avoid processing it again later
                                        processed_archives.add(container_archive)
                                        
                                        # Mark this container for cleanup when main extraction succeeds
                                        containers_to_cleanup.add(container_archive)
                                        
                                        if password_used and password_used not in passwords:
                                            passwords.append(password_used)
                                            extraction_result.new_passwords.append(password_used)
                                        
                                        # The missing parts should now be available in the current directory
                                        expected_part_name = f"{base_name}.{part_num:03d}"
                                        expected_part_path = main_archive.parent / expected_part_name
                                        
                                        if expected_part_path.exists():
                                            safe_print(f"  📄 Found extracted missing part: {expected_part_name} | 找到解压的缺少部分: {expected_part_name}")
                                            # Track this extracted part for cleanup
                                            extracted_parts_to_cleanup.add(expected_part_path)
                                        else:
                                            safe_print(f"  ⚠️ Missing part {expected_part_name} not found after extraction | 解压后未找到缺少的部分 {expected_part_name}")
                                    else:
                                        safe_print(f"  ❌ Failed to extract container: {message} | 解压容器失败: {message}")
                                        
                                except Exception as e:
                                    safe_print(f"  ❌ Error extracting container: {e} | 解压容器时出错: {e}")
                            
                            if not extracted_any_parts:
                                safe_print(f"  ❌ Failed to extract any missing parts from containers | 从容器中解压任何缺少部分失败")
                                extraction_result.failed_extractions.append((group_name, "Failed to extract missing parts from containers"))
                                continue
                        else:
                            safe_print(f"  ❌ Missing parts not found in any other archives | 在任何其他压缩文件中都未找到缺少的部分")
                            extraction_result.failed_extractions.append((group_name, f"Multi-part archive incomplete. Missing parts: {missing_parts}"))
                            continue
                    
                    # Re-check completeness after finding parts in group or extracting from containers
                    if found_in_group or (missing_parts and 'part_locations' in locals() and part_locations):
                        safe_print(f"  🔄 Re-checking completeness after finding missing parts... | 找到缺少部分后重新检查完整性...")
                        
                        # Rescan the directory to find all parts (including newly found ones)
                        archive_dir = main_archive.parent
                        all_parts_in_dir = []
                        for file_path in archive_dir.iterdir():
                            if file_path.is_file() and base_name.lower() in file_path.name.lower() and re.search(r'\.\d{3}$', file_path.suffix):
                                all_parts_in_dir.append(file_path)
                        
                        is_complete, found_parts, missing_parts = check_multipart_completeness(all_parts_in_dir, base_name)
                        
                        if is_complete:
                            safe_print(f"  ✅ Multi-part archive is now complete with parts: {found_parts} | 多部分压缩文件现在完整，包含部分: {found_parts}")
                            # Update the group files to include the newly found parts
                            group_files = all_parts_in_dir
                        else:
                            safe_print(f"  ⚠️ Multi-part archive still incomplete. Found parts: {found_parts}, Missing: {missing_parts} | 多部分压缩文件仍不完整。找到部分: {found_parts}，缺少: {missing_parts}")
                            extraction_result.failed_extractions.append((group_name, f"Multi-part archive incomplete. Missing parts: {missing_parts}"))
                            continue
                        
                    else:
                        safe_print(f"  ❌ Missing parts not found in any other archives | 在任何其他压缩文件中都未找到缺少的部分")
                        extraction_result.failed_extractions.append((group_name, f"Multi-part archive incomplete. Missing parts: {missing_parts}"))
                        continue
                else:
                    safe_print(f"  ✅ Multi-part archive is complete with parts: {found_parts} | 多部分压缩文件完整，包含部分: {found_parts}")
                    # Update the group files to include all parts found in directory
                    group_files = all_parts_in_dir
            
            # Create temporary extraction directory
            temp_extract_dir = main_archive.parent / f"temp_extract_{group_name}"
            
            try:
                # Check if this is a partial archive that needs special handling
                # But skip partial archive logic if this is a complete multi-part archive
                is_partial, base_name_partial = is_partial_archive(main_archive)
                
                if is_partial and not (is_multipart and is_complete):
                    # This is a partial archive (not a complete multi-part archive)
                    safe_print(f"  🧩 Detected partial archive content, extracting and reassembling... | 检测到部分压缩文件内容，正在解压和重新组装...")
                    success, message, password_used = extract_partial_archive_and_reassemble(main_archive, temp_extract_dir, passwords)
                else:
                    # Regular archive extraction (including complete multi-part archives)
                    if is_multipart and is_complete:
                        # For multi-part archives, we need to handle all parts together
                        safe_print(f"  🧩 Multi-part archive detected, handling all {len(group_files)} parts together | 检测到多部分压缩文件，正在处理所有 {len(group_files)} 个部分")
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
                    # Track successfully processed archive
                    extraction_result.successfully_processed_archives.append(main_archive)
                    
                    safe_print(f"  ✅ Extracted main archive successfully | 主压缩文件解压成功")
                    
                    # Extract nested archives recursively
                    safe_print(f"  🔄 Checking for nested archives... | 检查嵌套压缩文件...")
                    
                    final_files, new_passwords = extract_nested_archives(temp_extract_dir, passwords)
                    extraction_result.new_passwords.extend(new_passwords)
                    
                    # Determine extraction destination based on content
                    # If the archive contains partial archive files, extract to current path
                    contains_partial_archives = any(
                        re.search(r'\.\d{3}$', f.name) or 'part' in f.name.lower() 
                        for f in final_files if f.is_file()
                    )
                    
                    if contains_partial_archives:
                        safe_print(f"  📦 Archive contains partial files, extracting to current path | 压缩文件包含部分文件，解压到当前路径")
                        # Extract to current path (same directory as the archive)
                        current_extract_dir = main_archive.parent
                        
                        # Copy files directly to the current directory, preserving structure
                        copied_count = 0
                        for file_path in final_files:
                            if file_path.is_file():
                                # Calculate relative path from temp extraction directory
                                try:
                                    rel_path = file_path.relative_to(temp_extract_dir)
                                    dest_path = current_extract_dir / rel_path
                                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(file_path, dest_path)
                                    copied_count += 1
                                except Exception as e:
                                    safe_print(f"  ⚠️ Failed to copy {file_path.name}: {e}")
                        
                        safe_print(f"  ✅ Extracted {copied_count} files to current path | 解压 {copied_count} 个文件到当前路径")
                        extraction_result.completed_files.extend([current_extract_dir / f.relative_to(temp_extract_dir) 
                                                                for f in final_files if f.is_file()])
                    else:
                        # Regular extraction to _Unzipped directory
                        safe_print(f"  📁 Moving final extracted content to _Unzipped folder | 将最终解压内容移动到 _Unzipped 文件夹")
                        
                        # For subfolder groups, move content directly to _Unzipped without group name nesting
                        moved_count = 0
                        
                        # Find the actual content and move it directly to _Unzipped
                        for file_path in final_files:
                            if file_path.is_file():
                                try:
                                    # Get the relative path from temp extraction directory
                                    rel_path = file_path.relative_to(temp_extract_dir)
                                    
                                    # For nested structure like: archive_name/content_folder/files
                                    # We want to extract: content_folder/files directly to _Unzipped
                                    # Skip the archive name part if it exists
                                    if len(rel_path.parts) > 1:
                                        # Check if the first part is the archive name (common pattern)
                                        first_part = rel_path.parts[0]
                                        # If the first part looks like an archive name, skip it
                                        if any(ext in first_part.lower() for ext in ['.7z', '.zip', '.rar']) or first_part.endswith('.7z'):
                                            dest_rel_path = Path(*rel_path.parts[1:]) if len(rel_path.parts) > 1 else Path(rel_path.name)
                                        else:
                                            dest_rel_path = rel_path
                                    else:
                                        # Direct file
                                        dest_rel_path = rel_path
                                    
                                    dest_path = completed_dir / dest_rel_path
                                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(file_path, dest_path)
                                    moved_count += 1
                                except Exception as e:
                                    safe_print(f"  ⚠️ Failed to move {file_path.name}: {e}")
                        
                        safe_print(f"  ✅ Moved {moved_count} files to _Unzipped | 移动了 {moved_count} 个文件到 _Unzipped")
                        # Update the tracking to reflect the new locations
                        extraction_result.completed_files.extend([completed_dir / f.relative_to(temp_extract_dir) 
                                                                for f in final_files if f.is_file()])
                    
                    # Clean up temporary directory
                    if temp_extract_dir.exists():
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                    
                    # Determine if extraction was successful based on whether files were moved/copied
                    extraction_successful = False
                    extracted_file_count = 0
                    
                    if contains_partial_archives:
                        # For partial archives (extracted to current path), check copied_count
                        if 'copied_count' in locals() and copied_count > 0:
                            extraction_successful = True
                            extracted_file_count = copied_count
                    else:
                        # For regular archives (moved to _Unzipped), check moved_count
                        if 'moved_count' in locals() and moved_count > 0:
                            extraction_successful = True
                            extracted_file_count = moved_count
                    
                    if extraction_successful:
                        # Only clean up original files if we have successfully extracted content
                        safe_print(f"  ✅ Valid extraction completed, cleaning up original files | 有效解压完成，清理原始文件")
                        
                        # Clean up original files
                        deleted, failed = clean_up_original_files(group_files)
                        
                        # Debug: Show what we're tracking for cleanup
                        safe_print(f"  🔍 Debug: Containers to cleanup: {len(containers_to_cleanup)} | 容器清理追踪: {len(containers_to_cleanup)}")
                        safe_print(f"  🔍 Debug: Extracted parts to cleanup: {len(extracted_parts_to_cleanup)} | 解压部分清理追踪: {len(extracted_parts_to_cleanup)}")
                        
                        # Also clean up container archives that were used for this group
                        containers_deleted = 0
                        containers_failed = 0
                        for container_archive in containers_to_cleanup:
                            try:
                                if container_archive.exists():
                                    container_archive.unlink()
                                    containers_deleted += 1
                                    safe_print(f"  🗑️  Cleaned up container: {container_archive.name} | 清理容器: {container_archive.name}")
                            except Exception as e:
                                containers_failed += 1
                                safe_print(f"  ❌ Failed to clean up container {container_archive.name}: {e} | 清理容器失败 {container_archive.name}: {e}")
                        
                        # Also clean up extracted parts that were found in containers
                        extracted_parts_deleted = 0
                        extracted_parts_failed = 0
                        for extracted_part in extracted_parts_to_cleanup:
                            try:
                                if extracted_part.exists():
                                    extracted_part.unlink()
                                    extracted_parts_deleted += 1
                                    safe_print(f"  🗑️  Cleaned up extracted part: {extracted_part.name} | 清理解压的部分: {extracted_part.name}")
                            except Exception as e:
                                extracted_parts_failed += 1
                                safe_print(f"  ❌ Failed to clean up extracted part {extracted_part.name}: {e} | 清理解压部分失败 {extracted_part.name}: {e}")
                        
                        # Clean up extracted content folders and temp files in the subfolder
                        subfolder_cleanup_deleted = 0
                        subfolder_cleanup_failed = 0
                        
                        # Get the subfolder path
                        if group_files:
                            subfolder_path = group_files[0].parent
                            
                            # Clean up temp multipart files
                            for temp_file in subfolder_path.glob("temp_multipart_*"):
                                try:
                                    if temp_file.is_file():
                                        temp_file.unlink()
                                        subfolder_cleanup_deleted += 1
                                        safe_print(f"  🗑️  Cleaned up temp file: {temp_file.name} | 清理临时文件: {temp_file.name}")
                                except Exception as e:
                                    subfolder_cleanup_failed += 1
                                    safe_print(f"  ❌ Failed to clean up temp file {temp_file.name}: {e} | 清理临时文件失败 {temp_file.name}: {e}")
                            
                            # Clean up extracted content folders (folders that were created by extraction)
                            for item in subfolder_path.iterdir():
                                if item.is_dir() and not item.name.startswith('.'):
                                    # Check if this is likely an extracted content folder
                                    # (folders that contain many files and weren't there originally)
                                    try:
                                        item_files = list(item.rglob('*'))
                                        if len(item_files) > 10:  # Likely extracted content
                                            shutil.rmtree(item, ignore_errors=True)
                                            if not item.exists():
                                                subfolder_cleanup_deleted += 1
                                                safe_print(f"  🗑️  Cleaned up extracted folder: {item.name} | 清理解压文件夹: {item.name}")
                                            else:
                                                subfolder_cleanup_failed += 1
                                    except Exception as e:
                                        subfolder_cleanup_failed += 1
                                        safe_print(f"  ❌ Failed to clean up folder {item.name}: {e} | 清理文件夹失败 {item.name}: {e}")
                        
                        total_deleted = deleted + containers_deleted + extracted_parts_deleted + subfolder_cleanup_deleted
                        total_failed = failed + containers_failed + extracted_parts_failed + subfolder_cleanup_failed
                        safe_print(f"  🗑️  Cleaned up: {total_deleted} files deleted, {total_failed} failed | 清理完成: {total_deleted} 个文件已删除，{total_failed} 个失败")
                        
                        extraction_result.successful_extractions.append((group_name, extracted_file_count))
                    else:
                        safe_print(f"  ❌ No valid files extracted (only temporary files found) | 未解压出有效文件（仅找到临时文件）")
                        safe_print(f"  🔄 Preserving original files due to failed extraction | 由于解压失败保留原始文件")
                        extraction_result.failed_extractions.append((group_name, "No valid files extracted (only temporary files)"))
                        
                        # Only clean up temp files, but preserve original archive files
                        if group_files:
                            subfolder_path = group_files[0].parent
                            temp_cleanup_count = 0
                            
                            # Clean up only temp multipart files
                            for temp_file in subfolder_path.glob("temp_multipart_*"):
                                try:
                                    if temp_file.is_file():
                                        temp_file.unlink()
                                        temp_cleanup_count += 1
                                        safe_print(f"  🗑️  Cleaned up temp file: {temp_file.name} | 清理临时文件: {temp_file.name}")
                                except Exception as e:
                                    safe_print(f"  ❌ Failed to clean up temp file {temp_file.name}: {e} | 清理临时文件失败 {temp_file.name}: {e}")
                            
                            if temp_cleanup_count > 0:
                                safe_print(f"  🗑️  Cleaned up: {temp_cleanup_count} temp files, preserved original files | 清理完成: {temp_cleanup_count} 个临时文件，保留原始文件")
                    
                    # Track subfolder for cleanup if this group represents a subfolder
                    if not group_name.startswith("root_"):
                        # Extract subfolder name from group name (format: {folder_name}_{subgroup_name})
                        subfolder_name = group_name.split('_')[0]
                        if subfolder_name:
                            processed_subfolders.add(subfolder_name)
                    
                else:
                    # Error message is already cleaned by the extraction function
                    safe_print(f"  ❌ Extraction failed: {message}")
                    extraction_result.failed_extractions.append((group_name, message))
                    
                    # Clean up failed extraction directory
                    if temp_extract_dir.exists():
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                
            except Exception as e:
                safe_print(f"  ❌ Error processing group: {e} | 处理组时出错: {e}")
                extraction_result.failed_extractions.append((group_name, str(e)))
                
                # Clean up on error
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)
        
        # Save new passwords to password book
        if extraction_result.new_passwords:
            save_new_passwords(passwords_file, extraction_result.new_passwords)
        
        # Clean up successfully processed subfolders
        if processed_subfolders:
            safe_print(f"\n🗂️  Cleaning up successfully processed subfolders... | 清理成功处理的子文件夹...")
            subfolder_deleted = 0
            subfolder_failed = 0
            
            for subfolder_name in processed_subfolders:
                subfolder_path = root_path / subfolder_name
                if subfolder_path.exists() and subfolder_path.is_dir():
                    try:
                        # Check if subfolder is empty or only contains files we've processed
                        remaining_files = list(subfolder_path.rglob('*'))
                        remaining_files = [f for f in remaining_files if f.is_file()]
                        
                        if not remaining_files:
                            # Subfolder is empty, safe to delete
                            shutil.rmtree(subfolder_path)
                            subfolder_deleted += 1
                            safe_print(f"  🗑️  Deleted empty subfolder: {subfolder_name} | 删除空子文件夹: {subfolder_name}")
                        else:
                            safe_print(f"  ⚠️  Subfolder {subfolder_name} still contains {len(remaining_files)} files - skipping deletion | 子文件夹 {subfolder_name} 仍包含 {len(remaining_files)} 个文件 - 跳过删除")
                    except Exception as e:
                        subfolder_failed += 1
                        safe_print(f"  ❌ Failed to delete subfolder {subfolder_name}: {e} | 删除子文件夹失败 {subfolder_name}: {e}")
            
            if subfolder_deleted > 0 or subfolder_failed > 0:
                safe_print(f"  🗂️  Subfolder cleanup: {subfolder_deleted} deleted, {subfolder_failed} failed | 子文件夹清理: {subfolder_deleted} 个已删除，{subfolder_failed} 个失败")
        
        # Display final results
        display_extraction_results(extraction_result)
        
        # Step 3: Organize extracted files and cleanup archives
        if extraction_result.successful_extractions:
            safe_print("\n" + "=" * 60)
            safe_print("📁 ORGANIZING AND CLEANING UP | 整理和清理")
            safe_print("=" * 60)
            
            # Use the completed_files from extraction_result
            all_extracted_files = extraction_result.completed_files
            
            # Get successfully processed archives for cleanup
            archive_files_to_cleanup = extraction_result.successfully_processed_archives.copy()
            
            # Add archives from the containers and parts tracking
            archive_files_to_cleanup.extend(containers_to_cleanup)
            archive_files_to_cleanup.extend(extracted_parts_to_cleanup)
            
            # Also add archives from processed_archives set
            archive_files_to_cleanup.extend(processed_archives)
            
            # Remove duplicates and ensure they exist
            unique_archives = []
            seen = set()
            for archive_path in archive_files_to_cleanup:
                archive_path = Path(archive_path)  # Ensure it's a Path object
                if archive_path not in seen and archive_path.exists():
                    seen.add(archive_path)
                    unique_archives.append(archive_path)
            
            # Perform organization and cleanup
            success = organize_and_cleanup(
                extracted_files=all_extracted_files,
                archive_files=unique_archives,
                root_path=root_path,
                verbose=verbose
            )
            
            if success:
                # Create extraction summary
                unzipped_dir = root_path / "_Unzipped"
                moved_files = list(unzipped_dir.rglob('*')) if unzipped_dir.exists() else []
                moved_files = [f for f in moved_files if f.is_file()]
                
                create_extraction_summary(
                    moved_files=moved_files,
                    cleaned_archives=unique_archives,
                    unzipped_dir=unzipped_dir
                )
        else:
            safe_print("\n⚠️  No successful extractions to organize | 没有成功的解压文件需要整理")
        
    elif not no_extract and dry_run:
        safe_print("\n💡 Extraction not performed in dry-run mode | 预演模式下不执行解压")
        safe_print("💡 Use without --dry-run to perform actual extraction | 不使用 --dry-run 执行实际解压")
    elif no_extract:
        safe_print("\n💡 Extraction skipped (--no-extract specified) | 跳过解压（指定了 --no-extract）")
        
        # Still perform multi-part analysis for informational purposes
        safe_print("\n" + "=" * 60)
        safe_print("📊 MULTI-PART ARCHIVE ANALYSIS | 多部分压缩文件分析")
        safe_print("=" * 60)
        multipart_archives, potential_missing_containers = check_archive_completeness(all_files, verbose)
    
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
