# Change: Add rename history with revert-on-failure

## Why

The cloaked-file detector renames source files in-place (e.g. `1525.zip.001.bin` → `1525.7z.001`) before extraction begins. When extraction later fails — wrong password, corruption, missing volume, crash — the user is left with files whose names no longer match what they originally downloaded, making manual recovery difficult or impossible. We need to track every rename and revert it for any group whose extraction does not succeed, while still letting successful runs benefit from normalized filenames.

## What Changes

- Track every successful uncloak rename (`original_path → renamed_path`) in a new `RenameHistory` component.
- Bind each tracked rename to the `ArchiveGroup` it ends up in after Step 5 grouping.
- On per-group extraction failure (any path that already preserves the original archive), revert all renames bound to that group.
- On per-group extraction success (path that deletes the original archive), drop the group's history entries — no revert needed.
- Persist the in-progress history to a temp JSON file in the input root so an unexpected crash / Ctrl+C still leaves a recoverable record.
- On startup, if a leftover history file is detected, prompt the user `[y/N]` to revert pending renames before scanning.
- Surface revert actions in the existing rich UI (`Reverted N renames for <group>`).

## Capabilities

### New Capabilities
- `rename-history`: Track every uncloak rename, bind tracked renames to archive groups, revert renames for groups whose extraction is preserved (failed), persist history across crashes, and offer recovery on startup.

### Modified Capabilities
<!-- None — existing capabilities (cloaked-rename-collision, multipart-retention, etc.) are not changing their requirements; they are merely instrumented by the new rename-history capability. -->

## Impact

- **New module**: `complex_unzip_tool_v2/modules/rename_history.py` (the `RenameHistory` class + persistence helpers).
- **Modified modules**:
  - `complex_unzip_tool_v2/modules/cloaked_file_detector.py` — `uncloak_file` / `uncloak_files` accept an optional `RenameHistory` and call `history.record(...)` on each successful rename (including duplicate-collision renames).
  - `complex_unzip_tool_v2/modules/file_utils.py` — `uncloak_file_extensions` / `uncloak_file_extension_for_groups` pass the history through to the detector.
  - `complex_unzip_tool_v2/main.py` — instantiate `RenameHistory`, call `bind` after Step 5, call `revert_group` / `clear_group` on every Step 7/8 success/failure exit point, call `finalize` at end of run, and prompt for crash-recovery on startup.
- **New artifacts on disk**: `<input-root>/.unzip-rename-history.tmp.json` while a run is in progress; deleted on successful completion or after the user accepts a recovery prompt.
- **No new dependencies** — uses stdlib `json`.
- **Tests**: new `tests/test_rename_history.py` for the class; new integration tests in `tests/test_main.py` verifying revert on failure and no-revert on success.
