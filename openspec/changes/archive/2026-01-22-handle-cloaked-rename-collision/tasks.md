## 1. Implementation
- [x] Add collision-aware handling in cloaked rename flow so a pre-existing normalized target does not raise a fatal error.
- [x] Ensure group normalization prefers the existing normalized path when a collision is detected.
- [x] Emit a warning (not an error) that a cloaked duplicate was detected.

## 2. Tests
- [x] Add a regression test for a directory containing both `9.7z(1).001/.002` and `9.7z.001/.002` to ensure no rename error is raised and the normalized set is selected.
- [x] Update any existing tests that assume rename always succeeds.

## 3. Validation
- [x] Run `poetry run pytest -q`.
