import os

import complex_unzip_tool_v2.main as main
from complex_unzip_tool_v2.modules import const


def test_contained_multipart_parts_preserved_to_output_when_extraction_fails(
    monkeypatch, tmp_path
):
    """Regression: multipart parts inside a container must not be deleted by temp cleanup."""
    base_dir = tmp_path
    outer = base_dir / "outer.7z"
    outer.write_bytes(b"dummy")

    # Prevent interactive exit prompt
    monkeypatch.setattr(main, "_ask_for_user_input_and_exit", lambda: None)

    # Do not delete originals in this test.
    monkeypatch.setattr(main.file_utils, "safe_remove", lambda *a, **k: False)

    def fake_is_valid(path, *args, **kwargs):
        _ = (args, kwargs)
        return os.path.basename(path) in {"outer.7z", "MySet.7z.001"}

    monkeypatch.setattr(main.archive_utils, "is_valid_archive", fake_is_valid)

    def fake_extract(archive_path: str, output_path: str, *args, **kwargs) -> bool:
        _ = (args, kwargs)
        os.makedirs(output_path, exist_ok=True)
        base = os.path.basename(archive_path)
        if base == "outer.7z":
            # Create a contained multipart set where .002 is in a different folder.
            d1 = os.path.join(output_path, "A")
            d2 = os.path.join(output_path, "B")
            os.makedirs(d1, exist_ok=True)
            os.makedirs(d2, exist_ok=True)
            with open(os.path.join(d1, "MySet.7z.001"), "wb") as f:
                f.write(b"part1")
            with open(os.path.join(d2, "MySet.7z.002"), "wb") as f:
                f.write(b"part2")
            return True
        if base == "MySet.7z.001":
            # Always fail so the parts must be preserved to output.
            raise main.archive_utils.ArchiveError("Missing volume")
        return True

    monkeypatch.setattr(main.archive_utils, "extractArchiveWith7z", fake_extract)

    main.extract_files([str(base_dir)], use_recycle_bin=False)

    # Output folder is created under the processed directory.
    out_dir = base_dir / const.OUTPUT_FOLDER
    assert out_dir.exists()

    found_002 = False
    for root, _dirs, files in os.walk(out_dir):
        if "MySet.7z.002" in files:
            found_002 = True
            break
    assert found_002 is True


def test_should_delete_original_archives_false_when_password_failed_archives_present():
    assert (
        main._should_delete_original_archives(
            {"success": True, "password_failed_archives": ["a.7z"]}
        )
        is False
    )


def test_should_delete_original_archives_true_when_no_password_failed_archives():
    assert main._should_delete_original_archives({"success": True}) is True


def test_step7_autogroups_contained_zip_spanned_and_step8_processes_it(
    monkeypatch, tmp_path
):
    """Integration: Step 7 auto-groups contained .zip+.z01 so Step 8 extracts it."""
    base_dir = tmp_path
    outer = base_dir / "outer.zip"
    outer.write_bytes(b"dummy")

    # Prevent interactive exit prompt
    monkeypatch.setattr(main, "_ask_for_user_input_and_exit", lambda: None)

    # Do not delete originals in this test.
    monkeypatch.setattr(main.file_utils, "safe_remove", lambda *a, **k: False)

    # Treat our archives as valid
    monkeypatch.setattr(main.archive_utils, "is_valid_archive", lambda *a, **k: True)

    called: list[str] = []

    def fake_extract_nested_archives(archive_path: str, output_path: str, *a, **k):
        called.append(os.path.basename(archive_path))
        os.makedirs(output_path, exist_ok=True)

        base = os.path.basename(archive_path)
        if base == "outer.zip":
            # Simulate a container that yields a spanned ZIP set.
            p_zip = os.path.join(output_path, "Set.zip")
            p_z01 = os.path.join(output_path, "Set.z01")
            with open(p_zip, "wb") as f:
                f.write(b"zip")
            with open(p_z01, "wb") as f:
                f.write(b"z01")
            return {
                "success": True,
                "final_files": [p_zip, p_z01],
                "extracted_archives": [],
                "errors": [],
                "password_failed_archives": [],
                "user_provided_passwords": [],
                "password_used": {},
            }

        # For the contained set (Step 8), just report success.
        return {
            "success": True,
            "final_files": [],
            "extracted_archives": [],
            "errors": [],
            "password_failed_archives": [],
            "user_provided_passwords": [],
            "password_used": {},
        }

    monkeypatch.setattr(
        main.archive_utils, "extract_nested_archives", fake_extract_nested_archives
    )

    main.extract_files([str(base_dir)], use_recycle_bin=False)

    out_dir = base_dir / const.OUTPUT_FOLDER
    assert (out_dir / "Set.zip").exists()
    assert (out_dir / "Set.z01").exists()

    # Most important assertion: Step 8 attempted to process the contained main archive.
    assert "Set.zip" in called


