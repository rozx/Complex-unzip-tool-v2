"""Tests for the main module."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from complex_unzip_tool_v2.main import main, process_paths
from complex_unzip_tool_v2.path_validator import validate_paths
from complex_unzip_tool_v2.file_collector import collect_all_files, is_system_file
from complex_unzip_tool_v2.file_grouper import group_files_by_subfolder, group_files_by_similarity, group_files_by_priority
from complex_unzip_tool_v2.filename_utils import normalize_filename, calculate_similarity, extract_base_name


def test_main_function_exists():
    """Test that the main function exists and is callable."""
    assert callable(main)


def test_main_shows_help_with_no_args(capsys):
    """Test that main function shows help when no arguments provided."""
    with patch('sys.argv', ['complex-unzip']):
        try:
            main()
        except SystemExit:
            pass  # Expected behavior when no args provided
    captured = capsys.readouterr()
    # Help text should now be in stdout (normal help), not stderr (error)
    assert "usage:" in captured.out.lower() or "Complex Unzip Tool v2" in captured.out


def test_validate_paths_with_existing_file():
    """Test validate_paths with an existing file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        result = validate_paths([tmp_path])
        assert len(result) == 1
        assert result[0].exists()
    finally:
        os.unlink(tmp_path)


def test_validate_paths_with_nonexistent_file():
    """Test validate_paths with a non-existent file."""
    with pytest.raises(FileNotFoundError):
        validate_paths(["/this/path/does/not/exist"])


def test_validate_paths_with_directory():
    """Test validate_paths with an existing directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        result = validate_paths([tmp_dir])
        assert len(result) == 1
        assert result[0].is_dir()


def test_process_paths_with_file(capsys):
    """Test process_paths with a file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        process_paths([tmp_path])
        captured = capsys.readouterr()
        assert "Found 1 total files" in captured.out
        assert str(tmp_path.name) in captured.out
    finally:
        os.unlink(tmp_path)


def test_process_paths_with_directory(capsys):
    """Test process_paths with a directory containing files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create a test file in the directory
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        process_paths([tmp_path])
        captured = capsys.readouterr()
        assert "Found 1 total files" in captured.out
        assert "GROUPING BY SUBFOLDER" in captured.out


def test_chinese_text_in_output(capsys):
    """Test that Chinese text appears in the output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create a test file in the directory
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        process_paths([tmp_path])
        captured = capsys.readouterr()
        # Test Chinese text is present
        assert "复杂解压工具 v2" in captured.out
        assert "正在处理" in captured.out
        assert "处理完成" in captured.out


def test_collect_all_files():
    """Test file collection functionality."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test files
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Create subdirectory with files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file3 = subdir / "test3.txt"
        file3.write_text("content3")
        
        # Test non-recursive collection
        files = collect_all_files([tmp_path], recursive=False)
        assert len(files) == 2
        assert file1 in files
        assert file2 in files
        assert file3 not in files
        
        # Test recursive collection
        files_recursive = collect_all_files([tmp_path], recursive=True)
        assert len(files_recursive) == 3
        assert file1 in files_recursive
        assert file2 in files_recursive
        assert file3 in files_recursive


def test_collect_all_files_excludes_passwords_txt():
    """Test that passwords.txt files are excluded from file collection."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create test files including passwords.txt
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "archive.zip"
        passwords_file = tmp_path / "passwords.txt"
        passwords_file_upper = tmp_path / "PASSWORDS.TXT"  # Test case insensitivity
        
        file1.write_text("content1")
        file2.write_text("archive content")
        passwords_file.write_text("password1\npassword2")
        passwords_file_upper.write_text("password3\npassword4")
        
        # Test that passwords.txt files are excluded
        files = collect_all_files([tmp_path], recursive=False)
        assert len(files) == 2  # Should exclude both passwords.txt files
        assert file1 in files
        assert file2 in files
        assert passwords_file not in files
        assert passwords_file_upper not in files
        
        # Test with explicit passwords.txt path
        files_explicit = collect_all_files([passwords_file], recursive=False)
        assert len(files_explicit) == 0  # Should be empty as passwords.txt is filtered out


