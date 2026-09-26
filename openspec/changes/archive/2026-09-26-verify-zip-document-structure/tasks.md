## 1. Structure check

- [x] 1.1 Failing tests: plain zip named `.docx`/`.xlsx`/`.epub`/`.jar`/`.apk`/`.ipa`/`.pages`/`.key` is extracted, including a nested `资源.zip.docx`
- [x] 1.2 Guard tests: real documents with backslash paths and `*.dist-info`/`*.kml`/`index.xml` markers stay files
- [x] 1.3 Map each document extension to its required root entries and check them in `is_valid_archive`

## 2. Verification

- [x] 2.1 `pytest -q`, `flake8`, `mypy`, `black`
- [x] 2.2 Real 7-Zip check: a real `.docx`/`.jar` is kept, and `资源.zip.docx`/`game.apk` (plain zips) are extracted
- [x] 2.3 Release notes wording
