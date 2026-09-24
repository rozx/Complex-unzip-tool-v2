# Validation — 2026-09-24

## Automated checks

- macOS ARM64 / Python 3.11.14: **234 passed** (`poetry run pytest -q`).
- Linux ARM64 / Python 3.12.12 container: **234 passed**.
- Linux x64 / Python 3.11 container under Docker emulation: **234 passed**.
- New regressions were observed failing before implementation: native engine dispatch/permissions (7 failures), CLI preflight/exit behavior (4 failures), and platform packaging/asset validation (7 failures).
- Two existing tests used Windows-only path fixtures and failed on the initial macOS baseline (205 passed, 2 failed). They now use native paths while preserving their grouping/basename assertions.
- New runtime helper, builder, and new test files pass Black and flake8. The runtime helper and builder pass mypy with existing dependency errors excluded (`--follow-imports=silent`).
- Whole-project flake8 retains the same 193 baseline findings; whole-project mypy has 137 errors versus 138 before this change. Comparison ignoring shifted line numbers found no new diagnostics. Existing unrelated formatting/type/lint debt was not reformatted or repaired.
- CLI `--help`, Python compilation, `git diff --check`, and strict OpenSpec change validation pass.

## Native engine and standalone checks

Real 7-Zip smoke checks passed on macOS ARM64, Linux ARM64, and Linux x64 (Docker emulation):

- Listing and extracting ZIPs with Chinese filenames and spaces in paths.
- Encrypted 7z archives with a Unicode password and encrypted headers; wrong passwords produce the password domain error.
- Split 7z `.001`/`.002+` extraction with byte-for-byte output verification.
- Recursive 7z → ZIP extraction and regular-file rejection.
- Source CLI help, version, and extraction into `unzipped/` using disposable synthetic inputs.

`poetry run build` produced the macOS ARM64 standalone executable in `dist/complex-unzip-tool-v2` (about 12.6 MiB). Its help, version, and real extraction were verified from another working directory with stdin redirected, proving bundled-root lookup and normal POSIX exit behavior. Running the PyInstaller bootloader required execution outside the Codex filesystem sandbox because the sandbox blocks its sync semaphore.

Official release packages were checked against GitHub release-asset SHA-256 metadata before extraction. Every bundled engine and license matches `7z/manifest.json`. Unix engines retain mode `0755`; `file` confirms the macOS universal Intel/ARM64 binary and Linux static binaries.

## Limits and reproduction

- Windows native execution/build and Intel macOS execution were not available on this host. Windows/Intel platform selection and packaging have deterministic regression coverage; the Windows EXE/DLL are unchanged files from the official x64 installer.
- Linux engine, source CLI, and full suites were exercised in both architectures; Linux standalone builds were not executed. Packaging input selection is covered for both architectures.
- Linux suites used a read-only checkout mount and existing pure Python test/runtime dependencies. The containers had networking disabled during tests and archive smoke checks.
- The host's pre-existing global Poetry launcher points to a missing interpreter. A project-local ignored `.venv` was created, Poetry installed there, and locked project dependencies installed with `.venv/bin/poetry install`. Local commands can use `.venv/bin/poetry run ...`.
- No repository dependency versions were changed, release uploaded, remote push made, or Windows installation performed.