def test_collect_all_files_excludes_system_files():
    """Test that system files are excluded from file collection."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create regular files
        file1 = tmp_path / "document.txt"
        file2 = tmp_path / "archive.zip"
        file1.write_text("content1")
        file2.write_text("archive content")
        
        # Create Windows system files
        thumbs_db = tmp_path / "Thumbs.db"
        desktop_ini = tmp_path / "desktop.ini"
        system_file = tmp_path / "config.sys"
        thumbs_db.write_text("thumbnail cache")
        desktop_ini.write_text("[.ShellClassInfo]")
        system_file.write_text("system config")
        
        # Create macOS system files
        ds_store = tmp_path / ".DS_Store"
        spotlight = tmp_path / ".Spotlight-V100"
        ds_store.write_text("macos metadata")
        spotlight.write_text("spotlight index")
        
        # Create Linux system files
        directory_file = tmp_path / ".directory"
        trash_file = tmp_path / ".Trash-1000"
        directory_file.write_text("kde directory config")
        trash_file.write_text("trash metadata")
        
        # Test that system files are excluded
        files = collect_all_files([tmp_path], recursive=False)
        assert len(files) == 2  # Should only include regular files
        assert file1 in files
        assert file2 in files
        
        # Verify system files are excluded
        assert thumbs_db not in files
        assert desktop_ini not in files
        assert system_file not in files
        assert ds_store not in files
        assert spotlight not in files
        assert directory_file not in files
        assert trash_file not in files


def test_is_system_file():
    """Test the is_system_file function with various file types."""
    # Regular files should not be system files
    assert not is_system_file(Path("document.txt"))
    assert not is_system_file(Path("archive.zip"))
    assert not is_system_file(Path("program.exe"))
    
    # Windows system files
    assert is_system_file(Path("Thumbs.db"))
    assert is_system_file(Path("THUMBS.DB"))  # Case insensitive
    assert is_system_file(Path("desktop.ini"))
    assert is_system_file(Path("DESKTOP.INI"))
    assert is_system_file(Path("config.sys"))
    assert is_system_file(Path("autorun.inf"))
    
    # macOS system files
    assert is_system_file(Path(".DS_Store"))
    assert is_system_file(Path(".ds_store"))  # Case insensitive
    assert is_system_file(Path(".Spotlight-V100"))
    assert is_system_file(Path(".Trash"))
    
    # Linux system files
    assert is_system_file(Path(".directory"))
    assert is_system_file(Path(".Trash-1000"))
    assert is_system_file(Path("lost+found"))
    
    # Hidden files (should be system files, except archives)
    assert is_system_file(Path(".hidden_file"))
    assert is_system_file(Path(".config"))
    
    # Hidden archive files should NOT be system files
    assert not is_system_file(Path(".secret.zip"))
    assert not is_system_file(Path(".backup.7z"))
    assert not is_system_file(Path(".archive.rar"))


def test_group_files_by_subfolder():
    """Test subfolder grouping functionality."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create files in different directories
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        file2 = subdir / "file2.txt"
        file2.write_text("content2")
        
        files = [file1, file2]
        groups = group_files_by_subfolder(files)
        
        assert len(groups) == 2
        assert tmp_path in groups
        assert subdir in groups
        assert file1 in groups[tmp_path]
        assert file2 in groups[subdir]


def test_normalize_filename():
    """Test filename normalization."""
    assert normalize_filename("Test_File.txt") == "testfile"
    assert normalize_filename("Archive-2024.zip") == "archive2024"
    assert normalize_filename("My Document (1).pdf") == "mydocument1"


def test_calculate_similarity():
    """Test filename similarity calculation."""
    # Very similar files
    similarity = calculate_similarity("archive1.zip", "archive2.zip")
    assert similarity > 0.8
    
    # Different files
    similarity = calculate_similarity("archive.zip", "document.pdf")
    assert similarity < 0.5
    
    # Identical files
    similarity = calculate_similarity("test.txt", "test.txt")
    assert similarity == 1.0


