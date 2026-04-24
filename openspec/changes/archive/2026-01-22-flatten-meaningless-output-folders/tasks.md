# Tasks

## 1. Specs & Test Coverage
- [x] Add unit tests for output-path normalization (numeric-only and numeric+symbol chains).
- [x] Add a regression test ensuring meaningful folders are not flattened.
- [x] Add a collision test where two different sources collapse to the same destination.

## 2. Implementation
- [x] Add a helper to normalize output relative paths by stripping meaningless *leading* directory segments.
- [x] Wire normalization into the final move/copy stage that places extracted files into the output folder.
- [x] Ensure name-collision handling remains consistent with current behavior.
- [x] Optionally remove now-empty meaningless directories left behind (best-effort).

## 3. Validation
- [x] Run `poetry run pytest -q`.
- [x] Smoke: `poetry run main --help`.
