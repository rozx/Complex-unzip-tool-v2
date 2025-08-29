"""Tests for archive extraction functionality."""

import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from complex_unzip_tool_v2.archive_extractor import (
    get_7z_executable,
    is_archive_file,
    find_main_archive_in_group,
    ExtractionResult
)


class TestArchiveExtractor:
    """Test cases for archive extraction functionality."""
    
    def test_get_7z_executable(self):
        """Test 7z executable path detection."""
        seven_z_path = get_7z_executable()
        assert seven_z_path.name == "7z.exe"
        assert "7z" in str(seven_z_path)
    
    def test_is_archive_file(self):
        """Test archive file detection."""
        # Test common archive extensions
        assert is_archive_file(Path("test.7z")) == True
        assert is_archive_file(Path("test.zip")) == True
        assert is_archive_file(Path("test.rar")) == True
        assert is_archive_file(Path("test.001")) == True
        assert is_archive_file(Path("test.part1")) == True
        assert is_archive_file(Path("test.z01")) == True
        
        # Test non-archive files
        assert is_archive_file(Path("test.txt")) == False
        assert is_archive_file(Path("test.exe")) == False
        assert is_archive_file(Path("test.jpg")) == False
    
    def test_find_main_archive_in_group_unique_extension(self):
        """Test finding main archive with unique extension."""
        group_files = [
            Path("archive.7z"),      # Unique archive
            Path("data.001"),        # Multi-part
            Path("data.002"),        # Multi-part
            Path("data.003"),        # Multi-part
        ]
        
        main_archive = find_main_archive_in_group(group_files)
        assert main_archive == Path("archive.7z")
    
    def test_find_main_archive_in_group_first_part(self):
        """Test finding main archive as first part of split archive."""
        group_files = [
            Path("archive.001"),     # First part
            Path("archive.002"),     # Second part
            Path("archive.003"),     # Third part
        ]
        
        main_archive = find_main_archive_in_group(group_files)
        assert main_archive == Path("archive.001")
    
    def test_find_main_archive_in_group_no_archive(self):
        """Test finding main archive when no archives present."""
        group_files = [
            Path("document.txt"),
            Path("script.py"), 
            Path("readme.log"),
        ]
        
        # With enhanced detection, it should try script.py since .txt and .log are excluded
        main_archive = find_main_archive_in_group(group_files)
        assert main_archive == Path("script.py")
        
        # Test with only excluded files - should return None
        excluded_files = [
            Path("document.txt"),
            Path("config.log"),
            Path("program.exe"),
        ]
        main_archive = find_main_archive_in_group(excluded_files)
        assert main_archive is None
    
    def test_extraction_result_initialization(self):
        """Test ExtractionResult initialization."""
        result = ExtractionResult()
        
        assert result.successful_extractions == []
        assert result.failed_extractions == []
        assert result.passwords_used == []
        assert result.new_passwords == []
        assert isinstance(result.processed_files, set)
        assert result.completed_files == []
    
    @patch('subprocess.run')
    def test_extract_with_7z_success_no_password(self, mock_run):
        """Test successful extraction without password."""
        from complex_unzip_tool_v2.archive_extractor import extract_with_7z
        
        # Mock successful subprocess run
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "test.7z"
            output_dir = Path(temp_dir) / "output"
            
            # Create dummy archive file
            archive_path.touch()
            
            success, message, password = extract_with_7z(archive_path, output_dir, [])
            
            assert success == True
            assert "successfully without password" in message
            assert password is None
    
    @patch('subprocess.run')
    def test_extract_with_7z_success_with_password(self, mock_run):
        """Test successful extraction with password."""
        from complex_unzip_tool_v2.archive_extractor import extract_with_7z
        
        # Mock failed first attempt, successful second
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="Wrong password"),  # No password fails
            MagicMock(returncode=0, stderr="")                 # With password succeeds
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "test.7z"
            output_dir = Path(temp_dir) / "output"
            
            # Create dummy archive file
            archive_path.touch()
            
            success, message, password = extract_with_7z(archive_path, output_dir, ["testpass"])
            
            assert success == True
            assert "successfully with password" in message
            assert password == "testpass"
    
    @patch('subprocess.run')
    def test_extract_with_7z_failure(self, mock_run):
        """Test failed extraction."""
        from complex_unzip_tool_v2.archive_extractor import extract_with_7z
        
        # Mock failed subprocess run
        mock_run.return_value = MagicMock(returncode=1, stderr="Corrupted archive")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "test.7z"
            output_dir = Path(temp_dir) / "output"
            
            # Create dummy archive file
            archive_path.touch()
            
            success, message, password = extract_with_7z(archive_path, output_dir, [])
            
            assert success == False
            assert "Extraction failed" in message
            assert password is None
    
    def test_find_main_archive_complex_scenarios(self):
        """Test complex scenarios for finding main archive."""
        # Scenario 1: Mixed files with clear main archive
        group_files = [
            Path("readme.txt"),
            Path("archive.7z"),       # Should be selected (unique archive)
            Path("data.001"),
            Path("data.002"),
        ]
        
        main_archive = find_main_archive_in_group(group_files)
        assert main_archive == Path("archive.7z")
        
        # Scenario 2: Only split archives
        group_files = [
            Path("backup.001"),       # Should be selected (first part)
            Path("backup.002"),
            Path("backup.003"),
        ]
        
        main_archive = find_main_archive_in_group(group_files)
        assert main_archive == Path("backup.001")
        
        # Scenario 3: Multiple potential main archives
        group_files = [
            Path("archive1.7z"),
            Path("archive2.zip"),
        ]
        
        main_archive = find_main_archive_in_group(group_files)
        # Should return one of them (sorted order)
        assert main_archive in [Path("archive1.7z"), Path("archive2.zip")]
