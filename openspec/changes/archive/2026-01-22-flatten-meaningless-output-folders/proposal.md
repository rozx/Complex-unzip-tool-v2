# Change Proposal: Flatten meaningless output folders

## Summary
When archives are extracted, some contents end up inside “meaningless” intermediate folders under the final output directory (e.g., folders named only with numbers or numbers plus symbols).

Examples the user expects to be flattened:
- `unzipped/1/aaa.jpg` -> `unzipped/aaa.jpg`
- `unzipped/1/5555+/222.jpg` -> `unzipped/222.jpg`

This change adds an output-path normalization step so that, when moving extracted files into the final output folder, leading directory segments that match a configured “meaningless folder” pattern are ignored (flattened).

## Motivation
- Some archives include noisy or auto-generated nesting (often numeric-only) that provides no useful structure to users.
- Preserving these folders makes browsing extracted results harder and increases path depth.

## Goals
- Flatten (remove) meaningless **leading** folder segments under the final output folder.
- Preserve existing collision-handling behavior (e.g., `aaa.jpg` collisions become `aaa_1.jpg`).
- Keep changes minimal and limited to final output layout logic.

## Non-Goals
- Changing archive extraction semantics (what files are extracted).
- Flattening “meaningless” folders in the *middle* of a path (e.g., `photos/1/aaa.jpg`) unless explicitly requested.
- Modifying grouping, cloaked filename detection, or multipart rules.

## Proposed Behavior (High-Level)
- When producing the final destination path for an extracted file (relative to the output folder), normalize the relative path by removing any **prefix** directories that are deemed “meaningless”.
- Continue stripping prefix segments until the first meaningful directory or the filename is reached.

### Definition: “Meaningless folder” (proposed)
A directory name is considered meaningless if it contains:
- At least one digit, AND
- No letters (A-Z/a-z) and no CJK characters, AND
- Only digits and a limited set of symbols (e.g., `+ - _ . , ( ) [ ] { } ! @ # $ % ^ & =`), after trimming whitespace.

This definition is intentionally conservative to avoid flattening real user folders.

## Affected Areas
- Final output move logic (where extracted files are moved from temp extraction directories to the output folder): likely `complex_unzip_tool_v2/modules/archive_utils.py` and/or `complex_unzip_tool_v2/modules/file_utils.py`.
- Tests: add unit coverage around output-path normalization.

## Risks & Mitigations
- Risk: Two different files may collapse into the same destination path.
  - Mitigation: Reuse existing collision handling (suffix `_1`, `_2`, ...).
- Risk: Over-flattening folders that are actually meaningful.
  - Mitigation: Restrict flattening to **leading** segments; use a conservative pattern; add tests with meaningful folder names to ensure they are preserved.

## Validation
- Add tests proving:
  - `unzipped/1/aaa.jpg` becomes `unzipped/aaa.jpg`.
  - `unzipped/1/5555+/222.jpg` becomes `unzipped/222.jpg`.
  - Meaningful folders remain intact (e.g., `unzipped/photos/1/aaa.jpg` stays under `photos/1/`).
  - Collision cases preserve both files with suffixing.
- Run: `poetry run pytest -q`.

## Open Questions
1. Exact symbol set: should folders like `2024-01-01` or `01_02_03` be considered meaningless?
2. Should flattening apply only when the meaningless folders are *directly under* the output root (prefix), or anywhere in the path?
3. Should the behavior be configurable (e.g., via config JSON), or hard-coded for now?
