## 1. Archive-level type classification

- [x] 1.1 Failing tests: header `Type` parsing (PE, 7z+Offset, Split→7z, entry-level Type ignored, no header)
- [x] 1.2 Failing tests: `is_valid_archive` rejects PE/ELF/Compound, accepts SFX 7z, keeps password-error = archive
- [x] 1.3 Parse the header block of `7z l -slt` and expose the innermost archive type
- [x] 1.4 Apply the container allowlist in `is_valid_archive`

## 2. Recoverable nested cleanup

- [x] 2.1 Failing test: `extract_files` passes the user's `use_recycle_bin` to `extract_nested_archives`
- [x] 2.2 Replace the four hard-coded `use_recycle_bin=False` calls in `main.py`

## 3. Verification

- [x] 3.1 `pytest -q`, `flake8`, `mypy`, `black`, `main --help`
- [x] 3.2 Real 7-Zip check on plain PE, SFX, overlay PE and split volume
- [x] 3.3 Release notes entry
