## 1. Classification

- [x] 1.1 Failing tests: `is_valid_archive` rejects zip-typed documents/packages (case-insensitive), accepts zip disguised as media, non-zip containers named `.docx`, `.cbz`, and password-error listings
- [x] 1.2 Add the zip-based document extension set and apply it in `is_valid_archive` after the container allowlist

## 2. Pipeline behavior

- [x] 2.1 Failing test: nested `report.docx` is kept in `final_files` while a sibling `inner.zip` is extracted
- [x] 2.2 Failing test: top-level `report.docx` is not extracted or deleted and is reported as a kept document
- [x] 2.3 Bilingual messages for kept documents/packages at nested and top level

## 3. Verification

- [x] 3.1 `pytest -q`, `flake8`, `mypy`, `black`, `main --help`
- [x] 3.2 Real 7-Zip check on a `.docx`/`.jar` nested in a `.7z`
