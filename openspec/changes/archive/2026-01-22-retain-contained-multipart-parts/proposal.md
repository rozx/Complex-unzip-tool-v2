# Change Proposal: Retain contained multipart parts

## Summary
When an archive contains a multipart archive set (e.g., `x.7z.001` + `x.7z.002`), the tool currently identifies continuation parts as “skip” during nested scanning. Because those skipped parts are not included in `final_files`, they remain in the extraction temp directory and are deleted when the temp directory is cleaned up. This can prevent the contained multipart set from being extracted later and can also cause unexpected loss of the contained parts.

This change ensures multipart continuation parts (and related primary parts when applicable) extracted from a container are preserved (moved into a persistent location under the output folder) unless they were successfully relocated to an appropriate multipart group directory.

## Motivation
- Contained multipart volumes are necessary for successfully extracting the contained multipart archive.
- Skipping recursion into continuation parts is correct, but deleting them as a side effect of temp cleanup is not.
- Users should not lose files that were extracted from a container just because they were not selected for recursive extraction.

## Goals
- Preserve multipart continuation parts extracted from container archives (7z, rar, zip spanned, tar.* multipart) so they are not deleted by temp cleanup.
- Maintain current behavior when a continuation part is successfully relocated via `group_relocator` (i.e., it should still be skipped from recursion).
- Keep changes minimal and safe; avoid broad behavioral shifts outside nested multipart handling.

## Non-Goals
- Changing archive format support.
- Changing cloaked filename detection rules.
- Reworking the overall extraction pipeline.

## Proposed Behavior (High-Level)
- During nested extraction, when a multipart continuation file is detected:
  - If `group_relocator` returns `True`, treat it as relocated and keep skipping it from recursion.
  - If `group_relocator` returns `False` (or is not provided), record the file as “candidate parts” (not `final_files`) so the caller can decide whether to keep or clean them.

- Contained multipart sets should be handled in this order:
  1) **Try extraction first**: If a contained multipart primary is present (e.g., `x.7z.001`, `x.part1.rar`, `x.zip`), attempt to extract it.
  2) **If extraction fails**: attempt to match the contained parts against the *current archive’s* missing multipart volumes (i.e., treat the contained parts as candidates to satisfy missing parts for an existing multipart group / current extraction context).
  3) **If extraction succeeds after matching**: treat the matched contained parts as temporary artifacts and clean them.
  4) **If extraction still fails**: move the contained parts to the target output folder so they are preserved for manual retry.

- Target folder decision (answer to the previous open questions): preserved contained parts should be moved into the main output folder (the tool’s target output folder).

## Affected Areas
- `complex_unzip_tool_v2/modules/archive_utils.py`: nested scanning behavior for multipart continuation parts.
- `complex_unzip_tool_v2/main.py`: temp folder cleanup vs. moving preserved files to output.
- `complex_unzip_tool_v2/modules/file_utils.py`: may need a helper to create/attach new multipart groups for “newly discovered” multipart sets.

## Risks & Mitigations
- Risk: More files may be emitted into output (e.g., `.7z.002` parts) in cases where previously they were deleted.
  - Mitigation: Preserve only multipart-looking continuation parts, and keep existing relocation-first behavior.
- Risk: Introducing new return fields or different semantics in `extract_nested_archives`.
  - Mitigation: Keep existing keys stable; add a new optional result key (e.g., `preserved_files`) if needed.

## Validation
- Add a regression test reproducing the bug:
  - Outer archive extraction produces `x.7z.001` and `x.7z.002` in the temp extraction folder.
  - Multipart extraction of `x.7z.001` fails initially due to missing parts.
  - The tool attempts matching using the contained parts; if matching cannot make extraction succeed, the run completes and the temp folder is cleaned.
  - Assert `x.7z.002` exists in the output folder after the run.
- Ensure existing tests related to continuation relocation remain correct or are updated to match the new preservation guarantee.

