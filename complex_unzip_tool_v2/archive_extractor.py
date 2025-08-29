"""Archive extraction utilities for the Complex Unzip Tool."""

import os
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
import re


class ExtractionResult:
    """Class to track extraction results."""
    
    def __init__(self):
        self.successful_extractions = []
        self.failed_extractions = []
        self.passwords_used = []
        self.new_passwords = []
        self.processed_files = set()
        self.completed_files = []


def get_7z_executable() -> Path:
    """Get the path to the 7z executable.
    
    Returns:
        Path to 7z.exe
    """
    current_dir = Path(__file__).parent.parent
    seven_z_path = current_dir / "7z" / "7z.exe"
    
    if not seven_z_path.exists():
        raise FileNotFoundError(f"7z.exe not found at {seven_z_path}")
    
    return seven_z_path


def is_archive_file(file_path: Path, strict: bool = True) -> bool:
    """Check if a file is likely an archive file.
    
    Args:
        file_path: Path to the file to check
        strict: If True, only check known archive extensions. If False, treat all files as potential archives.
        
    Returns:
        True if the file appears to be an archive
    """
    if not strict:
        # In non-strict mode, treat any file as a potential archive
        # This is useful for cloaked files with disguised extensions
        return True
    
    archive_extensions = {
        '.7z', '.zip', '.rar', '.tar', '.gz', '.bz2', '.xz',
        '.001', '.002', '.003', '.004', '.005', '.006', '.007', '.008', '.009',
        '.part1', '.part2', '.part3', '.part4', '.part5',
        '.z01', '.z02', '.z03', '.z04', '.z05'
    }
    
    # Check file extension
    if file_path.suffix.lower() in archive_extensions:
        return True
    
    # Check for numbered extensions like .001, .002, etc.
    if re.match(r'\.\d{3}$', file_path.suffix):
        return True
    
    # Check for part extensions
    if re.match(r'\.part\d+$', file_path.suffix):
        return True
    
    return False


def extract_with_7z(archive_path: Path, output_dir: Path, passwords: List[str]) -> Tuple[bool, str, Optional[str]]:
    """Extract an archive using 7z.exe.
    
    Args:
        archive_path: Path to the archive file
        output_dir: Directory to extract to
        passwords: List of passwords to try
        
    Returns:
        Tuple of (success, output_message, password_used)
    """
    seven_z = get_7z_executable()
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Try without password first
    try:
        cmd = [str(seven_z), 'x', str(archive_path), f'-o{output_dir}', '-y']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "Extracted successfully without password", None
        else:
            # Check if it's a password issue
            if "Wrong password" in result.stderr or "password" in result.stderr.lower():
                # Continue to try passwords
                pass
            else:
                return False, f"Extraction failed: {result.stderr}", None
                
    except Exception as e:
        return False, f"Error running 7z: {e}", None
    
    # Try with each password
    for password in passwords:
        try:
            cmd = [str(seven_z), 'x', str(archive_path), f'-o{output_dir}', f'-p{password}', '-y']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"Extracted successfully with password", password
                
        except Exception as e:
            continue
    
    # If all passwords failed, return error
    return False, f"Failed to extract: All passwords failed or corrupted archive", None


def prompt_for_password(archive_name: str) -> Optional[str]:
    """Prompt user for a password.
    
    Args:
        archive_name: Name of the archive file
        
    Returns:
        Password entered by user, or None if cancelled
    """
    print(f"\n🔐 Password required for: {archive_name}")
    print(f"🔐 需要密码: {archive_name}")
    
    try:
        password = input("Enter password (or press Enter to skip): ")
        if password.strip():
            return password.strip()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user | 用户取消")
    
    return None


