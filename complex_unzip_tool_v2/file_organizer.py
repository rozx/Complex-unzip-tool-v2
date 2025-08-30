"""File organization and cleanup utilities."""

import shutil
import os
from pathlib import Path
from typing import List, Set, Optional, Tuple
from .console_utils import safe_print


def create_unzipped_folder(root_path: Path) -> Path:
    """Create the _Unzipped folder in the root path.
    
    Args:
        root_path: The root directory where _Unzipped folder should be created
        
    Returns:
        Path to the created _Unzipped folder
    """
    unzipped_dir = root_path / "_Unzipped"
    unzipped_dir.mkdir(exist_ok=True)
    return unzipped_dir


def move_extracted_files_to_unzipped(extracted_files: List[Path], root_path: Path, verbose: bool = False) -> List[Path]:
    """Move extracted files to the _Unzipped folder.
    
    Args:
        extracted_files: List of extracted file/folder paths
        root_path: The root directory containing the _Unzipped folder
        verbose: Whether to show detailed information
        
    Returns:
        List of successfully moved file paths in the _Unzipped folder
    """
    if not extracted_files:
        return []
    
    unzipped_dir = create_unzipped_folder(root_path)
    moved_files = []
    
    safe_print(f"\n📁 Moving {len(extracted_files)} extracted items to _Unzipped folder | 将 {len(extracted_files)} 个解压项移动到 _Unzipped 文件夹")
    safe_print("-" * 50)
    
    for extracted_path in extracted_files:
        try:
            if not extracted_path.exists():
                if verbose:
                    safe_print(f"⚠️  Skipping non-existent path: {extracted_path.name}")
                continue
            
            # Determine destination path, preserving original folder structure under root
            # Final layout: _Unzipped/<root_folder_name>/<relative_path_from_root>
            # Example: E:\Root\Sub\file.ext -> E:\Root\_Unzipped\Root\Sub\file.ext
            try:
                rel_parent = extracted_path.parent.relative_to(root_path)
                # Always include the root folder name to ensure nesting
                if str(rel_parent) == ".":
                    nested_dir = Path(root_path.name)
                else:
                    nested_dir = Path(root_path.name) / rel_parent
            except ValueError:
                # If path is outside root (unexpected), fallback to using its immediate folder under root name
                nested_dir = Path(root_path.name) / extracted_path.parent.name

            destination_dir = unzipped_dir / nested_dir
            destination_dir.mkdir(parents=True, exist_ok=True)
            destination = destination_dir / extracted_path.name
            
            # Handle name conflicts
            counter = 1
            original_destination = destination
            while destination.exists():
                if extracted_path.is_file():
                    stem = original_destination.stem
                    suffix = original_destination.suffix
                    destination = unzipped_dir / f"{stem}_{counter}{suffix}"
                else:
                    destination = unzipped_dir / f"{original_destination.name}_{counter}"
                counter += 1
            
            # Move the file or directory
            if extracted_path.is_file():
                shutil.move(str(extracted_path), str(destination))
                if verbose:
                    safe_print(f"  📄 Moved file: {extracted_path.name} → {destination.name}")
            elif extracted_path.is_dir():
                # For a directory, place it under the preserved nested_dir
                destination = destination_dir / extracted_path.name
                shutil.move(str(extracted_path), str(destination))
                if verbose:
                    safe_print(f"  📁 Moved folder: {extracted_path.name} → {destination.name}")
            
            moved_files.append(destination)
            
        except Exception as e:
            safe_print(f"  ❌ Failed to move {extracted_path.name}: {str(e)}")
    
    safe_print(f"✅ Successfully moved {len(moved_files)} items to _Unzipped | 成功移动 {len(moved_files)} 个项目到 _Unzipped")
    return moved_files


def cleanup_archive_files(archive_files: List[Path], verbose: bool = False) -> Tuple[List[Path], List[str]]:
    """Clean up successfully processed archive files.
    
    Args:
        archive_files: List of archive file paths to clean up
        verbose: Whether to show detailed information
        
    Returns:
        Tuple of (successfully_removed_files, error_messages)
    """
    if not archive_files:
        return [], []
    
    safe_print(f"\n🧹 Cleaning up {len(archive_files)} processed archive files | 清理 {len(archive_files)} 个已处理的压缩文件")
    safe_print("-" * 50)
    
    removed_files = []
    errors = []
    
    for archive_path in archive_files:
        try:
            if archive_path.exists():
                if archive_path.is_file():
                    archive_path.unlink()
                    removed_files.append(archive_path)
                    if verbose:
                        safe_print(f"  🗑️  Removed archive: {archive_path.name}")
                elif archive_path.is_dir():
                    shutil.rmtree(str(archive_path))
                    removed_files.append(archive_path)
                    if verbose:
                        safe_print(f"  🗑️  Removed directory: {archive_path.name}")
            else:
                if verbose:
                    safe_print(f"  ⚠️  Already removed: {archive_path.name}")
        except Exception as e:
            error_msg = f"Failed to remove {archive_path.name}: {str(e)}"
            errors.append(error_msg)
            safe_print(f"  ❌ {error_msg}")
    
    if removed_files:
        safe_print(f"✅ Successfully cleaned up {len(removed_files)} files/folders | 成功清理 {len(removed_files)} 个文件/文件夹")
    
    if errors:
        safe_print(f"⚠️  {len(errors)} cleanup errors occurred | 发生 {len(errors)} 个清理错误")
    
    return removed_files, errors


