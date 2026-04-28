"""Unit tests for RenameHistory."""

import json
import os
from pathlib import Path

import pytest

from complex_unzip_tool_v2.modules.rename_history import (
    HISTORY_FILENAME,
    RenameHistory,
)


def _make(tmp_path: Path, name: str, content: bytes = b"x") -> str:
    p = tmp_path / name
    p.write_bytes(content)
    return str(p)


class TestRecordPersist:
    def test_record_writes_to_disk(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))

        history_file = tmp_path / HISTORY_FILENAME
        assert history_file.exists()

        data = json.loads(history_file.read_text(encoding="utf-8"))
        assert data["version"] == 1
        assert len(data["entries"]) == 1
        assert data["entries"][0]["original"].endswith("a.bin")
        assert data["entries"][0]["renamed"].endswith("a.7z.001")
        assert data["entries"][0]["group"] is None

    def test_multiple_records_append(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))
        h.record(str(tmp_path / "b.bin"), str(tmp_path / "b.7z.002"))

        data = json.loads((tmp_path / HISTORY_FILENAME).read_text(encoding="utf-8"))
        assert len(data["entries"]) == 2


class TestBind:
    def test_bind_attaches_group(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        renamed = str(tmp_path / "a.7z.001")
        h.record(str(tmp_path / "a.bin"), renamed)

        bound = h.bind(renamed, "group-1")
        assert bound is True
        assert h.entries[0]["group"] == "group-1"

        # Persisted
        data = json.loads((tmp_path / HISTORY_FILENAME).read_text(encoding="utf-8"))
        assert data["entries"][0]["group"] == "group-1"

    def test_bind_unknown_path(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))

        bound = h.bind(str(tmp_path / "other.zip"), "group-x")
        assert bound is False

    def test_bind_does_not_double_bind(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        renamed = str(tmp_path / "a.7z.001")
        h.record(str(tmp_path / "a.bin"), renamed)
        assert h.bind(renamed, "g1") is True
        # Second call should not overwrite (already bound)
        assert h.bind(renamed, "g2") is False
        assert h.entries[0]["group"] == "g1"


class TestRevertGroup:
    def test_revert_renames_files_back(self, tmp_path):
        original = _make(tmp_path, "cloaked.bin")
        renamed = str(tmp_path / "real.7z.001")
        os.rename(original, renamed)

        h = RenameHistory(str(tmp_path))
        h.record(original, renamed)
        h.bind(renamed, "g1")

        count, sample = h.revert_group("g1")
        assert count == 1
        assert os.path.exists(original)
        assert not os.path.exists(renamed)
        assert sample == [("real.7z.001", "cloaked.bin")]
        assert h.entries == []

    def test_revert_skips_missing_renamed(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        # Renamed file never existed
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))
        h.bind(str(tmp_path / "a.7z.001"), "g1")

        count, sample = h.revert_group("g1")
        assert count == 0
        assert sample == []
        assert h.entries == []  # entry was dropped

    def test_revert_collision_safe_when_original_exists(self, tmp_path):
        original = str(tmp_path / "name.7z.001")
        renamed = str(tmp_path / "name.7z.002")
        # Pretend extraction left a file at the original path
        Path(original).write_bytes(b"existing")
        Path(renamed).write_bytes(b"renamed")

        h = RenameHistory(str(tmp_path))
        h.record(original, renamed)
        h.bind(renamed, "g1")

        count, sample = h.revert_group("g1")
        assert count == 1
        # Original kept untouched
        assert Path(original).read_bytes() == b"existing"
        # Renamed file went to a __reverted_<token> sibling
        assert not Path(renamed).exists()
        siblings = [
            p.name for p in tmp_path.iterdir() if "__reverted_" in p.name
        ]
        assert len(siblings) == 1
        assert sample[0][0] == "name.7z.002"
        assert "__reverted_" in sample[0][1]

    def test_revert_only_targets_requested_group(self, tmp_path):
        a_orig = _make(tmp_path, "a.bin")
        b_orig = _make(tmp_path, "b.bin")
        a_ren = str(tmp_path / "a.7z.001")
        b_ren = str(tmp_path / "b.7z.001")
        os.rename(a_orig, a_ren)
        os.rename(b_orig, b_ren)

        h = RenameHistory(str(tmp_path))
        h.record(a_orig, a_ren)
        h.record(b_orig, b_ren)
        h.bind(a_ren, "g1")
        h.bind(b_ren, "g2")

        count, _ = h.revert_group("g1")
        assert count == 1
        assert os.path.exists(a_orig)
        assert os.path.exists(b_ren)  # untouched
        assert len(h.entries) == 1
        assert h.entries[0]["group"] == "g2"


