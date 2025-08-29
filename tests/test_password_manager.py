"""Tests for password manager functionality."""

import tempfile
from pathlib import Path
import pytest

from complex_unzip_tool_v2.password_manager import (
    load_password_book,
    get_password_suggestions,
    display_password_info
)


class TestPasswordManager:
    """Test cases for password manager functionality."""
    
    def test_load_password_book_with_file(self):
        """Test loading passwords from an existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            passwords_file = temp_path / "passwords.txt"
            
            # Create test password file
            passwords_file.write_text("password1\npassword2\n\npassword3\n", encoding='utf-8')
            
            passwords = load_password_book(temp_path)
            
            assert len(passwords) == 3
            assert "password1" in passwords
            assert "password2" in passwords
            assert "password3" in passwords
    
    def test_load_password_book_no_file(self):
        """Test loading passwords when no file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            passwords = load_password_book(temp_path)
            
            assert len(passwords) == 0
    
    def test_load_password_book_empty_file(self):
        """Test loading passwords from an empty file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            passwords_file = temp_path / "passwords.txt"
            
            # Create empty password file
            passwords_file.write_text("", encoding='utf-8')
            
            passwords = load_password_book(temp_path)
            
            assert len(passwords) == 0
    
    def test_load_password_book_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            passwords_file = temp_path / "passwords.txt"
            
            # Create password file with whitespace
            passwords_file.write_text("  password1  \n\n  \npassword2\n  password3  \n", encoding='utf-8')
            
            passwords = load_password_book(temp_path)
            
            assert len(passwords) == 3
            assert "password1" in passwords
            assert "password2" in passwords
            assert "password3" in passwords
    
    def test_get_password_suggestions(self):
        """Test password suggestions functionality."""
        passwords = ["password1", "password2", "password3"]
        suggestions = get_password_suggestions(passwords, "test.zip")
        
        # Currently returns all passwords
        assert len(suggestions) == 3
        assert suggestions == passwords
    
    def test_display_password_info(self, capsys):
        """Test password info display."""
        passwords = ["password1", "password2", "password3"]
        
        display_password_info(passwords, verbose=False)
        captured = capsys.readouterr()
        
        assert "Password Book Summary" in captured.out
        assert "Total passwords: 3" in captured.out
    
    def test_display_password_info_verbose(self, capsys):
        """Test verbose password info display."""
        passwords = ["password1", "password2", "password3", "password4"]
        
        display_password_info(passwords, verbose=True)
        captured = capsys.readouterr()
        
        assert "Password Book Summary" in captured.out
        assert "Total passwords: 4" in captured.out
        assert "First few passwords" in captured.out
        assert "pa*******" in captured.out  # Masked password
    
    def test_display_password_info_empty(self, capsys):
        """Test password info display with empty list."""
        passwords = []
        
        display_password_info(passwords, verbose=False)
        captured = capsys.readouterr()
        
        # Should not output anything for empty password list
        assert captured.out == ""