def cleanup_empty_directories(root_path: Path, exclude_dirs: Optional[Set[str]] = None, verbose: bool = False) -> List[Path]:
    """Remove empty directories after successful extraction and cleanup.
    
    Args:
        root_path: The root directory to clean up empty folders from
        exclude_dirs: Set of directory names to exclude from cleanup (e.g., {'_Unzipped'})
        verbose: Whether to show detailed information
        
    Returns:
        List of removed directory paths
    """
    if exclude_dirs is None:
        exclude_dirs = {'_Unzipped', '.git', '.svn', '__pycache__'}
    
    removed_dirs = []
    
    # Walk through directories bottom-up to remove empty ones
    for dir_path in sorted(root_path.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if not dir_path.is_dir():
            continue
            
        if dir_path.name in exclude_dirs:
            continue
            
        if dir_path == root_path:
            continue  # Don't remove the root directory itself
            
        try:
            # Check if directory is empty
            if not any(dir_path.iterdir()):
                dir_path.rmdir()
                removed_dirs.append(dir_path)
                if verbose:
                    safe_print(f"  🗑️  Removed empty directory: {dir_path.relative_to(root_path)}")
        except OSError:
            # Directory not empty or permission error
            continue
        except Exception as e:
            if verbose:
                safe_print(f"  ⚠️  Could not remove directory {dir_path.name}: {str(e)}")
    
    if removed_dirs:
        safe_print(f"🧹 Removed {len(removed_dirs)} empty directories | 移除了 {len(removed_dirs)} 个空目录")
    
    return removed_dirs


def organize_and_cleanup(extracted_files: List[Path], archive_files: List[Path], root_path: Path, verbose: bool = False) -> bool:
    """Organize extracted files and clean up archives after successful extraction.
    
    Args:
        extracted_files: List of successfully extracted file/folder paths
        archive_files: List of archive files that were successfully processed
        root_path: The root directory for organization
        verbose: Whether to show detailed information
        
    Returns:
        True if organization and cleanup was successful, False otherwise
    """
    success = True
    
    try:
        # Step 1: Move extracted files to _Unzipped folder
        if extracted_files:
            moved_files = move_extracted_files_to_unzipped(extracted_files, root_path, verbose)
            if len(moved_files) != len(extracted_files):
                safe_print("⚠️  Some files could not be moved to _Unzipped folder | 部分文件无法移动到 _Unzipped 文件夹")
                success = False
        
        # Step 2: Clean up processed archive files
        if archive_files:
            removed_files, cleanup_errors = cleanup_archive_files(archive_files, verbose)
            if cleanup_errors:
                safe_print("⚠️  Some archive files could not be cleaned up | 部分压缩文件无法清理")
                success = False
        
        # Step 3: Clean up empty directories
        removed_dirs = cleanup_empty_directories(root_path, verbose=verbose)
        
        if success:
            safe_print("\n✅ Organization and cleanup completed successfully! | 整理和清理成功完成！")
        else:
            safe_print("\n⚠️  Organization and cleanup completed with some issues | 整理和清理完成但存在一些问题")
        
        return success
        
    except Exception as e:
        safe_print(f"\n❌ Organization and cleanup failed: {str(e)} | 整理和清理失败: {str(e)}")
        return False


def create_extraction_summary(moved_files: List[Path], cleaned_archives: List[Path], unzipped_dir: Path) -> None:
    """Create a summary of the extraction and organization process.
    
    Args:
        moved_files: List of files moved to _Unzipped folder
        cleaned_archives: List of cleaned up archive files
        unzipped_dir: Path to the _Unzipped folder
    """
    safe_print("\n" + "=" * 60)
    safe_print("📊 EXTRACTION SUMMARY | 解压摘要")
    safe_print("=" * 60)
    
    safe_print(f"📁 Extracted files location | 解压文件位置: {unzipped_dir}")
    safe_print(f"📄 Total extracted items | 解压项目总数: {len(moved_files)}")
    safe_print(f"🗑️  Cleaned archive files | 已清理压缩文件: {len(cleaned_archives)}")
    
    # Show only a small preview to keep console output concise
    if moved_files:
        preview_count = 10
        preview = sorted(moved_files)[:preview_count]
        safe_print(f"\n📋 Extracted items (first {len(preview)} shown) | 解压项目（仅显示前 {len(preview)} 个）:")
        for item in preview:
            item_type = "📁" if item.is_dir() else "📄"
            safe_print(f"   {item_type} {item.name}")
        remaining = len(moved_files) - len(preview)
        if remaining > 0:
            safe_print(f"   … and {remaining} more | 以及另外 {remaining} 个 …")
            safe_print(f"   ▶ Browse: {unzipped_dir}")
    
    safe_print(f"\n✅ All operations completed successfully! | 所有操作成功完成！")
    safe_print("=" * 60)