# ---------------------------------------------------------------------------
# Rename history integration
# ---------------------------------------------------------------------------


def _setup_cloaked_input(tmp_path):
    """Create a fake cloaked input that the detector will rename."""
    cloaked = tmp_path / "1525.zip(1).001"
    cloaked.write_bytes(b"PK\x03\x04dummy-7z-data")
    return cloaked


def test_rename_history_reverts_on_extraction_failure(monkeypatch, tmp_path):
    """When extraction fails, uncloak renames must be reverted so the user
    sees the original filenames."""
    from complex_unzip_tool_v2.modules.rename_history import HISTORY_FILENAME

    cloaked = _setup_cloaked_input(tmp_path)

    # Stub uncloak to perform a real rename and record it.
    def fake_uncloak(file_paths, history=None, **kwargs):
        result = []
        for p in file_paths:
            base = os.path.basename(p)
            if base == "1525.zip(1).001":
                new_path = os.path.join(os.path.dirname(p), "1525.7z.001")
                os.rename(p, new_path)
                if history is not None:
                    history.record(p, new_path)
                result.append(new_path)
            else:
                result.append(p)
        return result

    monkeypatch.setattr(main.file_utils, "uncloak_file_extensions", fake_uncloak)

    # Stub extraction to always fail.
    failure_result = {
        "success": False,
        "final_files": [],
        "extracted_archives": [],
        "errors": ["forced failure"],
        "password_failed_archives": [],
        "user_provided_passwords": [],
        "password_used": {},
    }
    monkeypatch.setattr(
        main.archive_utils, "extract_nested_archives", lambda *a, **k: failure_result
    )
    monkeypatch.setattr(main, "_ask_for_user_input_and_exit", lambda: None)

    main.extract_files([str(tmp_path)], use_recycle_bin=False)

    # The original cloaked filename must be back.
    assert cloaked.exists(), "rename was not reverted on failure"
    assert not (tmp_path / "1525.7z.001").exists()
    # History file removed because all entries were reverted
    assert not (tmp_path / HISTORY_FILENAME).exists()


def test_rename_history_cleared_on_extraction_success(monkeypatch, tmp_path):
    """When extraction succeeds, originals are deleted and history is cleared
    (the renamed files do not get reverted)."""
    from complex_unzip_tool_v2.modules.rename_history import HISTORY_FILENAME

    # Use a single-archive cloaked file (.7z) so Step 7's success path runs
    # safe_remove(group.mainArchiveFile) unconditionally.
    cloaked = tmp_path / "1525.7z隐藏"
    cloaked.write_bytes(b"PK\x03\x04dummy")
    renamed_basename = "1525.7z"

    def fake_uncloak(file_paths, history=None, **kwargs):
        result = []
        for p in file_paths:
            base = os.path.basename(p)
            if base == "1525.7z隐藏":
                new_path = os.path.join(os.path.dirname(p), renamed_basename)
                os.rename(p, new_path)
                if history is not None:
                    history.record(p, new_path)
                result.append(new_path)
            else:
                result.append(p)
        return result

    monkeypatch.setattr(main.file_utils, "uncloak_file_extensions", fake_uncloak)

    # Stub extraction to succeed (no nested files needed for Step 7 success).
    success_result = {
        "success": True,
        "final_files": [],
        "extracted_archives": [],
        "errors": [],
        "password_failed_archives": [],
        "user_provided_passwords": [],
        "password_used": {},
    }
    monkeypatch.setattr(
        main.archive_utils, "extract_nested_archives", lambda *a, **k: success_result
    )
    # Stub safe_remove so it actually removes the file (mimicking real success)
    monkeypatch.setattr(
        main.file_utils, "safe_remove", lambda path, **k: (os.remove(path) or True)
    )
    monkeypatch.setattr(main, "_ask_for_user_input_and_exit", lambda: None)

    main.extract_files([str(tmp_path)], use_recycle_bin=False)

    # Renamed file was deleted by safe_remove during success path
    assert not (tmp_path / renamed_basename).exists()
    # Original was NOT restored (because the file was deleted, not preserved)
    assert not cloaked.exists()
    # History file removed (no entries left)
    assert not (tmp_path / HISTORY_FILENAME).exists()


