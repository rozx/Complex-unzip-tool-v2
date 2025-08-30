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
        
        # Determine expected range based on the pattern and actual content analysis
        min_part = min(part_numbers)
        max_part = max(part_numbers)
        
        # Don't assume consecutive parts are complete - we need to verify
        # For now, assume consecutive parts form the expected set
        expected_parts = set(range(min_part, max_part + 1))
        
        # However, for single-part or two-part archives, we should be more conservative
        # and check if there might be additional parts in container files
        if len(part_numbers) <= 2:
            # This might be incomplete - will be verified by finding missing parts
            # For now, just use what we have as expected, but the missing part detection
            # will look for additional parts in container files
            expected_parts = part_numbers
        
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
    # Always look for potential container files, even if archive appears "complete"
    # because consecutive parts don't guarantee completeness
    
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
        
        # Skip if this file is already identified as a part of this archive
        if file_path in multipart_archive.found_parts.values():
            continue
        
        # Check if this file might contain the missing parts
        # Look for patterns that suggest archive content
        potential_container = False
        
        # Pattern 1: Files with common container names
        if any(keyword in file_name.lower() for keyword in [
            '11111', 'part', 'vol', 'disc', 'archive', 'backup', 'data', 'container'
        ]):
            potential_container = True
        
        # Pattern 2: Since archives can be cloaked with any extension, consider all files as potential containers
        # We'll let the extraction process determine if they're actually archives
        potential_container = True
        
        # Pattern 3: Files that might contain the next sequential parts
        # Check if filename suggests it might contain parts for this base name
        if base_name.lower() in file_name.lower():
            potential_container = True
        
        # Pattern 4: Files with numeric patterns that might indicate parts
        if re.search(r'\d+', file_name):
            potential_container = True
        
        if potential_container:
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
        
        # Always look for potential containers, even for "complete" archives
        # because having consecutive parts doesn't guarantee true completeness
        potential_containers = find_missing_parts_in_group(archive, files)
        
        if potential_containers:
            if verbose:
                safe_print(f"   🔍 Potential containers that might contain additional parts:")
                for container in potential_containers:
                    safe_print(f"      📁 {container.name}")
            potential_missing_containers.extend(potential_containers)
            
            # If we have potential containers, mark as incomplete for investigation
            incomplete_count += 1
            if verbose:
                safe_print(f"   ⚠️  Potentially incomplete - found potential containers | 可能不完整 - 发现潜在容器")
        else:
            if archive.is_complete:
                complete_count += 1
                if verbose:
                    safe_print(f"   ✅ Complete | 完整")
            else:
                incomplete_count += 1
                missing_parts = archive.get_missing_part_numbers()
                if verbose:
                    safe_print(f"   ❌ Incomplete - Missing parts: {missing_parts} | 不完整 - 缺少部分: {missing_parts}")
    
    # Summary
    safe_print(f"\n📊 Multi-part archive summary | 多部分压缩文件摘要:")
    safe_print(f"   ✅ Verified complete archives: {complete_count} | 已验证完整的压缩文件: {complete_count}")
    safe_print(f"   ⚠️  Archives needing investigation: {incomplete_count} | 需要调查的压缩文件: {incomplete_count}")
    
    if potential_missing_containers:
        safe_print(f"   🔍 Potential part containers found: {len(potential_missing_containers)} | 发现潜在的部分容器: {len(potential_missing_containers)}")
    
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
    
    # 1. First extract potential missing part containers (always prioritize these)
    potential_containers = []
    for archive in multipart_archives:
        # For ALL archives, check for potential containers
        containers = find_missing_parts_in_group(archive, other_files)
        potential_containers.extend(containers)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_containers = []
    for container in potential_containers:
        if container not in seen:
            seen.add(container)
            unique_containers.append(container)
    
    extraction_order.extend(unique_containers)
    
    # 2. Then extract multi-part archives (first parts only, as 7z will handle the rest)
    for archive in multipart_archives:
        if archive.found_parts:
            first_part = min(archive.found_parts.keys())
            first_part_file = archive.found_parts[first_part]
            if first_part_file not in extraction_order:
                extraction_order.append(first_part_file)
    
    # 3. Finally, other files not already included
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
