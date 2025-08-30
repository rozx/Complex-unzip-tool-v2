"""Display utilities for the Complex Unzip Tool."""

from pathlib import Path
from typing import Dict, List


def display_file_groups(priority_groups: Dict[str, List[Path]], 
                       verbose: bool = False) -> None:
    """Display the grouped files in a unified format.
    
    Args:
        priority_groups: Files grouped by priority (main display)
        verbose: Whether to show detailed information
    """
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
        elif "_multipart_" in group_name:
            # Multi-part archive in subfolder (e.g., "森系_multipart_森系.7z")
            parts = group_name.split("_multipart_")
            folder_name = parts[0]
            archive_name = parts[1] if len(parts) > 1 else "archive"
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
        elif "_single_" in group_name:
            # Single file in subfolder (e.g., "森系_single_11111")
            parts = group_name.split("_single_")
            folder_name = parts[0]
            file_name = parts[1] if len(parts) > 1 else "file"
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
