## Context

Step 4 of `extract_files` calls `cloaked_file_detector.uncloak_files`, which performs in-place `os.rename` on every file the rule engine matches (e.g. `1525.zip.001.bin → 1525.7z.001`). These renames are committed to disk *before* Step 5 even groups the files, and certainly before Step 7/8 know whether extraction will succeed.

`extract_files` already has well-defined success/failure exit points per `ArchiveGroup`:
- success → `safe_remove(group.mainArchiveFile / group.files...)` deletes originals
- failure → original files are intentionally retained for the user to inspect

The retained files are however no longer recognizable, because their names were changed at Step 4. The user's TODO calls this out:
> "Failed to rename files will be reverted back to their original names."

The system already has the right deletion-vs-keep policy in `_should_delete_original_archives(extract_result)`. We extend that policy: **whenever originals are kept, also revert the rename history for that group**.

## Goals / Non-Goals

**Goals:**
- Track every successful uncloak rename in memory and on disk.
- Bind every tracked rename to exactly one `ArchiveGroup` (its current home after Step 5 grouping).
- Revert all renames bound to a group whenever the group's outcome would have preserved the originals.
- Drop history entries cleanly for groups whose originals are deleted (success path).
- Survive crashes / Ctrl+C: the JSON record on disk is enough to recover original filenames in a subsequent run.
- Surface revert actions in the existing rich UI without rewriting it.

**Non-Goals:**
- Tracking moves done by `add_file_to_groups`, `relocate_multipart_parts_from_directory`, `_move_parts_next_to_primary`, `move_files_preserving_structure`. These are within-extraction operations; if extraction fails for the group, those files stay where Step 7/8 left them — that is the existing tool behavior we do not change.
- Tracking renames inside extracted output (the `unzipped/` tree) — those files are derived artifacts, not user inputs.
- Per-file selective revert. Revert is per-group, all-or-nothing.
- Cross-run history persistence beyond crash recovery (no long-term log, no audit trail).

## Decisions

### D1 — Track per file, bind per group
**Decision**: `RenameHistory.record(original, renamed)` is called by the detector immediately after each `os.rename` succeeds. The entry is unbound at this point. After Step 5 builds groups, `main` calls `RenameHistory.bind(renamed_path → group_key)` for every file in every group; entries that map to a known renamed_path get attached to that group.

**Why**:
- The detector runs before grouping exists, so it cannot know the group at record-time.
- Walking groups once after Step 5 is O(N) and gives us 100% binding coverage without changing the order of Step 4 / Step 5.
- An unbound entry at end-of-run means the renamed file vanished or never landed in any group → it gets reverted defensively at finalize time (treating "lost track" as "revert to be safe").

**Alternatives considered**:
- *Move uncloak into Step 5 per group*: invasive — uncloaking influences which files even look like archives, so reordering risks regressions.
- *Pass the group object to the detector*: would require either two passes or speculative grouping; doubles complexity for no benefit.

### D2 — Use `_should_delete_original_archives` as the revert gate
**Decision**: Wherever `main.extract_files` currently checks `_should_delete_original_archives(result)` to decide between deleting or preserving originals, also branch the history:
- delete originals → `history.clear_group(group_key)`
- keep originals → `history.revert_group(group_key)`

For exception paths that already preserve originals (the `except` blocks in Step 7/8), call `history.revert_group(group_key)` in the same `finally` cleanup region as `groups.remove(group)`.

**Why**: Reuses the single source of truth for "did this group succeed enough to delete originals". No new policy code; revert and delete stay in lockstep forever.

### D3 — Persistence format and location
**Decision**: A single JSON file `<input_root>/.unzip-rename-history.tmp.json` written eagerly on every `record`, `revert_group`, `clear_group`. Schema:
```json
{
  "version": 1,
  "input_root": "E:\\testDir - Copy",
  "started_at": "2026-04-27T21:30:00",
  "entries": [
    {"original": "...\\1525.zip.001.bin", "renamed": "...\\1525.7z.001", "group": "testDir-1525"}
  ]
}
```
- Located in the **first** input path (or its containing dir if it's a file). One file per run.
- `input_root` field detects "wrong directory" mistakes on recovery.
- Atomic write: write to `.unzip-rename-history.tmp.json.tmp`, then `os.replace` to final.
- On `finalize` (clean end of run with no outstanding entries), the file is deleted.

**Why JSON**: stdlib, human-readable for debugging, schema-versioned for future expansion.
**Why eager**: any crash between `record` and program exit must leave a valid file. The cost is a few KB-sized writes per uncloak — negligible.
**Why one file per input root**: parallel runs against different folders won't collide; a second run against the same folder will detect the leftover and prompt before clobbering.

### D4 — Crash-recovery prompt
**Decision**: At the start of `extract_files`, *before* Step 4, call `RenameHistory.load_pending(input_root)`. If a file exists and its `entries` are non-empty:
- Print a warning summarizing what will be reverted.
- Prompt `[y/N]` (default N to be safe).
- On `y`: revert each entry that still maps to an existing renamed file on disk; delete the history file; then continue with normal flow.
- On `n`: leave the file in place, continue normally (a fresh history file for the new run will overwrite it via the same `os.replace` path).

**Why default N**: pre-existing leftovers might predate manual user fixes; we should not auto-rollback without consent.

### D5 — Duplicate-collision renames are also tracked
**Decision**: When `_build_collision_path` triggers and `os.rename(file_path, duplicate_path)` succeeds, that rename is also recorded. On revert, it goes back to the original cloaked filename.

**Why**: collision renames are still user-facing renames of source files. If the group ultimately fails, the user wants to see their original `9.7z(1).001` again, not `9.7z(1)__duplicate_<token>.001`.

### D6 — Revert ignores files that no longer exist
**Decision**: `revert_group` attempts each `os.rename(renamed → original)`. If `renamed` no longer exists (e.g., 7-Zip moved/deleted it during a partial extraction), log an info message and skip — never raise. If `original` already exists at revert time (would clobber), use the same `_build_collision_path`-style suffix to choose a unique fallback name.

**Why**: revert is a best-effort safety net. Hard-failing during cleanup defeats the purpose.

### D7 — UI integration
**Decision**: `RenameHistory.revert_group` returns the count of files reverted plus a short list of `(renamed_basename, original_basename)` for the first ~5 entries. `main` prints these through existing `print_warning` / `print_info`:
```
⚠ Reverted 3 renames for group testDir-1525:
    1525.7z.001 → 1525.zip.001.bin
    ...
```

## Risks / Trade-offs

- **Risk**: Multiple input paths under different roots — picking the "first" for the history file location is arbitrary.
  - **Mitigation**: Always use the first path's directory; document this; the input_root field in JSON makes mismatches detectable on recovery.
- **Risk**: Eager-write JSON adds I/O on every uncloak (typically dozens to hundreds per run).
  - **Mitigation**: Files are tiny (a few KB total even for hundreds of entries). Not on a hot path. Acceptable.
- **Risk**: A user manually fixes things between runs and then accepts a stale recovery prompt.
  - **Mitigation**: Prompt defaults to N. Revert checks file existence before renaming. Clobber-safe via `_build_collision_path`-style fallback.
- **Risk**: Crash *during* a revert leaves a partially-reverted state.
  - **Mitigation**: Each `revert_group` rewrites the JSON after each successful per-file rename, removing that entry. A second run will resume reverting only the entries still on disk.
- **Trade-off**: We accept "revert all-or-nothing per group" rather than per-file fine-grain. Simpler API; matches the per-group success/failure model the rest of the tool uses.
