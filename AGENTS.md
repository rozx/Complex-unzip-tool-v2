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
