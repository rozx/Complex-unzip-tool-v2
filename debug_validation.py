#!/usr/bin/env python3

import sys

sys.path.insert(0, ".")

from complex_unzip_tool_v2.modules.archive_utils import (
    is_valid_archive,
    readArchiveContentWith7z,
)
from complex_unzip_tool_v2.classes.ArchiveTypes import ArchivePasswordError


def test_file_validation():
    test_file = r"e:\BaiduNDDownloads\1765.r1ar"
    print(f"Testing validation of: {test_file}")

    try:
        # Test the validation function
        is_valid = is_valid_archive(test_file)
        print(f"is_valid_archive returned: {is_valid}")

        # Test the underlying read function directly
        print("\nTesting readArchiveContentWith7z directly...")
        content = readArchiveContentWith7z(test_file)
        print(f"Content read successfully: {len(content)} items")

    except ArchivePasswordError as e:
        print(f"ArchivePasswordError caught: {e}")
        print("This should make is_valid_archive return True")
    except Exception as e:
        print(f"Other exception caught: {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_file_validation()
