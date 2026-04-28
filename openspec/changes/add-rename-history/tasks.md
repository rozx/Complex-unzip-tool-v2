## 1. Core RenameHistory module

- [x] 1.1 Create `complex_unzip_tool_v2/modules/rename_history.py` with the `RenameHistory` class skeleton (constructor accepts `input_root: str`, holds `entries: list[dict]`, holds `started_at` ISO timestamp).
- [x] 1.2 Implement `record(original: str, renamed: str)` — append entry (initially with `group=None`), then atomically write JSON to `<input_root>/.unzip-rename-history.tmp.json`.
- [x] 1.3 Implement `bind(renamed_path: str, group_key: str)` — find entry by `renamed` path and set its `group`; persist.
- [x] 1.4 Implement `revert_group(group_key: str) -> tuple[int, list[tuple[str, str]]]` — for every entry bound to that group, attempt `os.rename(renamed → original)`; skip missing renamed files; use collision-safe fallback when original already exists; remove successfully-reverted entries; persist after each entry; return `(count, sample)` for UI.
- [x] 1.5 Implement `clear_group(group_key: str)` — drop all entries bound to that group; persist.
- [x] 1.6 Implement `revert_unbound() -> int` — revert any entries whose `group is None` at finalize time.
- [x] 1.7 Implement `finalize()` — if no entries remain, delete the JSON file; otherwise leave it for next-run recovery.
- [x] 1.8 Implement `RenameHistory.load_pending(input_root: str) -> RenameHistory | None` classmethod — return a populated instance if a leftover file exists with non-empty entries; return None otherwise.
- [x] 1.9 Implement atomic JSON write helper (`_persist`): write `<file>.tmp` then `os.replace`. Use `json.dump` with stable key order.
- [x] 1.10 Implement collision-safe fallback for `revert_group` when `original` exists (mirror the `_build_collision_path` pattern from `cloaked_file_detector` for naming).

## 2. Integrate RenameHistory into uncloak flow

- [x] 2.1 Add optional `history: RenameHistory | None = None` parameter to `CloakedFileDetector.uncloak_file` and call `history.record(original, new)` after the success path of the primary `os.rename`.
- [x] 2.2 Also call `history.record(original, duplicate_path)` in the duplicate-collision branch when that rename succeeds.
- [x] 2.3 Add the same optional parameter to `CloakedFileDetector.uncloak_files` and pass it through.
- [x] 2.4 Add the optional parameter to `file_utils.uncloak_file_extensions` and `file_utils.uncloak_file_extension_for_groups`; pass to detector.

## 3. Wire into main extraction flow

- [x] 3.1 At the top of `main.extract_files`, derive `input_root` from `paths[0]` (file → its dirname; dir → itself).
- [x] 3.2 Before Step 1, call `RenameHistory.load_pending(input_root)`. If returned, summarize entries and prompt `[y/N]`. On `y`, call `revert_group` for each bound key plus `revert_unbound`, then delete the file. On `n`, leave file (will be overwritten by new run).
- [x] 3.3 Detect input_root mismatch in the recovery prompt and surface a warning before asking for confirmation.
- [x] 3.4 Instantiate the per-run `history = RenameHistory(input_root)` before Step 4.
- [x] 3.5 Pass `history` through `file_utils.uncloak_file_extensions(...)` in Step 4.
- [x] 3.6 After Step 5 builds groups, iterate every group and call `history.bind(file_path, group.name)` for each `file_path in group.files`.
- [x] 3.7 In Step 7 single-archive loop:
    - Success branch (`_should_delete_original_archives(result)` is True): call `history.clear_group(group.name)` after originals are deleted.
    - Preserve branch (returns False): call `history.revert_group(group.name)` and print the revert summary.
    - Exception path / failure paths that hit the `finally` removing the group: call `history.revert_group(group.name)` there as well.
- [x] 3.8 Mirror the same wiring in Step 8 multipart loop (success / preserve / exception paths).
- [x] 3.9 Before printing the final completion banner, call `history.revert_unbound()` to handle entries whose renamed file disappeared from any group.
- [x] 3.10 Call `history.finalize()` immediately before `_ask_for_user_input_and_exit()` in the success path.

## 4. UI integration

- [x] 4.1 Use existing `print_warning` to emit `Reverted N renames for <group>:` followed by up to 5 indented `renamed → original` lines from the sample list.
- [x] 4.2 Use `print_info` to emit a single line on `clear_group` only if the group had >0 entries (e.g. `Cleared N rename history entries for <group>`); skip otherwise to avoid noise.
- [x] 4.3 Use `print_warning` for the recovery prompt header and `print_info` for the entry summary lines.

## 5. Tests

- [x] 5.1 Create `tests/test_rename_history.py` covering: `record` persists; `bind` updates entries; `revert_group` renames files back and skips missing; `clear_group` drops entries; `finalize` deletes when empty / preserves otherwise; `load_pending` round-trip.
- [x] 5.2 Test the collision-safe fallback in `revert_group` (set up an existing file at the original path before reverting).
- [x] 5.3 Test atomic write (simulate exception mid-write — `<file>.tmp` may exist but main file remains valid).
- [x] 5.4 Add an integration test in `tests/test_main.py` that mocks extraction failure and asserts files are renamed back to their cloaked names after `extract_files` returns.
- [x] 5.5 Add an integration test in `tests/test_main.py` that mocks extraction success and asserts the history file is deleted and no revert occurs.
- [x] 5.6 Add an integration test for the recovery flow: pre-create a leftover history file in tmp_path, mock the `[y/N]` input as `y`, run `extract_files`, assert files reverted and history file deleted.

## 6. Validation

- [x] 6.1 Run `poetry run pytest -q` — all tests pass.
- [ ] 6.2 Run the tool against a real cloaked input dir, observe rename happens, force a failure (e.g. wrong password / Ctrl+C), confirm files are reverted and the JSON file is properly cleaned up or preserved as designed.
- [ ] 6.3 Run `openspec verify --change add-rename-history --json` and resolve any issues.
