# Design

## Current Behavior (Summary)
- Multipart handling identifies primary vs continuation parts and may relocate continuations during nested extraction.
- A reconciliation pass moves parts from output into group directories.
- Cleanup routines may operate on broader directories/files than intended when errors occur.

## Proposed Behavior
- Cleanup Guardrails:
  - Maintain a set of tool‑created temporary paths (staging/work dirs) for this run.
  - Deletion operations act only on those paths.
  - Source directories and files (including multipart volumes and group directories) are excluded.
- Failure Handling for Multipart:
  - On failure of any volume or missing parts, do not delete or recycle any source parts.
  - If a partially extracted output directory exists, allow cleaning contents inside tool‑created staging only; preserve source volumes and any relocated continuations.
- Logging:
  - Emit explicit messages: "Cleaned temp dir" vs "Retained source parts".

## Affected Areas
- `modules/archive_utils.py`: failure paths, nested extraction cleanup
- `modules/file_utils.py`: relocation and cleanup helpers
- `main.py`: wiring cleanup guard context (if needed)

## Alternatives Considered
- Add a user flag for aggressive cleanup (not chosen; increases risk)
- Track per‑file provenance metadata (overkill for now)

## Test Strategy
- Unit tests for 7z (.7z.001 missing .002), RAR (.part1.rar missing part2), ZIP (.zip with missing .z01)
- Nested extraction case where continuations are relocated and extraction later fails
- Assert: no source part deletion, temp dirs cleaned only, logs emitted
