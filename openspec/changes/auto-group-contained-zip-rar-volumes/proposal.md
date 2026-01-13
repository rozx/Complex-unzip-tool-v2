# Change Proposal: Auto-group contained ZIP/RAR volume sets

## Summary
The tool already has `ensure_contained_multipart_groups()` to create multipart `ArchiveGroup`s for multipart sets that are discovered only after extracting container archives (Step 7). Today this helper intentionally only auto-creates groups for unambiguous multipart primaries (`.7z.001`, `.tar.(gz|bz2|xz).001`, `.part1.rar`).

This change extends that auto-grouping to include:
- ZIP spanned sets: `.zip` + `.z01`, `.z02`, ...
- RAR volume sets: `.rar` + `.r00`, `.r01`, ...

The extension is conservative: it will only auto-create a group for `.zip` / `.rar` when at least one continuation part exists in the same directory bucket. This avoids misclassifying normal single-file `.zip`/`.rar` archives.

## Motivation
Users can extract an outer container archive that contains a multipart ZIP/RAR set. When that contained set is preserved to the output folder (e.g., due to extraction failure or because it should be processed later), Step 8 (multipart processing) can only extract it if an appropriate group exists. Without auto-grouping, these contained spanned ZIP/RAR sets may remain unprocessed unless the user re-runs the tool or manually extracts them.

## Goals
- Extend `ensure_contained_multipart_groups()` so contained ZIP spanned and RAR volume sets can be auto-grouped and processed by Step 8 in the same run.
- Keep grouping conservative to avoid creating multipart groups for normal `.zip`/`.rar` single archives.
- Ensure the chosen `mainArchiveFile` for spanned ZIP/RAR groups is `.zip` / `.rar` (not `.z01` / `.r00`).

## Non-Goals
- Changing the general grouping behavior in `create_groups_by_name()` for user-provided input folders.
- Expanding multipart base-name parsing (`get_archive_base_name`) or `MULTI_PART_PATTERNS` in this change.
- Changing cloaked filename rules.

## Proposed Behavior (High-Level)
When `ensure_contained_multipart_groups(file_paths, groups)` is called after Step 7 moves preserved files into the output folder:

- ZIP spanned auto-grouping:
  - If a bucket contains `X.zip` and any `X.zNN` (e.g., `X.z01`), create a multipart group for `X`.
  - Set the group’s `mainArchiveFile` to `X.zip`.

- RAR volume auto-grouping:
  - If a bucket contains `X.rar` and any `X.rNN` (e.g., `X.r00`), create a multipart group for `X`.
  - Set the group’s `mainArchiveFile` to `X.rar`.

- Do not auto-create `.zip`/`.rar` groups when no continuation parts exist.

## Risks & Mitigations
- Risk: `.zip`/`.rar` are ambiguous and could be single archives.
  - Mitigation: only group if a continuation exists in the same bucket.
- Risk: `ArchiveGroup.add_file()` currently prioritizes `first_part_regex` (`.z01`/`.r00`) when selecting `mainArchiveFile`.
  - Mitigation: for auto-created spanned ZIP/RAR groups, explicitly set the main archive back to `.zip`/`.rar` after adding files (or adjust selection logic in a tightly scoped way). The spec below constrains the desired behavior; implementation should follow the minimal safe approach.

## Affected Areas
- `complex_unzip_tool_v2/modules/file_utils.py`: extend `ensure_contained_multipart_groups()` detection logic.
- Potentially `complex_unzip_tool_v2/classes/ArchiveGroup.py`: only if needed to guarantee `.zip`/`.rar` remain the main file for spanned sets.

## Validation
- Add/extend unit tests for `ensure_contained_multipart_groups()`:
  - Creates a group for `X.zip` + `X.z01` (and sets main to `X.zip`).
  - Creates a group for `X.rar` + `X.r00` (and sets main to `X.rar`).
  - Does not create a group for `X.zip` alone or `X.rar` alone.

- Optional integration: a `main`-level test ensuring Step 7 can cause Step 8 to pick up a contained ZIP/RAR set when parts are present.
