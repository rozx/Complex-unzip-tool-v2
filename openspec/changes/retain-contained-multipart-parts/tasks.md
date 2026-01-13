# Tasks

## 1. Repro & Regression Coverage
- [x] Add a regression test covering: outer archive contains `x.7z.001` + `x.7z.002` and the run does not delete `x.7z.002` due to temp cleanup.
- [x] Add/adjust a unit test for `extract_nested_archives()` to assert non-relocated continuation parts are preserved for the caller (either via `final_files` or a new explicit return key).

## 2. Implementation
- [x] Update `extract_nested_archives()` to record continuation parts as **candidate parts** when `group_relocator` does not relocate them.
- [x] Ensure multipart processing attempts extraction of the multipart primary first.
- [x] On multipart extraction failure, attempt matching candidate parts to the current archive’s missing multipart volumes and retry extraction.
- [x] If extraction succeeds (initially or after matching), clean the candidate parts that were only needed to satisfy missing volumes.
- [x] If extraction still fails, move candidate parts to the target output folder before removing temp directories.
- [x] Document the chosen signaling mechanism (recommend: new explicit return key rather than overloading `final_files`).

## 3. Optional Enhancement (If Needed)
- [x] If contained multipart sets commonly have no existing group, add a minimal helper to create a new multipart `ArchiveGroup` for the discovered set so Step 8 can extract it automatically.

## 4. Validation
- [x] Run `poetry run pytest -q`.
- [x] Smoke: `poetry run main --help`.
