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
