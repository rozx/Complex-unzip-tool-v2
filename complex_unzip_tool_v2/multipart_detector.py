"""Multi-part archive completeness detection utilities."""

import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from .console_utils import safe_print


class MultiPartArchive:
    """Represents a multi-part archive with its parts and status."""
    
    def __init__(self, base_name: str, expected_parts: Set[int], found_parts: Dict[int, Path]):
        self.base_name = base_name
        self.expected_parts = expected_parts
        self.found_parts = found_parts
        self.missing_parts = expected_parts - set(found_parts.keys())
        self.is_complete = len(self.missing_parts) == 0
        
    def get_ordered_parts(self) -> List[Path]:
        """Get parts in numerical order."""
        return [self.found_parts[i] for i in sorted(self.found_parts.keys())]
    
    def get_missing_part_numbers(self) -> List[int]:
        """Get missing part numbers in order."""
        return sorted(self.missing_parts)


def detect_multipart_patterns(files: List[Path]) -> List[MultiPartArchive]:
    """Detect multi-part archive patterns and check completeness.
    
    Args:
        files: List of file paths to analyze
        
    Returns:
        List of MultiPartArchive objects representing detected multi-part archives
    """
    # Group files by base name patterns
    pattern_groups = defaultdict(list)
    
    for file_path in files:
        file_name = file_path.name
        
        # Pattern 1: filename.ext.001, filename.ext.002, etc.
        match = re.match(r'^(.+\.[^.]+)\.(\d{3})$', file_name, re.IGNORECASE)
        if match:
            base_name = match.group(1)
            part_num = int(match.group(2))
            pattern_groups[f"ext3_{base_name}"].append((part_num, file_path))
            continue
            
        # Pattern 2: filename.001, filename.002, etc.
        match = re.match(r'^(.+)\.(\d{3})$', file_name, re.IGNORECASE)
        if match:
            base_name = match.group(1)
            part_num = int(match.group(2))
            pattern_groups[f"num3_{base_name}"].append((part_num, file_path))
            continue
            
        # Pattern 3: filename.part1, filename.part2, etc.
        match = re.match(r'^(.+)\.part(\d+)$', file_name, re.IGNORECASE)
        if match:
            base_name = match.group(1)
            part_num = int(match.group(2))
            pattern_groups[f"part_{base_name}"].append((part_num, file_path))
            continue
            
        # Pattern 4: filename.z01, filename.z02, etc.
        match = re.match(r'^(.+)\.z(\d{2})$', file_name, re.IGNORECASE)
        if match:
            base_name = match.group(1)
            part_num = int(match.group(2))
            pattern_groups[f"z_{base_name}"].append((part_num, file_path))
            continue
            
        # Pattern 5: filename.vol001, filename.vol002, etc.
        match = re.match(r'^(.+)\.vol(\d{3})$', file_name, re.IGNORECASE)
        if match:
            base_name = match.group(1)
            part_num = int(match.group(2))
            pattern_groups[f"vol_{base_name}"].append((part_num, file_path))
            continue
    
    # Analyze each pattern group
    multipart_archives = []
    
    for pattern_key, parts_list in pattern_groups.items():
        if len(parts_list) < 2:
            continue  # Need at least 2 parts to be considered multi-part
            
        # Extract actual base name (remove pattern prefix)
        actual_base_name = pattern_key.split('_', 1)[1]
        
        # Create mapping of part numbers to file paths
        found_parts = {part_num: file_path for part_num, file_path in parts_list}
        part_numbers = set(found_parts.keys())
        
        # Determine expected range based on the pattern
        min_part = min(part_numbers)
        max_part = max(part_numbers)
        
        # For most patterns, we expect consecutive numbering
        # If we have consecutive parts, assume the sequence is complete
        expected_parts = set(range(min_part, max_part + 1))
        
        # Check if the parts are consecutive
        actual_consecutive = set(range(min_part, max_part + 1))
        if part_numbers == actual_consecutive:
            # We have consecutive parts, consider this complete
            expected_parts = part_numbers
        else:
            # We have gaps in the sequence, expected parts should fill the gaps
            expected_parts = actual_consecutive
        
        # Create MultiPartArchive object
        multipart_archive = MultiPartArchive(
            base_name=actual_base_name,
            expected_parts=expected_parts,
            found_parts=found_parts
        )
        
        multipart_archives.append(multipart_archive)
    
    return multipart_archives


