# Change Proposal: Prevent multipart deletion on failure

## Summary
When multipart extraction fails (e.g., missing volumes or bad passwords), the tool sometimes deletes or moves away source parts. This proposal adds strict retention and cleanup guardrails so that source multipart volumes (.7z.00x, .r00, .z01, .partN.rar) are never deleted or moved to the recycle bin due to extraction failure. Only temporary, tool‑created artifacts are cleaned up.

## Motivation
- Users risk losing multipart volumes if extraction errors trigger cleanup code that is too broad.
- Retaining source volumes enables recovery (e.g., adding missing parts later) and re‑trying extraction.
- Aligns with AGENTS.md goals: preserve behavior unless intentionally modified, and keep the app stable and safe.

## Goals
- Ensure no source multipart parts are deleted when extraction fails.
- Scope cleanup to temporary, tool‑created directories/files only.
- Preserve relocated continuation parts discovered during nested extraction.
- Provide clear logging about what is cleaned and what is retained.

## Non‑Goals
- No change to successful extraction behavior or relocation logic semantics.
- No change to detection rules or archive support matrix.

## Approach
- Introduce a "cleanup guard" policy: deletion operations operate only on known temporary paths (staging/work dirs) that the tool created during the current run.
- Tighten multipart failure path handling: on any error, skip deletion of group directories and source volumes.
- Ensure reconciliation and relocation do not mark relocated files for cleanup if extraction ultimately fails.
- Add tests covering failure scenarios across common multipart types (7z, RAR, ZIP spanned).

## Risks & Mitigations
- Risk: leftover temporary files increase disk use.
  - Mitigation: clean only tool‑created staging dirs; log retained items.
- Risk: behavior differences in nested extraction.
  - Mitigation: explicit scenarios and tests for nested continuation relocation.

## Validation
- Unit tests under `tests/` for failure scenarios verify no deletion of source parts.
- CLI smoke runs confirm informative logging and cleanup limited to temporary dirs.

## Open Questions
- Should we add a user‑visible flag to force aggressive cleanup? For now, no; keep minimal changes.
