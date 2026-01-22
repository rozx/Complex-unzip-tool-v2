# Design: Retain contained multipart parts

## Problem Statement
`extract_nested_archives()` detects multipart continuation parts (e.g., `*.7z.002`, `*.r01`, `*.z02`, `*.part2.rar`) and skips them so they are not treated as nested archives.

In the CLI pipeline, nested extraction typically runs inside a temporary extraction directory (e.g., `temp.<group>`). After nested extraction returns, the caller moves only `final_files` into the output folder and then deletes the temp directory.

Because skipped continuation parts are not present in `final_files`, they remain in temp and are deleted on cleanup. This can break extraction of the contained multipart set and is surprising from a data-retention perspective.

## Current Relevant Behavior
- In `extract_nested_archives()`:
  - Continuation parts are detected and skipped.
  - If `group_relocator` is provided and returns `True`, the continuation is considered relocated.
  - Otherwise, it is skipped and not included in `final_files`.
- In the CLI (`main.py`):
  - `final_files` are moved from the temp extraction directory to the output directory.
  - The temp directory is removed.

## Proposed Design
### Key Principle
Skipping recursion into a continuation part must not imply deleting that file.

### Strategy (Ordered)

#### 1) Identify continuation parts and record them as candidates
When a continuation part is detected during nested scanning:
1) Attempt relocation via `group_relocator`.
2) If relocation succeeds: keep current behavior (skip recursion; do not return it as a final).
3) If relocation fails or is unavailable:
  - Record it as a **candidate part** that must not be lost during temp cleanup.

#### 2) Try extraction of the contained multipart primary first
If the contained multipart primary file exists (e.g., `x.7z.001`, `x.part1.rar`, `x.zip`), attempt extraction using the current multipart extraction flow.

#### 3) If extraction fails, attempt matching to current archive’s missing parts
If extracting the multipart primary fails, attempt to match the recorded candidate parts to the *current archive’s* missing multipart volumes (i.e., treat candidates as potential missing parts for an existing multipart group / current extraction context).

If matching provides the missing parts and extraction then succeeds, those candidate parts are considered tool-extracted temporary artifacts and may be cleaned.

#### 4) If extraction still fails, preserve by moving to target output folder
If extraction still fails after matching, move candidate parts to the target output folder so they survive temp cleanup and can be retried manually.

Implementation signaling can be done with either:
- **Option A (minimal API change)**: include non-relocated candidate parts in `final_files` so they are moved out of temp alongside other outputs.
- **Option B (explicit signaling)**: add a new result key like `candidate_multipart_parts` so the caller can decide whether to clean (if used successfully) or preserve (move to output).

Given the need to conditionally clean candidate parts when extraction succeeds, Option B is the clearer fit.

### Handling “New” Multipart Sets
If the multipart set inside the container does not correspond to any existing group, relocation and matching may fail. In that case, preserving the parts by moving them to the target output folder is sufficient for a manual retry.

## Trade-offs
- Option A is simplest but changes the meaning of `final_files` to include non-regular artifacts.
- Option B is more explicit, but adds a new output field and requires wiring in callers.

## Test Strategy
- Add an end-to-end-ish test (likely in `tests/test_main.py` or a new targeted test) that simulates:
  - outer extraction creates `x.7z.001` and `x.7z.002` in temp
  - extraction of `x.7z.001` fails due to missing parts
  - matching attempt does not resolve the missing parts
  - temp cleanup runs
  - `.002` is still present in output

- Update/extend existing unit tests in `tests/test_archive_utils.py` to assert:
  - relocation-true behavior stays the same
  - relocation-false behavior now preserves the continuation (either in `final_files` or in a dedicated preservation list)
