# Design: Auto-group contained ZIP/RAR volume sets

## Context
`ensure_contained_multipart_groups()` exists specifically to address a pipeline timing issue:
- Step 5 builds `ArchiveGroup`s from the user’s initial input listing.
- Step 7 extracts single archives and may discover new multipart sets *inside* those containers.
- Those newly discovered sets must be added to `groups` so Step 8 (multipart extraction) can process them in the same run.

The current helper only auto-groups “unambiguous primaries” (e.g., `.7z.001`). `.zip` and `.rar` were intentionally excluded because they can represent either a single archive or a multipart set.

## Design Goals
- Extend auto-grouping for `.zip`/`.rar` without regressing into false positives.
- Ensure the extracted multipart pipeline uses the correct main archive file.

## Key Constraint: Main archive selection
`ArchiveGroup.add_file()` currently prioritizes `first_part_regex` to set `mainArchiveFile`. `first_part_regex` includes `.z01` and `.r00`, which means:
- If both `X.zip` and `X.z01` are in a group, adding `X.z01` can override the main archive to `X.z01`.
- If both `X.rar` and `X.r00` are in a group, adding `X.r00` can override the main archive to `X.r00`.

For spanned ZIP and RAR volumes, we want the main archive to remain `X.zip` / `X.rar`.

### Minimal approach (preferred)
Keep changes scoped to contained auto-group creation only:
- When auto-creating a spanned ZIP/RAR group, explicitly force `mainArchiveFile` to `X.zip` / `X.rar` after adding all files.
- This avoids changing general grouping or first-part heuristics for other flows.

### Alternative (broader scope)
Adjust `ArchiveGroup` selection rules so that if a group contains `X.zip` and any `X.zNN`, `.zip` is considered the main, and similarly for `.rar` + `.rNN`.
- This could improve behavior for all grouping flows, but is higher risk due to wider impact.

This change proposal prefers the minimal approach unless tests show the broader fix is necessary.

## Grouping Guardrails
We only auto-create groups when we can prove a multipart set exists:
- ZIP spanned: require `.zip` plus at least one `.zNN` in the same directory bucket.
- RAR volumes: require `.rar` plus at least one `.rNN` in the same directory bucket.

This avoids creating multipart groups for single archives like `movie.zip` or `backup.rar`.

## Compatibility Notes
- This design does not require expanding `MULTI_PART_PATTERNS` or changing `get_archive_base_name()`.
- It relies on filename patterns already used elsewhere (`multipart_regex`) and local directory bucketing in `ensure_contained_multipart_groups()`.

## Testing Strategy
- Unit tests should focus on `ensure_contained_multipart_groups()`:
  - `.zip` + `.z01` creates a group and preserves `.zip` as `mainArchiveFile`.
  - `.rar` + `.r00` creates a group and preserves `.rar` as `mainArchiveFile`.
  - `.zip` alone / `.rar` alone does not create new groups.

- If needed, add an integration test that verifies Step 7 → Step 8 handoff for a contained spanned set.
