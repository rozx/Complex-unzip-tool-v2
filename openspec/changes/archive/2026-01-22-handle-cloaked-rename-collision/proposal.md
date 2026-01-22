# Change: Handle cloaked rename collisions

## Why
When cloaked multipart files (e.g., `9.7z(1).001`) are normalized, a rename collision occurs if the normalized target (e.g., `9.7z.001`) already exists in the same folder. This raises a Windows error and contributes to extraction failure. The tool should treat this as a non-fatal condition and proceed with the valid normalized set.

## What Changes
- Detect rename collisions during cloaked-file normalization and avoid failing the run.
- When a normalized target exists, prefer the existing normalized file for grouping and extraction.
- Surface a warning (not an error) for collisions so the user knows duplicates were found.

## Impact
- Affected specs: `cloaked-rename-collision` (new capability delta)
- Affected code: `complex_unzip_tool_v2/modules/cloaked_file_detector.py`, `complex_unzip_tool_v2/modules/file_utils.py`, and related tests

## Open Questions
- Should the duplicate cloaked file (e.g., `9.7z(1).001`) be preserved as-is, or moved aside (e.g., suffix/duplicate folder) after a collision is detected?
