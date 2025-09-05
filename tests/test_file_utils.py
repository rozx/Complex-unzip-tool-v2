"""Unit tests for file_utils module."""

import os
import tempfile
import shutil
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import complex_unzip_tool_v2.modules.file_utils as fu
from complex_unzip_tool_v2.classes.ArchiveGroup import ArchiveGroup


class TestGetArchiveBaseName:
    """Tests for get_archive_base_name function."""

    def test_regular_archive_files(self):
        """Test with regular archive files."""
        assert fu.get_archive_base_name("test.zip") == ("test", "zip")
        assert fu.get_archive_base_name("archive.7z") == ("archive", "7z")
        assert fu.get_archive_base_name("file.tar.gz") == ("file.tar", "gz")

    def test_multipart_archive_files(self):
        """Test with multipart archive files."""
        assert fu.get_archive_base_name("archive.7z.001") == ("archive", "7z")
        assert fu.get_archive_base_name("test.rar.part1") == ("test", "rar")
        assert fu.get_archive_base_name("data.zip.001") == ("data", "zip")

    def test_path_with_directories(self):
        """Test with file paths containing directories."""
        assert fu.get_archive_base_name("/path/to/test.zip") == ("test", "zip")
        assert fu.get_archive_base_name("C:\\folder\\archive.7z.001") == (
            "archive",
            "7z",
        )

    def test_files_without_extension(self):
        """Test with files without extensions."""
        assert fu.get_archive_base_name("filename") == ("filename", "")

    def test_hidden_files(self):
        """Test with hidden files."""
        assert fu.get_archive_base_name(".hidden.zip") == (".hidden", "zip")


class TestReadDir:
    """Tests for read_dir function."""

    def setup_method(self):
        """Set up test directory structure."""
        self.test_dir = tempfile.mkdtemp()
        self.sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.sub_dir)

        # Create test files
        self.test_files = [
            os.path.join(self.test_dir, "file1.txt"),
            os.path.join(self.test_dir, "file2.zip"),
            os.path.join(self.sub_dir, "nested.7z"),
        ]
        for file_path in self.test_files:
            with open(file_path, "w") as f:
                f.write("test content")

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_read_directory(self):
        """Test reading files from a directory."""
        result = fu.read_dir([self.test_dir])
        assert len(result) >= 3  # Should include all test files
        assert any("file1.txt" in path for path in result)
        assert any("file2.zip" in path for path in result)
        assert any("nested.7z" in path for path in result)

    def test_read_individual_files(self):
        """Test reading individual file paths."""
        result = fu.read_dir(self.test_files)
        assert len(result) == 3
        for file_path in self.test_files:
            assert file_path in result

    def test_mixed_files_and_directories(self):
        """Test reading mix of files and directories."""
        paths = [self.test_dir, self.test_files[0]]
        result = fu.read_dir(paths)
        assert self.test_files[0] in result
        # Directory contents should also be included
        assert any("file2.zip" in path for path in result)

    def test_nonexistent_paths(self):
        """Test handling of nonexistent paths."""
        # read_dir includes non-directory paths in result regardless of existence
        result = fu.read_dir(["/nonexistent/path"])
        assert result == [
            "/nonexistent/path"
        ]  # Function adds non-directory paths as-is

    def test_empty_input(self):
        """Test with empty input list."""
        result = fu.read_dir([])
        assert result == []


