import builtins
import types
import importlib

import complex_unzip_tool_v2.modules.archive_utils as au
from complex_unzip_tool_v2.classes.ArchiveTypes import (
    ArchivePasswordError, ArchiveCorruptedError, ArchiveUnsupportedError,
    ArchiveFileInfo
)


def test_parse_7z_list_output_basic():
    sample = (
        "----------\n"
        "Path = folder/file.txt\n"
        "Folder = -\n"
        "Size = 123\n"
        "Packed Size = 100\n"
        "Modified = 2024-01-01 12:00:00\n"
        "Attributes = A\n"
        "CRC = 1234ABCD\n"
        "Method = LZMA2\n"
    )
    files = au._parse7zListOutput(sample)
    assert len(files) == 1
    f = files[0]
    assert f["name"] == "folder/file.txt"
    assert f["size"] == 123
    assert f["packed_size"] == 100
    assert f["type"] == "File"


def test_raise_for_7z_error_password():
    try:
        au._raise_for_7z_error(2, "Wrong password", "archive.7z")
    except ArchivePasswordError:
        pass
    else:
        assert False, "Expected ArchivePasswordError"


def test_raise_for_7z_error_corrupted():
    try:
        au._raise_for_7z_error(2, "Data error in encrypted file", "archive.7z")
    except ArchiveCorruptedError:
        pass
    else:
        assert False, "Expected ArchiveCorruptedError"


def test_raise_for_7z_error_unsupported():
    try:
        au._raise_for_7z_error(2, "Unsupported method", "archive.7z")
    except ArchiveUnsupportedError:
        pass
    else:
        assert False, "Expected ArchiveUnsupportedError"


def test_is_valid_archive_false_on_garbage(monkeypatch):
    # Simulate readArchiveContentWith7z raising ArchiveUnsupportedError
    def fake_read(*args, **kwargs):
        raise ArchiveUnsupportedError("not an archive")

    monkeypatch.setattr(au, "readArchiveContentWith7z", fake_read)
    assert au.is_valid_archive("not.zip") is False


def test_is_valid_archive_true_on_password_protected(monkeypatch):
    # Simulate readArchiveContentWith7z raising ArchivePasswordError
    def fake_read(*args, **kwargs):
        raise ArchivePasswordError("needs password")

    monkeypatch.setattr(au, "readArchiveContentWith7z", fake_read)
    assert au.is_valid_archive("protected.7z") is True


def test_build_7z_extract_cmd():
    cmd = au._build_7z_extract_cmd(
        seven_zip_path="7z.exe",
        password="secret",
        output_path="/out",
        archive_path="archive.zip",
        overwrite=True,
        specific_files=["file1.txt", "file2.txt"]
    )
    
    expected = [
        "7z.exe", "x", "-psecret", "-o/out", "-y", "archive.zip", "file1.txt", "file2.txt"
    ]
    assert cmd == expected


def test_build_7z_extract_cmd_no_overwrite():
    cmd = au._build_7z_extract_cmd(
        seven_zip_path="7z.exe",
        password="",
        output_path="/out",
        archive_path="archive.zip",
        overwrite=False
    )
    
    expected = [
        "7z.exe", "x", "-p", "-o/out", "-aos", "archive.zip"
    ]
    assert cmd == expected
