"""Display utilities for the Complex Unzip Tool."""

from pathlib import Path
from typing import Dict, List


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
        if group_name.endswith("_subfolder"):
            # Subfolder group (all files from one subfolder)
            folder_name = group_name.replace("_subfolder", "")
            icon = "📁"
            display_name = f"{folder_name} (subfolder | 子文件夹)"
        elif group_name.startswith("root_multipart_"):
            # Multi-part archive in root
            archive_name = group_name.replace("root_multipart_", "")
            icon = "📦"
            display_name = f"{archive_name} (multi-part | 多部分)"
        elif group_name.startswith("root_similar_"):
            # Similar files in root
            base_name = group_name.replace("root_similar_", "")
            icon = "📋"
            display_name = f"{base_name} (similar files | 相似文件)"
        elif group_name.startswith("root_single_"):
            # Single file in root
            file_name = group_name.replace("root_single_", "")
            icon = "📄"
            display_name = f"{file_name} (single file | 单个文件)"
        else:
            # Fallback
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