class TestRenameFile:
    """Tests for rename_file function."""

    def setup_method(self):
        """Set up test files."""
        self.test_dir = tempfile.mkdtemp()
        self.source_file = os.path.join(self.test_dir, "source.txt")
        self.target_file = os.path.join(self.test_dir, "target.txt")

        with open(self.source_file, "w") as f:
            f.write("test content")

    def teardown_method(self):
        """Clean up test files."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_successful_rename(self):
        """Test successful file rename."""
        result = fu.rename_file(self.source_file, self.target_file)
        assert result is True
        assert os.path.exists(self.target_file)
        assert not os.path.exists(self.source_file)

    def test_rename_nonexistent_file(self):
        """Test renaming a nonexistent file."""
        callback_mock = Mock()
        result = fu.rename_file("/nonexistent/file", self.target_file, callback_mock)
        assert result is False
        callback_mock.assert_called_once()
        assert "Error renaming file" in callback_mock.call_args[0][0]

    def test_rename_with_error_callback(self):
        """Test rename with error callback."""
        # Make target directory read-only to cause permission error
        callback_mock = Mock()
        readonly_dir = os.path.join(self.test_dir, "readonly")
        os.makedirs(readonly_dir)

        with patch("os.rename", side_effect=PermissionError("Permission denied")):
            result = fu.rename_file(
                self.source_file, os.path.join(readonly_dir, "test.txt"), callback_mock
            )
            assert result is False
            callback_mock.assert_called_once()
            assert "Permission denied" in callback_mock.call_args[0][0]


class TestSafeRemove:
    """Tests for safe_remove function."""

    def setup_method(self):
        """Set up test files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test.txt")

        with open(self.test_file, "w") as f:
            f.write("test content")

    def teardown_method(self):
        """Clean up test files."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("complex_unzip_tool_v2.modules.file_utils.send2trash")
    def test_remove_to_recycle_bin(self, mock_send2trash):
        """Test removing file to recycle bin."""
        result = fu.safe_remove(self.test_file, use_recycle_bin=True)
        assert result is True
        mock_send2trash.assert_called_once_with(self.test_file)

    def test_permanent_remove(self):
        """Test permanent file removal."""
        result = fu.safe_remove(self.test_file, use_recycle_bin=False)
        assert result is True
        assert not os.path.exists(self.test_file)

    def test_remove_nonexistent_file(self):
        """Test removing nonexistent file."""
        result = fu.safe_remove("/nonexistent/file")
        assert result is False

    def test_remove_with_error_callback(self):
        """Test remove with error callback."""
        callback_mock = Mock()

        with patch("os.remove", side_effect=PermissionError("Permission denied")):
            result = fu.safe_remove(
                self.test_file, use_recycle_bin=False, error_callback=callback_mock
            )
            assert result is False
            callback_mock.assert_called_once()
            assert "Permission denied" in callback_mock.call_args[0][0]


class TestShouldGroupFiles:
    """Tests for _should_group_files function."""

    def test_exact_name_match(self):
        """Test grouping with exact name match."""
        assert (
            fu._should_group_files("test", "test", "/path/file1.zip", "/path/file2.zip")
            is True
        )

    def test_multipart_related_files(self):
        """Test grouping multipart related files."""
        with patch.object(fu, "_are_multipart_related", return_value=True):
            assert (
                fu._should_group_files(
                    "archive", "archive", "/path/archive.7z.001", "/path/archive.7z.002"
                )
                is True
            )

    def test_similar_names(self):
        """Test grouping files with similar names."""
        # The function requires 0.95+ similarity AND exact base name match
        with patch.object(fu, "get_string_similarity", return_value=0.95):
            # Should work when group names have same base after splitting on '-'
            assert (
                fu._should_group_files(
                    "dir-test", "dir-test", "/path/test.zip", "/path/test.zip"
                )
                is True
            )

        with patch.object(fu, "get_string_similarity", return_value=0.85):
            # Should fail with lower similarity
            assert (
                fu._should_group_files(
                    "test", "test123", "/path/test.zip", "/path/test123.zip"
                )
                is False
            )

    def test_different_names_no_grouping(self):
        """Test that different names don't get grouped."""
        assert (
            fu._should_group_files(
                "archive1", "archive2", "/path/archive1.zip", "/path/archive2.zip"
            )
            is False
        )

    def test_short_names_no_grouping(self):
        """Test that short names with low similarity don't get grouped."""
        with patch.object(fu, "get_string_similarity", return_value=0.5):
            assert (
                fu._should_group_files("a", "b", "/path/a.zip", "/path/b.zip") is False
            )


class TestAreMultipartRelated:
    """Tests for _are_multipart_related function."""

    @patch("complex_unzip_tool_v2.modules.file_utils.re.search")
    def test_multipart_archives_same_base(self, mock_search):
        """Test multipart archives with same base name."""
        mock_search.return_value = True

        with patch.object(fu, "get_archive_base_name") as mock_get_base:
            mock_get_base.side_effect = [("archive", "7z"), ("archive", "7z")]
            result = fu._are_multipart_related(
                "/path/archive.7z.001", "/path/archive.7z.002"
            )
            assert result is True

    @patch("complex_unzip_tool_v2.modules.file_utils.re.search")
    def test_multipart_archives_different_base(self, mock_search):
        """Test multipart archives with different base names."""
        mock_search.return_value = True

        with patch.object(fu, "get_archive_base_name") as mock_get_base:
            mock_get_base.side_effect = [("archive1", "7z"), ("archive2", "7z")]
            result = fu._are_multipart_related(
                "/path/archive1.7z.001", "/path/archive2.7z.001"
            )
            assert result is False

    def test_empty_comparison_file(self):
        """Test with empty comparison file."""
        result = fu._are_multipart_related("/path/archive.7z.001", "")
        assert result is False

    @patch("complex_unzip_tool_v2.modules.file_utils.re.search")
    def test_non_multipart_archives(self, mock_search):
        """Test non-multipart archives."""
        mock_search.return_value = False
        result = fu._are_multipart_related("/path/archive1.zip", "/path/archive2.zip")
        assert result is False