def find_missing_parts_in_group(multipart_archive: MultiPartArchive, all_files: List[Path]) -> List[Path]:
    """Find missing parts of a multi-part archive within the same file group/directory.
    
    Args:
        multipart_archive: The multi-part archive to find missing parts for
        all_files: All available files in the current processing group
        
    Returns:
        List of file paths that might contain the missing parts
    """
    if multipart_archive.is_complete:
        return []
    
    missing_parts = []
    base_name = multipart_archive.base_name
    
    # Get the directory of existing parts
    if multipart_archive.found_parts:
        reference_dir = next(iter(multipart_archive.found_parts.values())).parent
    else:
        return []
    
    # Look for files in the same directory that might contain missing parts
    for file_path in all_files:
        if file_path.parent != reference_dir:
            continue
            
        file_name = file_path.name
        
        # Check if this file might contain the missing parts
        # Look for patterns that suggest archive content
        if any(keyword in file_name.lower() for keyword in [
            'part', 'vol', 'disc', 'archive', 'backup', 'data'
        ]):
            # Skip if this file is already identified as a part of this archive
            if file_path not in multipart_archive.found_parts.values():
                missing_parts.append(file_path)
    
    return missing_parts


def check_archive_completeness(files: List[Path], verbose: bool = False) -> Tuple[List[MultiPartArchive], List[Path]]:
    """Check completeness of multi-part archives in the given files.
    
    Args:
        files: List of file paths to analyze
        verbose: Whether to show detailed information
        
    Returns:
        Tuple of (detected_multipart_archives, potential_missing_part_containers)
    """
    safe_print("\n🔍 Checking multi-part archive completeness | 检查多部分压缩文件完整性")
    safe_print("-" * 50)
    
    # Detect multi-part patterns
    multipart_archives = detect_multipart_patterns(files)
    
    if not multipart_archives:
        safe_print("✓ No multi-part archives detected | 未检测到多部分压缩文件")
        return [], []
    
    potential_missing_containers = []
    complete_count = 0
    incomplete_count = 0
    
    for archive in multipart_archives:
        if verbose:
            safe_print(f"\n📦 Multi-part archive: {archive.base_name}")
            safe_print(f"   Found parts: {sorted(archive.found_parts.keys())}")
            safe_print(f"   Expected parts: {sorted(archive.expected_parts)}")
        
        if archive.is_complete:
            complete_count += 1
            if verbose:
                safe_print(f"   ✅ Complete | 完整")
        else:
            incomplete_count += 1
            missing_parts = archive.get_missing_part_numbers()
            if verbose:
                safe_print(f"   ❌ Incomplete - Missing parts: {missing_parts} | 不完整 - 缺少部分: {missing_parts}")
            
            # Look for potential containers that might have the missing parts
            potential_containers = find_missing_parts_in_group(archive, files)
            if potential_containers:
                if verbose:
                    safe_print(f"   🔍 Potential containers for missing parts:")
                    for container in potential_containers:
                        safe_print(f"      📁 {container.name}")
                potential_missing_containers.extend(potential_containers)
    
    # Summary
    safe_print(f"\n📊 Multi-part archive summary | 多部分压缩文件摘要:")
    safe_print(f"   ✅ Complete archives: {complete_count} | 完整的压缩文件: {complete_count}")
    safe_print(f"   ❌ Incomplete archives: {incomplete_count} | 不完整的压缩文件: {incomplete_count}")
    
    if potential_missing_containers:
        safe_print(f"   🔍 Potential missing part containers: {len(potential_missing_containers)} | 潜在的缺失部分容器: {len(potential_missing_containers)}")
    
    return multipart_archives, potential_missing_containers


def prioritize_extraction_order(multipart_archives: List[MultiPartArchive], other_files: List[Path]) -> List[Path]:
    """Prioritize extraction order based on multi-part archive completeness.
    
    Args:
        multipart_archives: List of detected multi-part archives
        other_files: Other files not part of multi-part archives
        
    Returns:
        List of files in optimal extraction order
    """
    extraction_order = []
    
    # 1. First extract potential missing part containers
    potential_containers = []
    for archive in multipart_archives:
        if not archive.is_complete:
            potential_containers.extend(find_missing_parts_in_group(archive, other_files))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_containers = []
    for container in potential_containers:
        if container not in seen:
            seen.add(container)
            unique_containers.append(container)
    
    extraction_order.extend(unique_containers)
    
    # 2. Then extract complete multi-part archives (first parts only, as 7z will handle the rest)
    for archive in multipart_archives:
        if archive.is_complete and archive.found_parts:
            first_part = min(archive.found_parts.keys())
            first_part_file = archive.found_parts[first_part]
            if first_part_file not in extraction_order:
                extraction_order.append(first_part_file)
    
    # 3. Finally, other files
    for file_path in other_files:
        if file_path not in extraction_order:
            # Skip individual parts of multi-part archives (except first parts already added)
            is_multipart_member = False
            for archive in multipart_archives:
                if file_path in archive.found_parts.values():
                    # Check if this is the first part (already added) or other parts (skip)
                    first_part = min(archive.found_parts.keys())
                    if file_path != archive.found_parts[first_part]:
                        is_multipart_member = True
                        break
            
            if not is_multipart_member:
                extraction_order.append(file_path)
    
    return extraction_order
