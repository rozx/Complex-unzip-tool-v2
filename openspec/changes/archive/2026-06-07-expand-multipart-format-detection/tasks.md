## 1. Regex foundation (`modules/regex.py`)

- [x] 1.1 Write failing tests for new pattern constants/predicates: generic numbered volume (`name.{ext}.NNN`, 3+ digit), its `.001` primary, and ZIPX/ARJ/ACE continuations (`.zxNN`, `.aNN`, `.cNN`)
- [x] 1.2 Add named patterns to `regex.py`: extend `multipart_regex` with generic `\.[A-Za-z0-9]+\.\d{3,}`, `zx\d{2}`, `a\d{2}`, `c\d{2}`; extend `first_part_regex` with generic numbered `\.[A-Za-z0-9]+\.0*1`
- [x] 1.3 Confirm `multipart_regex` still matches existing formats and does NOT match 1/2-digit suffixes (`.1`, `.01`); run regex tests green

## 2. Base-name parsing (`file_utils.get_archive_base_name`)

- [x] 2.1 Write failing tests: `a.zip.001→(a,zip)`, `a.rar.001→(a,rar)`, `a.iso.001→(a,iso)`, `a.zx01→(a,zipx)`, `a.a01→(a,arj)`, `a.c00→(a,ace)`, and regression `a.7z.001→(a,7z)`, `a.tar.gz.001→(a,tar)`
- [x] 2.2 Add generic numbered rule AFTER the specific patterns; add ZIPX/ARJ/ACE entries to `family_pattern_map`; map `.zipx/.arj/.ace` primaries to their family ext
- [x] 2.3 Run parsing tests green; verify ordering keeps tar/7z behavior unchanged

## 3. Entry-point priority (`classes/ArchiveGroup._entry_point_priority`)

- [x] 3.1 Write failing tests: `.{ext}.001` ranks as primary (beats `.{ext}.NNN`); `.zipx/.arj/.ace` rank as primaries; continuations score 0
- [x] 3.2 Add generic numbered `.0*1` primary rule and ZIPX/ARJ/ACE primary rules to `_entry_point_priority`
- [x] 3.3 Run priority tests green

## 4. Grouping integration (`file_utils.create_groups_by_name`)

- [x] 4.1 Write failing tests for spec scenarios: each set (`a.zip.001/.002`, `a.rar.001/.002`, `a.iso.001/.002`, `a.zipx+.zx01/.zx02`, `a.arj+.a01/.a02`, `a.ace+.c00/.c01`) → exactly one multipart group with the correct `mainArchiveFile`
- [x] 4.2 Add test that primary selection is insertion-order independent (`.002` added before `.001` still picks `.001`)
- [x] 4.3 Confirm green with no production change here (driven by tasks 1–3); fix any gap surfaced

## 5. Nested-extraction continuation handling (`modules/archive_utils.py`)

- [x] 5.1 Write failing tests (mocked) that generic numbered continuations and `.zxNN/.aNN/.cNN` are skipped/relocated, never recursed as nested archives, never chosen as entry point
- [x] 5.2 Extend the continuation-skip block, `_multipart_key_from_basename`, `_is_multipart_primary`, and `_find_matching_candidate_parts` for the new patterns
- [x] 5.3 Run archive_utils tests green

## 6. Contained auto-grouping (`file_utils.ensure_contained_multipart_groups`)

- [x] 6.1 Write failing tests: contained `X.{ext}.001` creates a group from `.001` alone; contained `.zipx/.arj/.ace` create a group only when a continuation is present; standalone `.arj` alone does not
- [x] 6.2 Extend `ensure_contained_multipart_groups` to detect generic numbered primaries and ZIPX/ARJ/ACE (with the continuation-required guard)
- [x] 6.3 Run tests green

## 7. Regression & quality gates

- [x] 7.1 Run full suite (`poetry run pytest -q`) — all green, existing formats unchanged
- [x] 7.2 Run `black`, `flake8`, `mypy`, and `--help` smoke; fix any issues introduced by this change only

## 8. Documentation

- [x] 8.1 Update the primary/continuation rules in `CLAUDE.md` and `AGENTS.md` to include generic `name.{ext}.001`, ZIPX, ARJ, ACE
- [x] 8.2 Add a release note for v1.2.1 covering the expanded multipart format coverage, and explicitly note the ACE limitation (recognized/grouped but not extractable by the bundled 7-Zip)