def find_main_archive_in_group(group_files: List[Path]) -> Optional[Path]:
    """Find the main archive file in a group that should be extracted first.
    
    Args:
        group_files: List of files in the group
        
    Returns:
        Path to the main archive file, or None if not found
    """
    # Look for files with different extensions from others
    extensions = [f.suffix.lower() for f in group_files]
    extension_counts = {}
    
    for ext in extensions:
        extension_counts[ext] = extension_counts.get(ext, 0) + 1
    
    # Find files with unique extensions (likely main archives)
    unique_files = []
    for file_path in group_files:
        if extension_counts[file_path.suffix.lower()] == 1:
            unique_files.append(file_path)
    
    # If we found unique files, prefer known archive-like ones first, then try any file
    if unique_files:
        # First try files that look like archives with strict checking
        strict_archive_files = [f for f in unique_files if is_archive_file(f, strict=True)]
        if strict_archive_files:
            return strict_archive_files[0]
        
        # If no strict archives found, try any unique file (could be cloaked)
        # But exclude common non-archive files
        non_excluded_unique = [f for f in unique_files if f.suffix.lower() not in ['.txt', '.exe', '.dll', '.sys', '.log']]
        if non_excluded_unique:
            return non_excluded_unique[0]
    
    # If no unique files, look for .001 files (first part of split archives)
    first_parts = [f for f in group_files if f.suffix.lower() in ['.001', '.part1', '.z01']]
    if first_parts:
        return first_parts[0]
    
    # Fallback: try any file that looks like an archive (strict mode first)
    strict_archive_files = [f for f in group_files if is_archive_file(f, strict=True)]
    if strict_archive_files:
        return sorted(strict_archive_files)[0]
    
    # Last resort: try any file (non-strict mode for cloaked archives)
    # Skip common non-archive files like .txt, .exe, etc.
    non_executable_files = [f for f in group_files if f.suffix.lower() not in ['.txt', '.exe', '.dll', '.sys', '.log']]
    if non_executable_files:
        return sorted(non_executable_files)[0]
    
    return None


def extract_nested_archives(extract_dir: Path, passwords: List[str], max_depth: int = 5) -> Tuple[List[Path], List[str]]:
    """Recursively extract nested archives.
    
    Args:
        extract_dir: Directory containing extracted files
        passwords: List of passwords to try
        max_depth: Maximum recursion depth
        
    Returns:
        Tuple of (final_files, new_passwords_found)
    """
    if max_depth <= 0:
        return list(extract_dir.rglob('*')), []
    
    new_passwords = []
    
    # Find potential archive files in the extraction directory (use non-strict mode for cloaked files)
    archive_files = []
    for file_path in extract_dir.rglob('*'):
        if file_path.is_file():
            # First try strict checking for known archive formats
            if is_archive_file(file_path, strict=True):
                archive_files.append(file_path)
            # Also try files that might be cloaked archives (avoid common non-archive files)
            elif file_path.suffix.lower() not in ['.txt', '.exe', '.dll', '.sys', '.log', '.ini', '.cfg']:
                # Try to extract any other file as it might be a cloaked archive
                archive_files.append(file_path)
    
    if not archive_files:
        # No more archives to extract
        return [f for f in extract_dir.rglob('*') if f.is_file()], new_passwords
    
    # Extract each potential archive found
    for archive_file in archive_files:
        nested_extract_dir = archive_file.parent / f"{archive_file.stem}_extracted"
        
        success, message, password_used = extract_with_7z(archive_file, nested_extract_dir, passwords)
        
        if success:
            print(f"  📦 Extracted nested archive: {archive_file.name}")
            
            if password_used and password_used not in passwords:
                new_passwords.append(password_used)
            
            # Remove the archive file after successful extraction
            try:
                archive_file.unlink()
            except Exception:
                pass
            
            # Recursively extract any nested archives
            final_files, more_passwords = extract_nested_archives(nested_extract_dir, passwords + new_passwords, max_depth - 1)
            new_passwords.extend(more_passwords)
        else:
            # If extraction failed, it might not be an archive after all
            # Only report failure for files that look like archives with strict checking
            if is_archive_file(archive_file, strict=True):
                print(f"  ❌ Failed to extract nested archive: {archive_file.name}")
    
    return [f for f in extract_dir.rglob('*') if f.is_file()], new_passwords


