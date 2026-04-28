## ADDED Requirements

### Requirement: Track every successful uncloak rename
The system SHALL record every in-place rename performed by the cloaked-file detector during a run, capturing the original path, the renamed path, and a stable identifier for the run.

#### Scenario: Single cloaked file renamed
- **WHEN** the detector renames `1525.zip.001.bin` to `1525.7z.001` during Step 4
- **THEN** the rename history SHALL contain an entry with `original=1525.zip.001.bin` and `renamed=1525.7z.001`

#### Scenario: Duplicate-collision rename
- **WHEN** the detector encounters a collision target and renames the cloaked file to a `__duplicate_<token>` variant via `_build_collision_path`
- **THEN** the rename history SHALL contain an entry mapping the original cloaked name to the duplicate variant

#### Scenario: Failed rename is not recorded
- **WHEN** `os.rename` raises an exception during uncloaking
- **THEN** the rename history SHALL NOT contain an entry for that file

### Requirement: Bind tracked renames to archive groups
The system SHALL associate every tracked rename with the `ArchiveGroup` whose file list contains its `renamed` path after Step 5 grouping completes.

#### Scenario: Bind after grouping
- **WHEN** Step 5 produces an `ArchiveGroup` with name `dir-1525` containing files including `1525.7z.001`
- **AND** the rename history contains an entry with `renamed=1525.7z.001`
- **THEN** that entry SHALL be bound to group key `dir-1525`

#### Scenario: Renamed file not present in any group
- **WHEN** binding completes and a tracked entry's `renamed` path appears in no group's file list
- **THEN** the entry SHALL remain unbound and SHALL be reverted at end-of-run

### Requirement: Revert renames when group originals are preserved
The system SHALL revert all rename history entries bound to a group whenever that group's outcome would have caused the original archive files to be preserved (i.e. the same condition under which `_should_delete_original_archives` returns False, or any failure path that bypasses the deletion step entirely).

#### Scenario: Group fails with password skip
- **WHEN** Step 7 or Step 8 finishes a group with `password_failed_archives` non-empty (originals preserved)
- **THEN** the system SHALL rename every bound file from `renamed` back to `original`
- **AND** SHALL emit a warning indicating how many renames were reverted for that group

#### Scenario: Group raises an exception
- **WHEN** Step 7 or Step 8 catches an exception for a group and falls into the `finally` cleanup that retains the source parts
- **THEN** the system SHALL revert all renames bound to that group

#### Scenario: Revert encounters missing renamed file
- **WHEN** revert is asked to rename `renamed → original` but `renamed` no longer exists on disk
- **THEN** the system SHALL skip that entry, log an info message, and continue with remaining entries

#### Scenario: Revert encounters existing original
- **WHEN** revert is asked to rename `renamed → original` but `original` already exists on disk
- **THEN** the system SHALL pick a unique fallback path using the same collision-suffix scheme as the cloaked detector and complete the rename without raising

### Requirement: Drop history entries for successful groups
The system SHALL remove all rename history entries bound to a group whenever that group's outcome causes the original archive files to be deleted (`_should_delete_original_archives` returns True).

#### Scenario: Group succeeds and originals are deleted
- **WHEN** Step 7 or Step 8 finishes a group successfully and removes the original archive(s)
- **THEN** the system SHALL clear the history entries bound to that group
- **AND** SHALL NOT attempt to revert any of those renames

### Requirement: Persist history across crashes
The system SHALL persist the rename history to a JSON file in the input root directory, updated eagerly after every record / revert / clear operation, and removed on clean program completion when the history contains no remaining entries.

#### Scenario: History written on each record
- **WHEN** a new rename is recorded
- **THEN** the file `<input_root>/.unzip-rename-history.tmp.json` SHALL exist on disk and SHALL contain the entry
- **AND** the write SHALL be atomic (write to temp + `os.replace`)

#### Scenario: File removed on clean exit
- **WHEN** the run completes with all groups processed and no entries remaining
- **THEN** `.unzip-rename-history.tmp.json` SHALL be deleted

#### Scenario: File survives crash
- **WHEN** the program is terminated abnormally (SIGINT, exception in unrelated code, OS kill) after at least one rename was recorded
- **THEN** the JSON file SHALL remain on disk reflecting all renames that had been recorded up to the moment of termination

### Requirement: Recover from leftover history on startup
The system SHALL detect a pre-existing `.unzip-rename-history.tmp.json` in the input root before Step 4 runs, summarize its contents to the user, and prompt for revert with a default of "no".

#### Scenario: Leftover detected, user accepts
- **WHEN** a leftover history file with non-empty entries is detected at startup
- **AND** the user enters `y` at the recovery prompt
- **THEN** the system SHALL revert each entry whose `renamed` path still exists, applying the same missing-file and clobber-safety rules as in-run revert
- **AND** SHALL delete the history file before continuing
- **AND** SHALL then proceed with the normal Step 1+ flow

#### Scenario: Leftover detected, user declines
- **WHEN** a leftover history file is detected and the user enters `n` (or accepts the default)
- **THEN** the system SHALL leave the file in place
- **AND** SHALL proceed with the normal flow, where any new records during the run will overwrite the file

#### Scenario: Leftover with mismatched input root
- **WHEN** a leftover history file is detected but its `input_root` field does not match the current input root
- **THEN** the system SHALL warn the user about the mismatch in the recovery prompt before asking for confirmation
