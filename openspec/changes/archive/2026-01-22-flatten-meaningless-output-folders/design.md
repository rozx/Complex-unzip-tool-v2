# Design: Flatten meaningless output folders

## Problem Statement
Some archives extract into paths that include one or more meaningless intermediate folders under the tool’s final output folder. These folders are typically numeric-only or numeric plus symbols.

This produces output like:
- `unzipped/1/aaa.jpg`
- `unzipped/1/5555+/222.jpg`

Users expect these to be flattened to:
- `unzipped/aaa.jpg`
- `unzipped/222.jpg`

## Current Relevant Behavior
- The CLI creates a single output root folder (default `unzipped`).
- Extracted files are moved from temporary extraction locations into the output folder.
- Some move flows preserve directory structure (relative paths) and handle name collisions.

## Proposed Design
### Key Principle
Flattening should be safe and predictable: only remove meaningless **leading** path segments to avoid damaging intentional folder structure.

### Normalization Algorithm
Given a relative path like `1/5555+/222.jpg`:
1) Split into path parts.
2) While the first part is a “meaningless folder” (per rule), drop it.
3) Re-join remaining parts.
4) If all directories were dropped, the file lands directly under the output folder.

### Meaningless Folder Predicate
A folder name is considered meaningless when:
- It contains at least one digit.
- It contains no letters (A-Z/a-z) and no CJK characters.
- It is comprised of digits plus a small allow-list of punctuation/symbols.

This conservative approach avoids flattening names like `photos`, `音乐`, `abc123`, etc.

### Collision Handling
If normalization causes two files to map to the same destination path, reuse existing collision logic to suffix the filename (e.g., `_1`, `_2`).

### Placement in Pipeline
Integrate normalization where the tool computes the destination path under the output root (i.e., the “final move” stage). This ensures:
- All extraction flows benefit (single archives, nested outputs, multipart outputs).
- The behavior is centralized and testable.

## Test Strategy
- Unit tests for the predicate and normalization.
- Regression tests exercising move-to-output behavior (including collision).

## Non-Goals
- Flattening segments beyond the leading prefix.
- Making it configurable in this change (unless requested after approval).