class TestIsLikelyArchive:
    """Tests for _is_likely_archive function."""

    def test_common_archive_extensions(self):
        """Test files with common archive extensions."""
        assert fu._is_likely_archive("test.zip") is True
        assert fu._is_likely_archive("archive.7z") is True
        assert fu._is_likely_archive("data.rar") is True
        assert fu._is_likely_archive("file.tar") is True

    def test_multipart_archive_patterns(self):
        """Test files with multipart patterns."""
        with patch(
            "complex_unzip_tool_v2.modules.file_utils.re.search", return_value=True
        ):
            assert fu._is_likely_archive("archive.7z.001") is True

    def test_suspicious_files_with_detection(self):
        """Test suspicious files that get detected as archives."""
        with patch.object(fu, "detect_archive_extension", return_value="zip"):
            assert fu._is_likely_archive("suspicious.exe") is True

    def test_suspicious_files_without_detection(self):
        """Test suspicious files that are not detected as archives."""
        with patch.object(fu, "detect_archive_extension", return_value=None):
            assert fu._is_likely_archive("suspicious.exe") is False

    def test_regular_text_files(self):
        """Test regular non-archive files."""
        assert fu._is_likely_archive("document.txt") is False
        assert fu._is_likely_archive("image.jpg") is False
        assert fu._is_likely_archive("video.mp4") is False

    def test_error_handling(self):
        """Test error handling returns True as fallback."""
        with patch("os.path.basename", side_effect=Exception("Error")):
            assert fu._is_likely_archive("any_file.zip") is True


