import os
import tempfile
from unittest.mock import patch

import complex_unzip_tool_v2.main as main
from complex_unzip_tool_v2.modules import const


def _touch(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"")


def test_multipart_parts_not_deleted_on_failure(tmp_path):
    # Create a fake multipart set: ZIP spanned missing .z01
    base_dir = tmp_path
    # Group name derived by file_utils.create_groups_by_name, base filenames should group
    zip_main = os.path.join(base_dir, "set.zip")
    zip_z01 = os.path.join(base_dir, "set.z01")

    # Only create main part, simulate missing continuation
    _touch(zip_main)
    # Do NOT create zip_z01 to simulate failure

    # Patch extract_nested_archives to simulate failure result
    failure_result = {
        "success": False,
        "final_files": [],
        "extracted_archives": [],
        "errors": ["missing continuation"],
        "password_failed_archives": [],
        "user_provided_passwords": [],
        "password_used": {},
    }

    removed = []

    def fake_safe_remove(path, use_recycle_bin=True, error_callback=None):
        removed.append(path)
        return True

    with (
        patch(
            "complex_unzip_tool_v2.modules.archive_utils.extract_nested_archives",
            return_value=failure_result,
        ),
        patch(
            "complex_unzip_tool_v2.modules.file_utils.safe_remove",
            side_effect=fake_safe_remove,
        ),
        patch("complex_unzip_tool_v2.main._ask_for_user_input_and_exit", lambda: None),
    ):
        # Run extraction on the directory
        main.extract_files([str(base_dir)], use_recycle_bin=False)

    # Assert source parts still exist
    assert os.path.exists(zip_main)
    # Continuation never existed; key assertion is no deletion calls happened on source parts
    assert zip_main not in removed


def test_rar_parts_not_deleted_on_failure(tmp_path):
    base_dir = tmp_path
    rar_part1 = os.path.join(base_dir, "archive.part1.rar")
    rar_part2 = os.path.join(base_dir, "archive.part2.rar")

    _touch(rar_part1)
    # Missing part2 to force failure

    failure_result = {
        "success": False,
        "final_files": [],
        "extracted_archives": [],
        "errors": ["missing part2"],
        "password_failed_archives": [],
        "user_provided_passwords": [],
        "password_used": {},
    }

    removed = []

    def fake_safe_remove(path, use_recycle_bin=True, error_callback=None):
        removed.append(path)
        return True

    with (
        patch(
            "complex_unzip_tool_v2.modules.archive_utils.extract_nested_archives",
            return_value=failure_result,
        ),
        patch(
            "complex_unzip_tool_v2.modules.file_utils.safe_remove",
            side_effect=fake_safe_remove,
        ),
        patch("complex_unzip_tool_v2.main._ask_for_user_input_and_exit", lambda: None),
    ):
        main.extract_files([str(base_dir)], use_recycle_bin=False)

    assert os.path.exists(rar_part1)
    assert rar_part1 not in removed
