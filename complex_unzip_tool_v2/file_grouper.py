"""File grouping utilities for the Complex Unzip Tool."""

import re
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from .filename_utils import extract_base_name, normalize_filename, calculate_similarity


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


def group_files_by_priority(files: List[Path], root_path: Path) -> Dict[str, List[Path]]:
    """Group files with root-aware priority:
    1. Subfolders from root: all files in subfolder = one group
    2. Files in root: group by filename similarity
    
    Args:
        files: List of file paths
        root_path: The root path being processed
        
    Returns:
        Dictionary mapping group names to lists of files
    """
    groups = {}
    group_counter = 0
    
    # Separate root files from subfolder files
    root_files = []
    subfolder_files = defaultdict(list)
    
    for file_path in files:
        try:
            # Try to find if this file is under root_path
            relative_path = file_path.relative_to(root_path)
            
            if len(relative_path.parts) == 1:
                # File is directly in root
                root_files.append(file_path)
            else:
                # File is in a subfolder - find the immediate subfolder under root
                immediate_subfolder = root_path / relative_path.parts[0]
                subfolder_files[immediate_subfolder].append(file_path)
        except ValueError:
            # File is not under root_path, treat as root file
            root_files.append(file_path)
    
    # Group subfolder files - but analyze each subfolder's contents properly
    for subfolder, subfolder_file_list in subfolder_files.items():
        folder_name = subfolder.name
        
        # Instead of grouping all files in subfolder together,
        # analyze the subfolder's files for proper archive grouping
        subfolder_groups = group_files_by_similarity(subfolder_file_list)
        
        for subgroup_name, file_list in subfolder_groups.items():
            # Prefix with subfolder name to avoid conflicts
            group_name = f"{folder_name}_{subgroup_name}"
            groups[group_name] = file_list
    
    # Group root files by filename similarity
    if root_files:
        root_groups = group_files_by_similarity(root_files)
        for group_name, file_list in root_groups.items():
            groups[f"root_{group_name}"] = file_list
    
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
    
    # First, detect multi-part archives
    base_name_groups = defaultdict(list)
    remaining_files = []
    
    for file_path in files:
        base_name = extract_base_name(file_path.name)
        original_name = file_path.name
        
        # Enhanced multi-part archive detection
        is_multipart = (
            # Standard patterns: .7z.001, .rar.002, .zip.003
            re.search(r'\.(7z|rar|zip)\.\d+', original_name, re.IGNORECASE) or
            # Generic numbered patterns: .001, .002, .003
            re.search(r'\.\d{3}', original_name) or
            # Archive-like with numbers: "16.7z - Copy.001删", "file.part01"
            re.search(r'(7z|rar|zip|part|vol).*\.\d+', original_name, re.IGNORECASE) or
            # Any file with numbers that might be cloaked: "name.001删", "file_1"
            re.search(r'[\s._-]\d+', original_name) or
            # Files where base_name differs significantly from original (indicating processing)
            (len(base_name) < len(Path(original_name).stem) * 0.8)
        )
        
        if is_multipart:
            base_name_groups[base_name].append(file_path)
        else:
            remaining_files.append(file_path)
    
    # Create groups for multi-part archives
    for base_name, archive_files in base_name_groups.items():
        if len(archive_files) > 1:
            # Multiple parts of the same archive
            group_name = f"multipart_{base_name}"
            groups[group_name] = sorted(archive_files, key=lambda x: x.name)
            used_files.update(archive_files)
        else:
            # Single part, add to remaining files for similarity grouping
            remaining_files.extend(archive_files)
    
    # Group remaining files by similarity
    for file_path in remaining_files:
        if file_path in used_files:
            continue
            
        similar_group = [file_path]
        used_files.add(file_path)
        
        # Find similar files
        for other_file in remaining_files:
            if other_file in used_files or other_file == file_path:
                continue
                
            similarity = calculate_similarity(
                normalize_filename(file_path.name),
                normalize_filename(other_file.name)
            )
            
            if similarity >= threshold:
                similar_group.append(other_file)
                used_files.add(other_file)
        
        if len(similar_group) > 1:
            # Multiple similar files
            base_name = normalize_filename(file_path.stem)
            group_name = f"similar_{base_name}"
            groups[group_name] = sorted(similar_group, key=lambda x: x.name)
        else:
            # Single file
            group_name = f"single_{normalize_filename(file_path.stem)}"
            groups[group_name] = similar_group
    
    return groups
