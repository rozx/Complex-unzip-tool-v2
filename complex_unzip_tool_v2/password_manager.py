"""Password management utilities for the Complex Unzip Tool."""

from pathlib import Path
from typing import List, Optional
from .console_utils import safe_print


def load_password_book(root_path: Path) -> List[str]:
    """Load passwords from passwords.txt file, checking multiple locations.
    
    Args:
        root_path: The root directory path to look for passwords.txt
        
    Returns:
        List of passwords, one per line from the file
    """
    passwords = []
    
    # Check multiple locations for passwords.txt
    possible_locations = [
        root_path / "passwords.txt",  # Target directory
        Path.cwd() / "passwords.txt",  # Current working directory (project dir)
        Path(__file__).parent.parent / "passwords.txt"  # Tool's directory
    ]
    
    passwords_file = None
    for location in possible_locations:
        if location.exists() and location.is_file():
            passwords_file = location
            break
    
    if passwords_file:
        try:
            with open(passwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    password = line.strip()
                    if password:  # Skip empty lines
                        passwords.append(password)
            
            if passwords:
                safe_print(f"📖 Loaded {len(passwords)} passwords from password book | 从密码本加载了 {len(passwords)} 个密码")
                safe_print(f"📂 Password file: {passwords_file}")
            else:
                safe_print("📖 Password book found but no passwords loaded | 找到密码本但未加载密码")
                
        except Exception as e:
            safe_print(f"⚠️  Error reading password book: {e} | 读取密码本时出错: {e}")
    else:
        safe_print("📖 No password book found (passwords.txt) | 未找到密码本 (passwords.txt)")
    
    return passwords


def get_password_suggestions(passwords: List[str], archive_name: str) -> List[str]:
    """Get password suggestions based on archive name.
    
    This function can be enhanced to provide smart password suggestions
    based on the archive filename or other heuristics.
    
    Args:
        passwords: List of available passwords
        archive_name: Name of the archive file
        
    Returns:
        List of suggested passwords (currently returns all passwords)
    """
    # For now, return all passwords
    # Future enhancement: could prioritize passwords based on filename patterns
    return passwords


def display_password_info(passwords: List[str], verbose: bool = False) -> None:
    """Display information about loaded passwords.
    
    Args:
        passwords: List of loaded passwords
        verbose: Whether to show detailed information
    """
    if not passwords:
        return
    
    safe_print(f"\n📖 Password Book Summary | 密码本摘要:")
    safe_print(f"   📊 Total passwords: {len(passwords)} | 总密码数: {len(passwords)}")
    
    if verbose and passwords:
        print(f"   📋 First few passwords | 前几个密码:")
        # Show first 3 passwords for preview (masked for security)
        for i, password in enumerate(passwords[:3]):
            masked_password = password[:2] + "*" * (len(password) - 2) if len(password) > 2 else "*" * len(password)
            print(f"      {i+1}. {masked_password}")
        
        if len(passwords) > 3:
            print(f"      ... and {len(passwords) - 3} more | 还有 {len(passwords) - 3} 个")


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
            safe_print(f"⚠️  Error reading password file: {e} | 读取密码文件错误: {e}")
    
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
            safe_print(f"🔐 Added {len(passwords_to_add)} new passwords to password book | 向密码本添加了 {len(passwords_to_add)} 个新密码")
        except Exception as e:
            safe_print(f"⚠️  Error saving passwords: {e} | 保存密码时出错: {e}")
