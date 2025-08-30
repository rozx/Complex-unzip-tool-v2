"""File renaming utilities for restoring cloaked archive files."""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional


def detect_cloaked_files(files: List[Path]) -> Dict[Path, Path]:
    """Detect cloaked archive files and determine their original names.
    
    Args:
        files: List of file paths to analyze
        
    Returns:
        Dictionary mapping current file path to suggested original file path
    """
    rename_suggestions = {}
    
    # Common cloaking patterns
    cloaking_patterns = [
        # Pattern: *.001删 -> *.001
        (r'\.(\d{3})删$', r'.\1'),
        # Pattern: *.001删除 -> *.001
        (r'\.(\d{3})删除$', r'.\1'),
        # Pattern: *.7z删 -> *.7z
        (r'\.7z删$', r'.7z'),
        # Pattern: *.7z删除 -> *.7z
        (r'\.7z删除$', r'.7z'),
        # Pattern: *.zip删 -> *.zip
        (r'\.zip删$', r'.zip'),
        # Pattern: *.rar删 -> *.rar
        (r'\.rar删$', r'.rar'),
        # Pattern: *删.001 -> *.001
        (r'删\.(\d{3})$', r'.\1'),
        # Pattern: *删除.001 -> *.001
        (r'删除\.(\d{3})$', r'.\1'),
        # Pattern: *.part001删 -> *.part001
        (r'\.part(\d{3})删$', r'.part\1'),
        # Pattern: *.z01删 -> *.z01
        (r'\.z(\d{2})删$', r'.z\1'),
        # Pattern: remove trailing 删 or 删除
        (r'删除?$', r''),
    ]
    
    for file_path in files:
        original_name = file_path.name
        suggested_name = original_name
        
        # Try each pattern
        for pattern, replacement in cloaking_patterns:
            if re.search(pattern, suggested_name, re.IGNORECASE):
                suggested_name = re.sub(pattern, replacement, suggested_name, flags=re.IGNORECASE)
                break
        
        # Only suggest rename if the name actually changed and looks like an archive
        if suggested_name != original_name and _is_archive_like(suggested_name):
            suggested_path = file_path.parent / suggested_name
            # Check if target doesn't already exist
            if not suggested_path.exists():
                rename_suggestions[file_path] = suggested_path
    
    return rename_suggestions


def _is_archive_like(filename: str) -> bool:
    """Check if a filename looks like an archive file.
    
    Args:
        filename: The filename to check
        
    Returns:
        True if the filename appears to be an archive
    """
    archive_patterns = [
        r'\.\d{3}$',  # .001, .002, etc.
        r'\.7z$',     # .7z
        r'\.zip$',    # .zip
        r'\.rar$',    # .rar
        r'\.part\d+$', # .part001
        r'\.z\d{2}$', # .z01, .z02
    ]
    
    for pattern in archive_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    
    return False


def rename_cloaked_files(rename_suggestions: Dict[Path, Path], dry_run: bool = True) -> Tuple[List[Path], List[str]]:
    """Rename cloaked files to their original names.
    
    Args:
        rename_suggestions: Dictionary mapping current paths to target paths
        dry_run: If True, only simulate the renaming (don't actually rename)
        
    Returns:
        Tuple of (successfully_renamed_files, error_messages)
    """
    successful_renames = []
    error_messages = []
    
    if not rename_suggestions:
        return successful_renames, error_messages
    
    print(f"\n🔧 {'[DRY RUN] Simulating automatic' if dry_run else 'Performing automatic'} file renaming | "
          f"{'[预演] 模拟自动' if dry_run else '执行自动'}文件重命名")
    print("-" * 50)
    
    for current_path, target_path in rename_suggestions.items():
        try:
            print(f"{'🔍' if dry_run else '✏️ '} {current_path.name} → {target_path.name}")
            
            if not dry_run:
                current_path.rename(target_path)
                successful_renames.append(target_path)
            else:
                successful_renames.append(current_path)  # For dry run, keep original path
                
        except Exception as e:
            error_msg = f"❌ Failed to rename {current_path.name}: {e} | 重命名失败 {current_path.name}: {e}"
            error_messages.append(error_msg)
            print(error_msg)
    
    if successful_renames:
        count = len(successful_renames)
        if dry_run:
            print(f"\n🔍 [DRY RUN] Would rename {count} files automatically | [预演] 将自动重命名 {count} 个文件")
            print(f"💡 Run without --dry-run to perform actual renaming | 不使用 --dry-run 运行以执行实际重命名")
        else:
            print(f"\n✅ Successfully renamed {count} files automatically | 成功自动重命名 {count} 个文件")
    
    if error_messages:
        print(f"\n⚠️  {len(error_messages)} errors occurred | 发生了 {len(error_messages)} 个错误")
    
    return successful_renames, error_messages


def display_rename_suggestions(rename_suggestions: Dict[Path, Path]) -> None:
    """Display the rename suggestions in a user-friendly format.
    
    Args:
        rename_suggestions: Dictionary mapping current paths to target paths
    """
    if not rename_suggestions:
        return
    
    print(f"\n📝 Detected {len(rename_suggestions)} cloaked files (will be renamed automatically) | "
          f"检测到 {len(rename_suggestions)} 个伪装文件（将自动重命名）:")
    print("-" * 50)
    
    for current_path, target_path in rename_suggestions.items():
        print(f"🔧 {current_path.name}")
        print(f"   → {target_path.name}")
        print(f"   📁 {current_path.parent}")
        print()


def group_rename_suggestions_by_directory(rename_suggestions: Dict[Path, Path]) -> Dict[Path, Dict[Path, Path]]:
    """Group rename suggestions by their parent directory.
    
    Args:
        rename_suggestions: Dictionary mapping current paths to target paths
        
    Returns:
        Dictionary mapping directory paths to their rename suggestions
    """
    grouped = {}
    
    for current_path, target_path in rename_suggestions.items():
        parent_dir = current_path.parent
        if parent_dir not in grouped:
            grouped[parent_dir] = {}
        grouped[parent_dir][current_path] = target_path
    
    return grouped