def create_completed_structure(completed_dir: Path, group_name: str, files: List[Path]) -> Path:
    """Create the completed folder structure and copy files.
    
    Args:
        completed_dir: Base completed directory
        group_name: Name of the group (subfolder name)
        files: List of files to copy
        
    Returns:
        Path to the created group directory
    """
    group_dir = completed_dir / group_name
    group_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path in files:
        if file_path.is_file():
            dest_path = group_dir / file_path.name
            try:
                shutil.copy2(file_path, dest_path)
                print(f"  📄 Copied: {file_path.name}")
            except Exception as e:
                print(f"  ❌ Failed to copy {file_path.name}: {e}")
    
    return group_dir


def clean_up_original_files(files_to_delete: List[Path]) -> Tuple[int, int]:
    """Clean up original files after successful processing.
    
    Args:
        files_to_delete: List of file paths to delete
        
    Returns:
        Tuple of (successfully_deleted, failed_to_delete)
    """
    deleted_count = 0
    failed_count = 0
    
    for file_path in files_to_delete:
        try:
            if file_path.exists():
                file_path.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"  ⚠️  Failed to delete {file_path.name}: {e}")
            failed_count += 1
    
    return deleted_count, failed_count


def save_new_passwords(passwords_file: Path, new_passwords: List[str]) -> None:
    """Save new passwords to the password book.
    
    Args:
        passwords_file: Path to passwords.txt file
        new_passwords: List of new passwords to add
    """
    if not new_passwords:
        return
    
    existing_passwords = set()
    
    # Read existing passwords
    if passwords_file.exists():
        try:
            with open(passwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    password = line.strip()
                    if password:
                        existing_passwords.add(password)
        except Exception as e:
            print(f"  ⚠️  Error reading password file: {e}")
    
    # Add new passwords
    passwords_to_add = []
    for password in new_passwords:
        if password and password not in existing_passwords:
            passwords_to_add.append(password)
            existing_passwords.add(password)
    
    if passwords_to_add:
        try:
            with open(passwords_file, 'a', encoding='utf-8') as f:
                for password in passwords_to_add:
                    f.write(f"{password}\n")
            print(f"  🔐 Added {len(passwords_to_add)} new passwords to password book")
        except Exception as e:
            print(f"  ⚠️  Error saving passwords: {e}")


def display_extraction_results(result: ExtractionResult) -> None:
    """Display the final extraction results.
    
    Args:
        result: ExtractionResult object containing all results
    """
    print("\n" + "=" * 60)
    print("🎯 EXTRACTION RESULTS | 解压结果")
    print("=" * 60)
    
    if result.successful_extractions:
        print(f"\n✅ Successfully processed {len(result.successful_extractions)} groups:")
        for group_name, files_count in result.successful_extractions:
            print(f"  📁 {group_name}: {files_count} files extracted")
    
    if result.failed_extractions:
        print(f"\n❌ Failed to process {len(result.failed_extractions)} groups:")
        for group_name, reason in result.failed_extractions:
            print(f"  📁 {group_name}: {reason}")
    
    if result.new_passwords:
        print(f"\n🔐 Added {len(result.new_passwords)} new passwords to password book")
    
    if result.completed_files:
        print(f"\n📦 Files copied to 'completed' folder: {len(result.completed_files)}")
    
    total_processed = len(result.successful_extractions) + len(result.failed_extractions)
    success_rate = (len(result.successful_extractions) / total_processed * 100) if total_processed > 0 else 0
    
    print(f"\n📊 Overall success rate: {success_rate:.1f}% ({len(result.successful_extractions)}/{total_processed})")
    print("=" * 60)