def test_group_files_by_similarity():
    """Test similarity grouping functionality."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create similar files
        file1 = tmp_path / "archive1.zip"
        file2 = tmp_path / "archive2.zip"
        file3 = tmp_path / "document.pdf"
        
        file1.write_text("content1")
        file2.write_text("content2")
        file3.write_text("content3")
        
        files = [file1, file2, file3]
        groups = group_files_by_similarity(files, threshold=0.7)
        
        # Should have at least one group with archive files
        archive_group = None
        for group_name, group_files in groups.items():
            if len(group_files) > 1 and all("archive" in f.name for f in group_files):
                archive_group = group_files
                break
        
        assert archive_group is not None
        assert file1 in archive_group
        assert file2 in archive_group


def test_extract_base_name():
    """Test base name extraction for precise grouping."""
    # Multi-part 7z archives
    assert extract_base_name("12.7z.001") == "12.7z"
    assert extract_base_name("16.7z.002") == "16.7z"
    assert extract_base_name("archive.7z.003") == "archive.7z"

    # Multi-part rar archives
    assert extract_base_name("data.rar.001") == "data.rar"

    # Multi-part with just numbers
    assert extract_base_name("backup.001") == "backup"
    assert extract_base_name("backup.002") == "backup"

    # Cloaked extensions (new test cases)
    assert extract_base_name("16.7z - Copy.001删") == "16.7z - copy"
    assert extract_base_name("16.7z - Copy.002删") == "16.7z - copy"
    assert extract_base_name("archive.7z.001隐藏") == "archive.7z"

    # Regular files
    assert extract_base_name("document.pdf") == "document"


def test_cloaked_multipart_grouping():
    """Test that cloaked multi-part archives are properly grouped together."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create cloaked multi-part files
        files_to_create = [
            "16.7z - Copy.001删",   # Cloaked part 1
            "16.7z - Copy.002删",   # Cloaked part 2  
            "normal.7z.001",        # Standard part 1
            "normal.7z.002",        # Standard part 2
            "single_file.txt",      # Individual file
        ]
        
        file_paths = []
        for filename in files_to_create:
            file_path = tmp_path / filename
            file_path.write_text(f"content of {filename}")
            file_paths.append(file_path)
        
        groups = group_files_by_similarity(file_paths, threshold=0.9)
        
        # Should have 2 multi-part groups + 1 single file
        multipart_groups = [g for name, g in groups.items() if name.startswith("multipart_")]
        single_groups = [g for name, g in groups.items() if name.startswith("single_")]
        
        assert len(multipart_groups) == 2  # 16.7z - copy group and normal.7z group
        assert len(single_groups) == 1     # single_file.txt
        
        # Check that cloaked files are grouped together
        cloaked_group = None
        normal_group = None
        
        for group in multipart_groups:
            filenames = [f.name for f in group]
            if "16.7z - Copy.001删" in filenames:
                cloaked_group = group
            elif "normal.7z.001" in filenames:
                normal_group = group
        
        assert cloaked_group is not None
        assert normal_group is not None
        assert len(cloaked_group) == 2  # Both cloaked parts
        assert len(normal_group) == 2   # Both normal parts
    assert extract_base_name("image.jpg") == "image"
    assert extract_base_name("script.exe") == "script"
    
    # Files without extensions
    assert extract_base_name("readme") == "readme"


def test_precise_grouping():
    """Test that the new precise grouping works correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create multi-part archives that should be grouped separately
        files_to_create = [
            "12.7z.001", "12.7z.002",  # Group 1
            "16.7z.001", "16.7z.002",  # Group 2
            "backup.rar.001", "backup.rar.002",  # Group 3
            "document.pdf",  # Individual
            "script1.exe",   # Individual
            "script2.exe",   # Individual
        ]
        
        file_paths = []
        for filename in files_to_create:
            file_path = tmp_path / filename
            file_path.write_text(f"content of {filename}")
            file_paths.append(file_path)
        
        groups = group_files_by_similarity(file_paths, threshold=0.9)
        
        # Should have 3 multi-part groups + 3 individual files
        multi_part_groups = [g for name, g in groups.items() if not name.startswith("single_")]
        single_file_groups = [g for name, g in groups.items() if name.startswith("single_")]
        
        assert len(multi_part_groups) == 3  # 12.7z, 16.7z, backup.rar groups
        assert len(single_file_groups) == 3  # document.pdf, script1.exe, script2.exe
        
        # Each multi-part group should have exactly 2 files
        for group in multi_part_groups:
            assert len(group) == 2


def test_subfolder_priority_grouping():
    """Test that subfolder priority grouping works correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create subdirectories with multiple files each
        subdir1 = tmp_path / "folder1"
        subdir2 = tmp_path / "folder2"
        subdir1.mkdir()
        subdir2.mkdir()
        
        # Files in folder1 - should all be grouped together
        file1a = subdir1 / "archive.7z.001"
        file1b = subdir1 / "archive.7z.002"
        file1c = subdir1 / "readme.txt"
        file1a.write_text("content1a")
        file1b.write_text("content1b") 
        file1c.write_text("content1c")
        
        # Files in folder2 - should all be grouped together
        file2a = subdir2 / "backup.7z.001"
        file2b = subdir2 / "backup.7z.002"
        file2a.write_text("content2a")
        file2b.write_text("content2b")
        
        all_files = [file1a, file1b, file1c, file2a, file2b]
        
        groups = group_files_by_priority(all_files, tmp_path)
        
        # Should have 2 subfolder archive groups (all files in each folder grouped together)
        subfolder_archive_groups = [g for name, g in groups.items() if name.endswith("_subfolder")]
        assert len(subfolder_archive_groups) == 2
        
        # Verify the groups contain the correct files
        folder1_group = None
        folder2_group = None
        
        for name, group in groups.items():
            if file1a in group:
                folder1_group = group
            elif file2a in group:
                folder2_group = group
        
        assert folder1_group is not None
        assert folder2_group is not None
        assert len(folder1_group) == 3  # archive.7z.001, archive.7z.002, readme.txt
        assert len(folder2_group) == 2   # backup.7z.001, backup.7z.002
        
        # Verify all files from folder1 are in folder1_group
        assert file1a in folder1_group
        assert file1b in folder1_group
        assert file1c in folder1_group
        
        # Verify all files from folder2 are in folder2_group
        assert file2a in folder2_group
        assert file2b in folder2_group
