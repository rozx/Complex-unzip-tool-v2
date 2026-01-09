# Tasks

- [x] Add regression tests: multipart extraction failure retains all source parts
- [x] Introduce cleanup guard policy limiting deletions to tool‑created temp dirs
- [x] Apply guardrails in failure paths for single and multipart phases
- [x] Ensure nested relocation never marks relocated parts for cleanup on failure
- [x] Add logging lines clarifying retained vs cleaned items
- [x] Run `pytest` (unit + integration) and verify no source deletions occur
- [x] Update README (Troubleshooting) if behavior becomes user‑visible
- [x] Prepare release notes entry summarizing retention change
