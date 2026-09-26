## Why

After issue #21, archive classification trusts 7-Zip's archive-level `Type`. Zip-based document and package formats (`.docx`, `.xlsx`, `.odt`, `.epub`, `.jar`, `.apk`, `.ipa`, `.msix`, `.vsix`, …) are reported as `Type = zip`, so when one appears inside an archive it is unpacked into its internal XML/class files and the original file is removed.

## What Changes

- A file whose archive-level type is `zip` **and** whose extension is a known zip-based document/package extension is classified as a regular file: it is kept unchanged, moved to the output like any other file, and never extracted or deleted.
  - The type gate comes first: a `.docx` whose type is `7z`/`Rar` is still a (disguised) container and is extracted.
  - The extension gate comes second: a zip disguised as `.jpg`/`.mp4`/`.txt` or with a cloaked name is still extracted.
  - Extension matching is case-insensitive and uses only the final extension.
  - Comic book archives (`.cbz`) are not on the list; their images are what users want, so they are still extracted.
  - Password errors while listing keep the file an archive (unchanged).
- Top-level inputs share `is_valid_archive`, so a zip-based document found by a folder scan is left in place like any other non-archive file instead of being exploded and recycled.
- A bilingual message names kept documents/packages at both nested and top level.

## Impact

- Code: `modules/archive_utils.py` (`is_valid_archive`, nested scan and depth-0 messages).
- Spec: `nested-archive-classification` gains a requirement.
- Behavior: nested and top-level zip-based documents/packages are no longer exploded. Users who want the contents of such a file can rename it to `.zip`.
