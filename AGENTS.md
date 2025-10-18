# AI Agents Guide

This document defines how AI agents (and humans using them) should operate in this repository.

- Repo: `Complex-unzip-tool-v2`
- Primary language: Python (3.11)
- Package/Deps: Poetry (`pyproject.toml`, `poetry.lock`)
- Tests: `pytest` in `tests/`
- Bundling: scripts in `scripts/` and `7z/` binaries bundled for archive ops
- Default dev shell: Windows PowerShell

## Project Summary
A command-line tool to unzip/extract various archive formats, including nested and password-protected archives, with cloaked file detection.
- Handles multiple archive types (zip, rar, 7z, tar, etc.)
- Supports nested archives
- Handles password-protected archives using a password book
- Detects cloaked files based on configurable rules
- Always extract single archive first to see if it contains other contained archives
- Supports extraction to a specified output directory
- Provides clear CLI feedback and logging
- Have both Chinese and English language support

## Goals
- Keep the app stable and easy to maintain.
- Prefer minimal, well-scoped changes with tests.
- Follow a clear workflow so changes are reproducible locally on Windows.

## Ground Rules
- Do not exfiltrate secrets or make network calls unless explicitly required.
- Assume local execution on Windows with PowerShell; keep commands compatible.
- Respect the existing structure under `complex_unzip_tool_v2/` and `scripts/`.
- Use `pytest` for tests; add or update tests when changing behavior.
- Keep public APIs stable unless the change is intentional and documented.
- Use concise, focused commits/PRs with a clear description and checklist status.
- Always try to reuse existing utilities and patterns in the codebase.        

## Quickstart Commands

- Run in PowerShell:

```powershell
# From repo root
poetry run main
```

- Install dependencies (Poetry):

```powershell
# From repo root
poetry install
```

- Run tests:

```powershell
poetry run pytest -q
```

- Smoke test the CLI:

```powershell
poetry run main --help
```

- Build (packaging helper):

```powershell
# Option A: via Poetry
poetry run build
```

Note: The project bundles `7z/7z.exe`; code paths may assume this local binary.

## Repository Facts
- Entry points: `complex_unzip_tool_v2/__main__.py`, `complex_unzip_tool_v2/main.py`.
- Core modules:
  - `modules/archive_utils.py`, `modules/archive_extension_utils.py`
  - `modules/file_utils.py`, `modules/password_util.py`
  - `modules/cloaked_file_detector.py` (uses `config/cloaked_file_rules.json`)
- Domain classes under `classes/`: archive types, groups, password book.
- Icons for packaging: `icons/`.
- Tests in `tests/` cover archives, cloaked file detection, file utilities.

## Typical Agent Roles
- Feature/Code Agent: implement small features/bug fixes with tests.
- Test Agent: expand coverage, add regression tests, ensure edge cases.
- Docs Agent: update `README.md` and inline docs for changed behavior.
- Build/Release Agent: keep packaging scripts working; no secret leakage.

## Change Workflow
1) Branch and plan a minimal change set.
2) Add/adjust tests under `tests/` (write failing test first if practical).
3) Implement changes in `complex_unzip_tool_v2/` (keep diffs small and focused).
4) Run quality gates locally:
   - Build: ensure code runs (smoke test CLI)
   - Tests: `poetry run pytest -q`
   - Lint/Typecheck: if configured in `pyproject.toml`
5) Update docs (`README.md`) if user-facing behavior changes.
6) Commit with a clear message and open a PR with a short checklist.

## Quality Gates (Definition of Done)
- Build/Run: CLI `--help` works without errors.
- Tests: all tests pass locally; new behavior is covered by tests.
- No syntax/type errors; imports resolved.
- No unnecessary refactors or churn; only relevant lines changed.
- Docs updated when behavior or usage changes.

## Testing Guidelines
- Put tests in `tests/`, named `test_*.py`.
- Cover happy path and at least one edge case (e.g., missing password, invalid archive, cloaked file detection).
- Prefer small, deterministic examples; avoid large fixtures unless needed.

