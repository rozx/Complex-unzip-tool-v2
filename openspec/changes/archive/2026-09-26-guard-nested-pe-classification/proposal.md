## Why

Issue #21: every plain `.exe`/`.dll` found inside an extracted archive is classified as a nested archive, because `is_valid_archive()` treats "7-Zip can list it" as "it is an archive". 7-Zip's `PE` handler lists the sections of any executable (`.text`, `.rsrc`, …), so the tool "extracts" each executable into a `NAME.dll_2/` folder of section blobs and deletes the original — permanently, because `main.py` forces `use_recycle_bin=False` for nested cleanup. One report lost 155 executables from a game directory while the run reported SUCCESS.

## What Changes

- Classify a file as an archive using 7-Zip's **archive-level** `Type =` field (the header block of `7z l -slt`, before the first `----------` line). Only an allowlist of real container formats (7z, Rar, Rar5, zip, gzip, bzip2, xz, zstd, lzma, lzma86, Z, tar, Cab, Arj, Lzh, Cpio, wim, Iso, Udf, Split) counts as an archive. Executables and other non-container formats 7-Zip can open (PE, ELF, MachO, Compound, FLV, Hash, …) are kept as regular files.
  - The innermost header `Type` wins (a `.7z.001` reports `Split` then `7z`), so what 7-Zip would actually extract is what gets judged.
  - A self-extracting archive (`Type = 7z` + `Offset = N`) is still extracted; a plain PE (`Type = PE`) or a PE with unknown overlay (`Cannot open the file as archive`) is kept.
  - Password-protected archives whose listing fails with a password error remain archives (unchanged).
  - Listings with no header `Type` (legacy/mocked output) keep the previous "non-empty listing" behavior.
- Nested-archive cleanup honors the user's deletion mode: Recycle Bin by default, permanent only with `--permanent-delete`, so any future misjudgment is recoverable.

## Impact

- Code: `modules/archive_utils.py` (`readArchiveContentWith7z` / `_parse7zListOutput` header parsing, `is_valid_archive`), `main.py` (four `extract_nested_archives` calls).
- Behavior: nested executables/documents that 7-Zip merely *can open* are no longer exploded; nested cleanup becomes recoverable. Zip-based documents (`.docx`, `.jar`, …) report `Type = zip` and are out of scope (tracked separately).
- Top-level inputs share `is_valid_archive`, so a plain `.exe` passed directly is reported as "not a valid archive" instead of being exploded; SFX detection in `archive_extension_utils.py` is unchanged.