class TestCreateGroupsByName:
    """Tests for create_groups_by_name function."""

    def setup_method(self):
        """Set up test files."""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = [
            os.path.join(self.test_dir, "archive1.zip"),
            os.path.join(self.test_dir, "archive2.7z"),
            os.path.join(self.test_dir, "data.rar"),
        ]

        # Create the test files
        for file_path in self.test_files:
            with open(file_path, "wb") as f:
                # Write some binary content that looks like a valid archive
                f.write(b"PK\x03\x04")  # ZIP file signature

    def teardown_method(self):
        """Clean up test files."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch.object(fu, "_is_likely_archive", return_value=True)
    def test_create_groups_basic(self, mock_is_likely):
        """Test basic group creation."""
        with patch.object(ArchiveGroup, "add_file"):
            groups = fu.create_groups_by_name(self.test_files)
            assert len(groups) == 3  # Each file should create its own group

    @patch.object(fu, "_is_likely_archive", return_value=False)
    def test_skip_non_archive_files(self, mock_is_likely):
        """Test skipping non-archive files."""
        warning_callback = Mock()
        groups = fu.create_groups_by_name(self.test_files, warning_callback)
        assert len(groups) == 0
        warning_callback.assert_called_once()
        assert "Skipped" in warning_callback.call_args[0][0]

    @patch.object(fu, "_is_likely_archive", return_value=True)
    @patch.object(fu, "_should_group_files", return_value=True)
    def test_group_related_files(self, mock_should_group, mock_is_likely):
        """Test grouping related files."""
        with patch.object(ArchiveGroup, "add_file"):
            groups = fu.create_groups_by_name(self.test_files)
            # Files should be grouped together due to mocked _should_group_files returning True
            assert len(groups) <= len(self.test_files)

    @patch.object(fu, "_is_likely_archive", return_value=True)
    def test_archive_validation_error(self, mock_is_likely):
        """Test handling archive validation errors."""
        warning_callback = Mock()

        # Mock ArchiveGroup.add_file to raise ValueError (validation error)
        with patch.object(
            ArchiveGroup, "add_file", side_effect=ValueError("Invalid archive")
        ):
            groups = fu.create_groups_by_name(self.test_files, warning_callback)
            assert (
                len(groups) == 0
            )  # All files should be skipped due to validation errors
            warning_callback.assert_called_once()


class TestMoveFilesPreservingStructure:
    """Tests for move_files_preserving_structure function."""

    def setup_method(self):
        """Set up test directory structure."""
        self.source_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()

        # Create nested directory structure
        self.subdir = os.path.join(self.source_dir, "subdir")
        os.makedirs(self.subdir)

        # Create test files
        self.test_files = [
            os.path.join(self.source_dir, "file1.txt"),
            os.path.join(self.subdir, "file2.txt"),
        ]

        for file_path in self.test_files:
            with open(file_path, "w") as f:
                f.write("test content")

    def teardown_method(self):
        """Clean up test directories."""
        shutil.rmtree(self.source_dir, ignore_errors=True)
        shutil.rmtree(self.dest_dir, ignore_errors=True)

    def test_move_files_basic(self):
        """Test basic file moving with structure preservation."""
        result = fu.move_files_preserving_structure(
            self.test_files, self.source_dir, self.dest_dir
        )

        assert len(result) == 2
        assert "file1.txt" in result
        assert (
            os.path.join("subdir", "file2.txt") in result
            or "subdir/file2.txt" in result
        )

        # Check that files were actually moved
        assert os.path.exists(os.path.join(self.dest_dir, "file1.txt"))
        assert os.path.exists(os.path.join(self.dest_dir, "subdir", "file2.txt"))

        # Source files should be gone
        assert not os.path.exists(self.test_files[0])
        assert not os.path.exists(self.test_files[1])

    def test_move_with_callbacks(self):
        """Test moving with progress and success callbacks."""
        progress_callback = Mock()
        success_callback = Mock()

        result = fu.move_files_preserving_structure(
            self.test_files,
            self.source_dir,
            self.dest_dir,
            verbose=True,
            progress_callback=progress_callback,
            success_callback=success_callback,
        )

        assert len(result) == 2
        assert progress_callback.call_count == 2  # Called for each file
        assert success_callback.call_count == 2  # Called for each successful move

    def test_move_with_duplicate_handling(self):
        """Test handling of duplicate filenames."""
        # Create a file in destination that would conflict
        dest_file = os.path.join(self.dest_dir, "file1.txt")
        with open(dest_file, "w") as f:
            f.write("existing content")

        result = fu.move_files_preserving_structure(
            [self.test_files[0]], self.source_dir, self.dest_dir  # Just move one file
        )

        assert len(result) == 1
        # Should have created file1_1.txt or similar
        assert any(
            os.path.exists(os.path.join(self.dest_dir, f"file1_{i}.txt"))
            for i in range(1, 5)
        )

    def test_move_nonexistent_files(self):
        """Test moving nonexistent files."""
        error_callback = Mock()

        result = fu.move_files_preserving_structure(
            ["/nonexistent/file.txt"],
            self.source_dir,
            self.dest_dir,
            error_callback=error_callback,
        )

        assert len(result) == 0
        # Error callback should not be called for nonexistent files (they're just skipped)

    def test_move_with_permission_error(self):
        """Test handling permission errors during move."""
        error_callback = Mock()

        with patch("shutil.move", side_effect=PermissionError("Permission denied")):
            result = fu.move_files_preserving_structure(
                self.test_files,
                self.source_dir,
                self.dest_dir,
                error_callback=error_callback,
            )

            assert len(result) == 0  # No files successfully moved
            assert error_callback.call_count == 2  # Error called for each file


class TestUnconvertedArchive:
    """Tests for archive files signature and detection"""

    def setup_method(self):
        """Set up test with mock archive files."""
        self.test_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test files."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_zip_file_signature(self):
        """Test ZIP file signature detection."""
        zip_file = os.path.join(self.test_dir, "test.zip")
        with open(zip_file, "wb") as f:
            f.write(b"PK\x03\x04")  # ZIP file signature

        assert fu._is_likely_archive(zip_file) is True

    def test_invalid_archive_signature(self):
        """Test invalid archive signature."""
        fake_zip = os.path.join(self.test_dir, "fake.zip")
        with open(fake_zip, "w") as f:
            f.write("This is not a real ZIP file")

        # Should still return True because of the .zip extension
        assert fu._is_likely_archive(fake_zip) is True


if __name__ == "__main__":
    pytest.main([__file__])