## Coding Conventions
- Keep functions small; prefer pure helpers in `modules/` when feasible.
- Error handling: raise domain exceptions under `classes/ArchiveExceptions.py` when appropriate.
- Paths: prefer using `pathlib` and utilities in `modules/file_utils.py`.
- Archive ops: centralize in `archive_utils.py` and `archive_extension_utils.py`.
- Config-driven behavior (e.g., cloaked rules) should read from `config/`.

## Passwords handling
- Password discovery sources (in this order):
  1) Target directory: `passwords.txt` located in the directory you pass to the CLI.
  2) Tool root directory: `passwords.txt` at the repository root (next to `AGENTS.md`).

- File format: one password per line; blank lines are ignored.

- Encoding support when reading `passwords.txt`:
  - Tries multiple encodings automatically: `utf-8-sig`, `utf-8`, `gbk`, `gb2312`, `big5`, `utf-16`, `utf-16-le`, `utf-16-be`.
  - Falls back to UTF-8 with errors ignored if necessary.
  - Byte Order Marks (BOM) are handled/stripped.

- Saving behavior:
  - When new passwords are learned during a run, they are saved to the local `passwords.txt` in UTF-8.
  - Save only occurs when there are actual changes.

## Renaming/Uncloaking rules
The tool normalizes “cloaked” filenames before grouping/extracting. This is Step 4 in the CLI (“Uncloaking file extensions”).

- Engine: `CloakedFileDetector` using rules from `complex_unzip_tool_v2/config/cloaked_file_rules.json`.
- Goal: Convert disguised names (with trailing junk/suffixes) into proper archive names, including multipart suffixes.

Safety guards (never rename these):
- Files that already have a proper multipart format are left as-is, e.g.:
  - `.7z.001`, `.7z.002`, ...
  - `.r00`, `.r01`, ... (RAR continuation)
  - `.z01`, `.z02`, ... (ZIP continuation)
  - `.tar.gz.001`, `.tar.bz2.001`, `.tar.xz.001`
  - `.part1.rar`, `.part2.rar`
- Files that already end with a proper single archive extension are left as-is, e.g.:
  - `.7z`, `.rar`, `.zip`, `.tar`, `.tgz`, `.tbz2`, `.txz`, `.gz`, `.bz2`, `.xz`, `.arj`, `.cab`, `.lzh`, `.lha`, `.ace`, `.iso`, `.img`, `.bin`.

Rule schema (JSON):
- `name`: identifier for the rule.
- `matching_type`: one of `both`, `filename`, `ext`.
  - `both`: `filename_pattern` matches the name, and `ext_pattern` matches the extension part (can be empty string to mean “no extension”).
  - `filename`: only `filename_pattern` is used; can capture archive type and part number.
  - `ext`: only `ext_pattern` is used (works on the last extension token).
- `filename_pattern` / `ext_pattern`: regexes; capture groups feed the new name.
- `priority`: larger values run first.
- `type`: archive type hint (`7z`, `rar`, `zip`, `auto`, etc.).
- `enabled`: toggle rule on/off.

Resolution flow:
1) Skip if filename is already proper (see “Safety guards”).
2) Iterate rules by `priority` (desc). If a rule matches, build the new filename:
   - Multipart part numbers are normalized to 3 digits (e.g., `1` -> `001`).
   - If `type` is `auto`, we try to detect via `archive_extension_utils.detect_archive_extension`.
3) Optional verification: the detector attempts to confirm the archive type via signature when possible; it’s lenient for cloaked files to avoid blocking normalization.
4) Apply rename only if the new filename differs and passes the basic checks.

Examples (intended outcomes):
- `11111.7z删除` -> `11111.7z`
- `11111.7z.00删1` -> `11111.7z.001`
- `archive.zip.z0隐藏1` -> `archive.zip.z01`
- `file.rar.r00删除` -> `file.rar.r00`

Where to change rules:
- Edit `complex_unzip_tool_v2/config/cloaked_file_rules.json`.
- Use `priority` to order more specific rules above generic ones.
- Set `enabled: false` to disable a rule without removing it.