class TestClearGroup:
    def test_clear_drops_entries_without_renaming(self, tmp_path):
        original = _make(tmp_path, "a.bin")
        renamed = str(tmp_path / "a.7z.001")
        os.rename(original, renamed)

        h = RenameHistory(str(tmp_path))
        h.record(original, renamed)
        h.bind(renamed, "g1")

        cleared = h.clear_group("g1")
        assert cleared == 1
        assert os.path.exists(renamed)  # still renamed!
        assert not os.path.exists(original)
        assert h.entries == []

    def test_clear_unknown_group_returns_zero(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))
        h.bind(str(tmp_path / "a.7z.001"), "g1")

        cleared = h.clear_group("nonexistent")
        assert cleared == 0
        assert len(h.entries) == 1


class TestRevertUnbound:
    def test_revert_unbound_only_targets_unbound(self, tmp_path):
        a_orig = _make(tmp_path, "a.bin")
        b_orig = _make(tmp_path, "b.bin")
        a_ren = str(tmp_path / "a.7z.001")
        b_ren = str(tmp_path / "b.7z.001")
        os.rename(a_orig, a_ren)
        os.rename(b_orig, b_ren)

        h = RenameHistory(str(tmp_path))
        h.record(a_orig, a_ren)
        h.record(b_orig, b_ren)
        h.bind(a_ren, "g1")  # only `a` is bound

        count, _ = h.revert_unbound()
        assert count == 1
        assert os.path.exists(b_orig)  # b reverted
        assert os.path.exists(a_ren)  # a still renamed (bound, not unbound)


class TestFinalize:
    def test_finalize_deletes_when_empty(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))
        h.clear_group("nonexistent")  # entries still there
        h.entries.clear()
        h.finalize()

        assert not (tmp_path / HISTORY_FILENAME).exists()

    def test_finalize_preserves_when_entries_remain(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))
        h.finalize()

        assert (tmp_path / HISTORY_FILENAME).exists()


class TestLoadPending:
    def test_round_trip(self, tmp_path):
        h1 = RenameHistory(str(tmp_path))
        h1.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))
        h1.bind(str(tmp_path / "a.7z.001"), "g1")

        h2 = RenameHistory.load_pending(str(tmp_path))
        assert h2 is not None
        assert len(h2.entries) == 1
        assert h2.entries[0]["group"] == "g1"
        assert h2.root_matches(str(tmp_path))

    def test_returns_none_when_no_file(self, tmp_path):
        assert RenameHistory.load_pending(str(tmp_path)) is None

    def test_returns_none_when_empty_entries(self, tmp_path):
        # Manually drop a JSON file with no entries
        (tmp_path / HISTORY_FILENAME).write_text(
            json.dumps({"version": 1, "input_root": str(tmp_path), "entries": []}),
            encoding="utf-8",
        )
        assert RenameHistory.load_pending(str(tmp_path)) is None

    def test_returns_none_when_invalid_json(self, tmp_path):
        (tmp_path / HISTORY_FILENAME).write_text("garbage{not json", encoding="utf-8")
        assert RenameHistory.load_pending(str(tmp_path)) is None

    def test_root_matches_detects_mismatch(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))

        loaded = RenameHistory.load_pending(str(tmp_path))
        assert loaded.root_matches(str(tmp_path)) is True
        assert loaded.root_matches(str(tmp_path / "different")) is False


class TestAtomicWrite:
    def test_no_temp_file_remains_after_normal_write(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))

        tmp_file = tmp_path / (HISTORY_FILENAME + ".tmp")
        assert not tmp_file.exists()
        assert (tmp_path / HISTORY_FILENAME).exists()

    def test_main_file_unchanged_when_persist_fails_mid_write(self, tmp_path, monkeypatch):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))
        original_contents = (tmp_path / HISTORY_FILENAME).read_bytes()

        # Force os.replace to fail; the main file should be untouched
        def boom(*args, **kwargs):
            raise OSError("simulated")

        monkeypatch.setattr("os.replace", boom)
        h.record(str(tmp_path / "b.bin"), str(tmp_path / "b.7z.001"))

        # Main file unchanged because os.replace failed
        assert (tmp_path / HISTORY_FILENAME).read_bytes() == original_contents


class TestDeleteFile:
    def test_delete_file_removes_history_file(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record(str(tmp_path / "a.bin"), str(tmp_path / "a.7z.001"))

        h.delete_file()
        assert not (tmp_path / HISTORY_FILENAME).exists()

    def test_delete_file_safe_when_missing(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        # No record() called → no file
        h.delete_file()  # should not raise


class TestBoundGroupKeys:
    def test_returns_unique_keys_in_order(self, tmp_path):
        h = RenameHistory(str(tmp_path))
        h.record("/x/a.bin", "/x/a.7z.001")
        h.record("/x/b.bin", "/x/b.7z.001")
        h.record("/x/c.bin", "/x/c.7z.001")
        h.bind("/x/a.7z.001", "g1")
        h.bind("/x/b.7z.001", "g2")
        h.bind("/x/c.7z.001", "g1")

        assert h.bound_group_keys() == ["g1", "g2"]


if __name__ == "__main__":
    pytest.main([__file__])