def test_rename_history_recovery_prompt_yes_reverts(monkeypatch, tmp_path):
    """A leftover history file from a previous run can be reverted on prompt 'y'."""
    from complex_unzip_tool_v2.modules.rename_history import (
        HISTORY_FILENAME,
        RenameHistory,
    )

    # Pre-create a renamed file and a leftover history pointing to it
    renamed = tmp_path / "leftover.7z.001"
    original = tmp_path / "leftover.bin"
    renamed.write_bytes(b"data")

    h = RenameHistory(str(tmp_path))
    h.record(str(original), str(renamed))
    h.bind(str(renamed), "previous-run-group")

    assert (tmp_path / HISTORY_FILENAME).exists()

    # Patch input() to answer 'y' to the recovery prompt.
    monkeypatch.setattr("builtins.input", lambda *a, **k: "y")
    monkeypatch.setattr(main, "_ask_for_user_input_and_exit", lambda: None)
    # No-op extraction so we just exercise the recovery path.
    monkeypatch.setattr(
        main.archive_utils,
        "extract_nested_archives",
        lambda *a, **k: {
            "success": True,
            "final_files": [],
            "extracted_archives": [],
            "errors": [],
            "password_failed_archives": [],
            "user_provided_passwords": [],
            "password_used": {},
        },
    )
    monkeypatch.setattr(main.file_utils, "safe_remove", lambda *a, **k: False)
    monkeypatch.setattr(main.file_utils, "uncloak_file_extensions", lambda paths, **k: paths)

    main.extract_files([str(tmp_path)], use_recycle_bin=False)

    # Recovery happened: original restored, renamed gone
    assert original.exists()
    assert not renamed.exists()
    # The leftover history file was deleted (recovery path) and the new run
    # did not create a fresh one (no records during run).
    assert not (tmp_path / HISTORY_FILENAME).exists()


def test_rename_history_recovery_prompt_no_keeps_file(monkeypatch, tmp_path):
    """Answering 'n' to recovery leaves the renamed file in place."""
    from complex_unzip_tool_v2.modules.rename_history import (
        HISTORY_FILENAME,
        RenameHistory,
    )

    renamed = tmp_path / "leftover.7z.001"
    original = tmp_path / "leftover.bin"
    renamed.write_bytes(b"data")

    h = RenameHistory(str(tmp_path))
    h.record(str(original), str(renamed))
    h.bind(str(renamed), "previous-run-group")

    monkeypatch.setattr("builtins.input", lambda *a, **k: "n")
    monkeypatch.setattr(main, "_ask_for_user_input_and_exit", lambda: None)
    monkeypatch.setattr(
        main.archive_utils,
        "extract_nested_archives",
        lambda *a, **k: {
            "success": True,
            "final_files": [],
            "extracted_archives": [],
            "errors": [],
            "password_failed_archives": [],
            "user_provided_passwords": [],
            "password_used": {},
        },
    )
    monkeypatch.setattr(main.file_utils, "safe_remove", lambda *a, **k: False)
    monkeypatch.setattr(main.file_utils, "uncloak_file_extensions", lambda paths, **k: paths)

    main.extract_files([str(tmp_path)], use_recycle_bin=False)

    # Renamed kept, original not restored
    assert renamed.exists()
    assert not original.exists()
    # History file deleted by finalize() since the new run did not record anything
    # (so the in-memory history was empty by end of run)
    assert not (tmp_path / HISTORY_FILENAME).exists()
