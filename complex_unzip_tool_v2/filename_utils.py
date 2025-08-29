"""Filename utilities for the Complex Unzip Tool."""

import re
import difflib
from pathlib import Path


def normalize_filename(filename: str) -> str:
    """Normalize filename for comparison by removing special characters and converting to lowercase.
    
    Args:
        filename: The filename to normalize
        
    Returns:
        Normalized filename string
    """
    # Remove file extension and convert to lowercase
    name_without_ext = Path(filename).stem.lower()
    
    # Remove special characters, keep only alphanumeric and basic separators
    normalized = re.sub(r'[^\w\s._-]', '', name_without_ext)
    
    # Replace multiple spaces/separators with single space and remove spaces
    normalized = re.sub(r'[\s._-]+', '', normalized)
    
    return normalized


def calculate_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two normalized filenames.
    
    Args:
        name1: First filename (normalized)
        name2: Second filename (normalized)
        
    Returns:
        Similarity ratio between 0.0 and 1.0
    """
    return difflib.SequenceMatcher(None, name1, name2).ratio()


def extract_base_name(filename: str) -> str:
    """Extract base name from a potentially multi-part archive filename.
    
    This function handles various multi-part archive formats, including cases
    where extensions might be cloaked or have additional characters.
    
    Examples:
        archive.7z.001 -> archive.7z
        backup.rar.002 -> backup.rar
        16.7z - Copy.001删 -> 16.7z - copy
        file.zip.003 -> file.zip
        backup.001 -> backup
        document.pdf -> document
        
    Args:
        filename: The filename to extract base name from
        
    Returns:
        Base name without part number
    """
    # Remove file extension first if it exists
    name_without_ext = Path(filename).stem
    
    # Pattern 1: Standard multi-part archives: .7z.001, .rar.002, .zip.003, etc.
    pattern1 = r'^(.+\.(7z|rar|zip))\.\d+$'
    match1 = re.search(pattern1, filename, re.IGNORECASE)
    
    if match1:
        return match1.group(1).lower()
    
    # Pattern 2: Multi-part with additional text: "16.7z - Copy.001删" -> "16.7z - copy"
    # Look for archive-like patterns followed by dots and numbers, ignoring trailing text
    pattern2 = r'^(.+(?:7z|rar|zip)[^.]*?)\.\d+.*$'
    match2 = re.search(pattern2, filename, re.IGNORECASE)
    
    if match2:
        base_part = match2.group(1)
        # Clean up the base part - remove extra spaces and normalize
        base_part = re.sub(r'\s+', ' ', base_part).strip()
        return base_part.lower()
    
    # Pattern 3: Generic numbered files: .001, .002, .003, etc.
    pattern3 = r'^(.+)\.\d{3}.*$'
    match3 = re.search(pattern3, filename)
    
    if match3:
        base_part = match3.group(1)
        # Clean up the base part
        base_part = re.sub(r'\s+', ' ', base_part).strip()
        return base_part.lower()
    
    # Pattern 4: Look for any pattern with numbers at the end
    # This catches cases like "name.part1", "file_001", etc.
    pattern4 = r'^(.+?)[\s._-]*\d+.*$'
    match4 = re.search(pattern4, name_without_ext)
    
    if match4:
        base_part = match4.group(1)
        # Only consider this a multi-part if it looks like an archive or has typical patterns
        if (re.search(r'(7z|rar|zip|part|vol)', base_part, re.IGNORECASE) or 
            len([f for f in [filename] if re.search(r'[\s._-]\d+', f)]) > 0):
            base_part = re.sub(r'\s+', ' ', base_part).strip()
            return base_part.lower()
    
    # No pattern matched, return the stem (filename without extension)
    return Path(filename).stem.lower()
