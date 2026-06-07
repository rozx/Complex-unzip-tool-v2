## Why

The tool only reliably recognizes a subset of multi-part archive naming
conventions. 7-Zip's generic volume splitter produces `name.<ext>.001/.002/…`
for **any** source file, yet only `.7z.001` and `.tar.{gz,bz2,xz}.001` are
detected today — `name.zip.001` (common), `name.rar.001`, `name.iso.001`, and
any other `<ext>.001` are split into multiple wrong groups or mis-handled as
single archives, so they fail to extract and leave continuation parts behind.
WinZip ZIPX splits (`.zx01/.zipx`) and ARJ/ACE multi-volume sets are likewise
unrecognized. Users with these formats get incorrect grouping and data left
unextracted.

## What Changes

- Recognize **7-Zip generic numbered volume splits for ANY base extension**:
  `name.<ext>.001/.002/…` (zero-padded, 3+ digits, requires a `.001` entry) as
  one multipart set whose primary entry point is the `.001` part. Covers
  `name.zip.001`, `name.rar.001`, `name.iso.001`, and arbitrary `<ext>`.
  `name.7z.001` and `name.tar.{gz,bz2,xz}.001` keep their current behavior.
- Recognize **WinZip ZIPX split**: `name.zx01/.zx02/… + name.zipx`; primary is
  `name.zipx`, continuations are `.zxNN`.
- Recognize **ARJ multi-volume**: `name.arj + name.a01/.a02/…`; primary is
  `name.arj`, continuations are `.aNN`.
- Recognize **ACE multi-volume**: `name.ace + name.c00/.c01/…`; primary is
  `name.ace`, continuations are `.cNN`. NOTE: classification/grouping only — the
  bundled 7-Zip **cannot decode ACE**, so extraction still fails and is surfaced
  as a normal extraction failure (source parts retained, nothing deleted).
- Every part of a recognized set groups into **one** `ArchiveGroup` with the
  correct primary as `mainArchiveFile`; continuation parts are never selected as
  the extraction entry point and are not treated as nested archives during
  recursive extraction (they are relocated/skipped like existing continuations).
- Preserve existing safety: extraction-success is still the only trigger for
  deleting originals, so a false-positive numbered file (e.g. `report.2024.001`)
  that is not actually an archive is retained when extraction fails — no data
  loss.

## Capabilities

### New Capabilities

- `multipart-format-detection`: the canonical catalog of supported multi-part
  naming conventions across all archive formats; classification of each filename
  as a primary entry point vs a continuation part; the guarantee that all parts
  of one set form a single group with the correct primary; and continuation
  handling during recursive/nested extraction (never an entry point, never a
  nested archive).

### Modified Capabilities

- `contained-zip-rar-autogrouping`: extend contained-set auto-grouping
  (`ensure_contained_multipart_groups`) so sets discovered from containers in the
  output folder are also created for the newly supported formats — generic
  `name.<ext>.001`, ZIPX, ARJ, ACE — not only ZIP/RAR.

## Impact

- Code (the cross-cutting primary/continuation invariant, kept consistent across
  files):
  - `modules/regex.py` — `multipart_regex`, `first_part_regex`.
  - `classes/ArchiveGroup.py` — `_entry_point_priority`.
  - `modules/file_utils.py` — `get_archive_base_name`,
    `ensure_contained_multipart_groups`, `relocate_multipart_parts_from_directory`.
  - `modules/archive_utils.py` — continuation-skip logic,
    `_multipart_key_from_basename`, `_is_multipart_primary`,
    `_find_matching_candidate_parts`.
- Behavior: more sets correctly recognized and extracted; **no change** to the
  deletion/retention safety model.
- Tests: extensive new grouping/classification cases (TDD), plus regression for
  the existing supported formats.
- No new dependencies; Windows-only; bundled 7-Zip binary unchanged. ACE remains
  non-extractable by the bundled engine (documented limitation).
