# Tasks: Auto-group contained ZIP/RAR volume sets

- [x] Inspect existing multipart grouping behavior
   - Confirm how `create_groups_by_name()` groups `.zip` + `.z01` and `.rar` + `.r00` today.
   - Confirm how `ArchiveGroup.mainArchiveFile` is selected when both primary and continuation exist.

- [x] Extend `ensure_contained_multipart_groups()` (contained-only)
   - Add detection for ZIP spanned buckets: `X.zip` + any `X.zNN`.
   - Add detection for RAR volume buckets: `X.rar` + any `X.rNN`.
   - Ensure the created group’s `mainArchiveFile` is `.zip` / `.rar` for these sets.

- [x] Add unit tests
   - ZIP spanned: group created; `mainArchiveFile == X.zip`.
   - RAR volumes: group created; `mainArchiveFile == X.rar`.
   - Negative cases: `.zip` alone / `.rar` alone => no group created.

- [x] (Optional) Integration test
   - Simulate Step 7 moving contained spanned sets into output and verify Step 8 sees the new group.

- [x] Validation
   - Run `pytest -q`.
   - Run `openspec validate auto-group-contained-zip-rar-volumes --strict`.