Testing:
- See `tests/test_cloaked_file_detector.py` for unit tests covering rule matching and safety guards.
- Run tests with `poetry run pytest -q`.

## Nested multipart handling (inside containers)
When extracting an archive that itself contains multipart archives (e.g., a .7z containing another multi-part set), the tool excludes continuation parts from the final outputs so they are not moved to the destination. Only the primary part is considered for further extraction.

- Primary vs continuation identification:
  - 7z volumes: primary is `.7z.001`; continuations are `.7z.002+`.
  - TAR multipart: primary is `.tar.gz/.tar.bz2/.tar.xz.001`; continuations are `.002+`.
  - RAR volumes: primary is `.rar` or `.part1.rar`; continuations are `.r00`, `.r01`, … and `.part2+.rar`.
  - ZIP spanned: primary is `.zip`; continuations are `.z01`, `.z02`, …

- Behavior:
  - Continuation parts detected during nested extraction are skipped (not treated as nested archives and not added to `final_files`).
  - Only the primary part is extracted recursively.
  - After processing, the temporary extraction folder is removed, so any skipped continuation files inside that temp directory are cleaned up instead of being moved to the output folder.

- Implementation:
  - `complex_unzip_tool_v2/modules/archive_utils.py` → `extract_nested_archives()` filtering logic while iterating over extracted files.
  - This logic runs only for nested contents. Top-level grouping/multipart processing remains unchanged.

- Validation:
  - CLI smoke: `poetry run main --help`.
  - End-to-end: run against a directory where an outer archive contains a multipart set; only files from extracting the primary part should end up in the output directory, with continuation parts neither moved nor left behind.

## Non-archive handling during nested scan
The tool treats every file as a potential archive by default. During nested extraction, we probe files with 7‑Zip but avoid flagging regular files (e.g., .mp4) as corrupted by mapping 7‑Zip output appropriately and parsing list output robustly.

- Behavior:
  - All files are candidates for probing via 7‑Zip.
  - If 7‑Zip prints messages like “Can not open file as archive”, “cannot open file as archive”, or “is not archive”, we treat this as unsupported/non‑archive (not corruption) and skip it.
  - Regular files encountered during nested scanning therefore do not produce spurious corruption errors.

- Implementation:
  - `complex_unzip_tool_v2/modules/archive_utils.py` → `_raise_for_7z_error()` maps the above messages to `ArchiveUnsupportedError` (non‑archive/unsupported), not `ArchiveCorruptedError`.
  - `_parse7zListOutput()` begins parsing after the dashed separator to remain compatible with varying 7‑Zip outputs.
  - `is_valid_archive()` uses 7‑Zip listing plus the mapping above to determine if a file is an archive.

- Validation:
  - Unit tests: `poetry run pytest -q` should pass.
  - Smoke: running against directories containing non‑archive files (e.g., .mp4) should not produce “corrupted archive” messages for those files.

## Common Local Paths
- 7-Zip: `./7z/7z.exe`
- Config: `complex_unzip_tool_v2/config/cloaked_file_rules.json`
- CLI Entrypoint: `complex_unzip_tool_v2/__main__.py`

## PR Template (suggested)
- Summary: what changed and why
- Tests: added/updated tests and results (`pytest -q` passes)
- Impact: user-facing behavior changes? update `README.md`
- Risks: edge cases considered; rollback plan if needed

## Troubleshooting
- Poetry not found: install Poetry or run via system Python if necessary.
- Windows path issues: use raw strings or `pathlib` to avoid backslash escapes.
- 7z missing: ensure `./7z/7z.exe` exists; code should refer to the bundled binary.

## Scope for Agents
- Keep PRs atomic and under ~300 lines of changes when possible.
- Avoid introducing new dependencies unless clearly justified and added to `pyproject.toml`.
- Do not modify bundled binaries under `7z/`.

---

If anything here conflicts with `README.md`, prefer the README and update this file accordingly in the same change.
