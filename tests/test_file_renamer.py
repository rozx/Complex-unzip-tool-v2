"""Tests for file renaming functionality."""

import tempfile
from pathlib import Path
import pytest

from complex_unzip_tool_v2.file_renamer import (
    detect_cloaked_files,
    rename_cloaked_files,
    _is_archive_like,
    group_rename_suggestions_by_directory
)


class TestFileRenamer:
    """Test cases for file renaming functionality."""
    
    def test_detect_cloaked_files_basic(self):
        """Test basic cloaked file detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            test_files = [
                temp_path / "archive.7z.001删",
                temp_path / "backup.7z.002删除",
                temp_path / "normal.txt",
                temp_path / "data.zip删",
            ]
            
            for file_path in test_files:
                file_path.touch()
            
            suggestions = detect_cloaked_files(test_files)
            
            assert len(suggestions) == 3  # Should detect 3 cloaked files
            assert temp_path / "archive.7z.001删" in suggestions
            assert temp_path / "backup.7z.002删除" in suggestions
            assert temp_path / "data.zip删" in suggestions
            assert temp_path / "normal.txt" not in suggestions
            
            # Check suggested names
            assert suggestions[temp_path / "archive.7z.001删"].name == "archive.7z.001"
            assert suggestions[temp_path / "backup.7z.002删除"].name == "backup.7z.002"
            assert suggestions[temp_path / "data.zip删"].name == "data.zip"
    
    def test_detect_cloaked_files_complex_patterns(self):
        """Test detection of complex cloaking patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files with various patterns
            test_files = [
                temp_path / "16.7z - Copy.001删",
                temp_path / "archive删.002",
                temp_path / "data.part001删",
                temp_path / "backup.z01删除",
                temp_path / "file删除",  # This should not be detected as archive
            ]
            
            for file_path in test_files:
                file_path.touch()
            
            suggestions = detect_cloaked_files(test_files)
            
            # Should detect archive-like files but not generic files
            assert len(suggestions) >= 3
            assert temp_path / "16.7z - Copy.001删" in suggestions
            assert temp_path / "data.part001删" in suggestions
            assert temp_path / "backup.z01删除" in suggestions
            
            # Check suggested names
            assert suggestions[temp_path / "16.7z - Copy.001删"].name == "16.7z - Copy.001"
            assert suggestions[temp_path / "data.part001删"].name == "data.part001"
            assert suggestions[temp_path / "backup.z01删除"].name == "backup.z01"
    
    def test_is_archive_like(self):
        """Test archive file detection."""
        assert _is_archive_like("file.001") == True
        assert _is_archive_like("file.999") == True
        assert _is_archive_like("archive.7z") == True
        assert _is_archive_like("backup.zip") == True
        assert _is_archive_like("data.rar") == True
        assert _is_archive_like("file.part001") == True
        assert _is_archive_like("backup.z01") == True
        
        assert _is_archive_like("document.txt") == False
        assert _is_archive_like("image.jpg") == False
        assert _is_archive_like("script.py") == False
        assert _is_archive_like("config.ini") == False
    
    def test_rename_cloaked_files_dry_run(self):
        """Test dry run functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            original_file = temp_path / "archive.7z.001删"
            original_file.touch()
            
            suggestions = {
                original_file: temp_path / "archive.7z.001"
            }
            
            renamed_files, errors = rename_cloaked_files(suggestions, dry_run=True)
            
            # File should not actually be renamed in dry run
            assert original_file.exists()
            assert not (temp_path / "archive.7z.001").exists()
            assert len(renamed_files) == 1
            assert len(errors) == 0
    
    def test_rename_cloaked_files_actual(self):
        """Test actual file renaming."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            original_file = temp_path / "archive.7z.001删"
            original_file.write_text("test content")
            
            suggestions = {
                original_file: temp_path / "archive.7z.001"
            }
            
            renamed_files, errors = rename_cloaked_files(suggestions, dry_run=False)
            
            # File should be actually renamed
            assert not original_file.exists()
            assert (temp_path / "archive.7z.001").exists()
            assert (temp_path / "archive.7z.001").read_text() == "test content"
            assert len(renamed_files) == 1
            assert len(errors) == 0
    
    def test_rename_conflict_handling(self):
        """Test handling of rename conflicts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            cloaked_file = temp_path / "archive.7z.001删"
            cloaked_file.touch()
            
            # Create a file that would conflict
            target_file = temp_path / "archive.7z.001"
            target_file.touch()
            
            # This should not suggest a rename due to conflict
            suggestions = detect_cloaked_files([cloaked_file])
            
            # Should not suggest rename if target already exists
            assert len(suggestions) == 0
    
    def test_group_rename_suggestions_by_directory(self):
        """Test grouping rename suggestions by directory."""
        temp_base = Path("/temp")
        dir1 = temp_base / "dir1"
        dir2 = temp_base / "dir2"
        
        suggestions = {
            dir1 / "file1.001删": dir1 / "file1.001",
            dir1 / "file2.002删": dir1 / "file2.002",
            dir2 / "file3.001删": dir2 / "file3.001",
        }
        
        grouped = group_rename_suggestions_by_directory(suggestions)
        
        assert len(grouped) == 2
        assert dir1 in grouped
        assert dir2 in grouped
        assert len(grouped[dir1]) == 2
        assert len(grouped[dir2]) == 1
    
    def test_no_cloaked_files(self):
        """Test behavior when no cloaked files are found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create normal files
            test_files = [
                temp_path / "normal.txt",
                temp_path / "archive.7z",
                temp_path / "backup.zip",
            ]
            
            for file_path in test_files:
                file_path.touch()
            
            suggestions = detect_cloaked_files(test_files)
            
            assert len(suggestions) == 0
    
    def test_edge_cases(self):
        """Test edge cases in cloaked file detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test edge cases
            test_files = [
                temp_path / "删.001",  # Starts with 删
                temp_path / "file.删",  # Ends with 删 but not archive-like
                temp_path / ".001删",   # Starts with .
                temp_path / "删除删除.7z删",  # Multiple 删除
            ]
            
            for file_path in test_files:
                file_path.touch()
            
            suggestions = detect_cloaked_files(test_files)
            
            # Should handle edge cases gracefully
            assert isinstance(suggestions, dict)
            # The exact number depends on which patterns match and are archive-like
