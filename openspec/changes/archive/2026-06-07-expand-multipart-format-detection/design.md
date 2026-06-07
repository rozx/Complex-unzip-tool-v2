## Context

Multi-part archive handling rests on one invariant: 7-Zip must be invoked on the
**primary** volume of a set, never a continuation part. That primary/continuation
distinction is duplicated across four files — `modules/regex.py`,
`classes/ArchiveGroup.py`, `modules/file_utils.py`, `modules/archive_utils.py` —
and must stay consistent (CLAUDE.md calls this out explicitly).

Today the catalog of recognized naming conventions is incomplete. Verified
current behavior:

| Set | Result today |
| --- | --- |
| `a.7z.001/.002` | ✅ one group, multipart, main `.001` |
| `a.tar.{gz,bz2,xz}.001/.002` | ✅ one group, multipart, main `.001` |
| `a.zip` + `a.z01/.z02` | ✅ one group, multipart, main `.zip` |
| `a.rar` + `a.r00/.r01` | ✅ one group, multipart, main `.rar` |
| `a.part1.rar/.part2.rar` (and padded) | ✅ one group, multipart, main `.part1` |
| `a.zip.001/.002` | ⚠️ one group but **not multipart** (single path; `.002` left behind) |
| `a.rar.001/.002` | ❌ **two groups** (base parsed as `a.rar`) |
| `a.iso.001` / `a.<ext>.001` | ❌ **two groups** |
| `a.zipx` + `a.zx01` | ❌ **three groups** |
| `a.arj` + `a.a01` | ❌ **three groups** |
| `a.ace` + `a.c00` | ❌ **three groups** |

Constraints: Windows-only; the bundled `7z.exe` is the only engine and **cannot
decode ACE**; tests mock the subprocess (no real `7z.exe`), so all logic here must
be unit-testable from filenames alone.

## Goals / Non-Goals

**Goals:**
- Recognize 7-Zip generic numbered volume splits `name.<ext>.NNN` for **any**
  `<ext>` (zip, rar, iso, bin, …) as one multipart set with `.001` as the
  primary entry point.
- Recognize native ZIPX (`.zipx`/`.zxNN`), ARJ (`.arj`/`.aNN`), ACE
  (`.ace`/`.cNN`) sets as one group with the correct primary.
- Keep every part of a set in a single `ArchiveGroup`; never select a
  continuation as the entry point; never treat a continuation as a nested
  archive during recursive extraction.
- Preserve all existing supported formats unchanged (regression-guarded).
- Preserve the deletion/retention safety model unchanged.

**Non-Goals:**
- Bare numeric splits with no archive token (`name.001/.002` with `name` having
  no extension) — out of scope (a separate concern; the earlier bug fix already
  keeps them safe).
- 1- and 2-digit numeric volume suffixes (`.1`, `.01`) — out of scope; only
  zero-padded ≥3-digit suffixes (what 7-Zip emits) are treated as volumes.
- Making ACE *extractable* — impossible with the bundled engine. ACE is
  recognized/grouped only; extraction failure is surfaced normally.
- Refactoring the existing duplicated primary/continuation logic into one module
  beyond what this change needs (kept atomic).

## Decisions

### D1 — One generic rule for 7-Zip numbered volume splits, ordered after the specific ones

7-Zip's splitter appends a zero-padded numeric run to the *whole* original
filename, so the canonical shape is `<name>.<ext>.<NNN>`. We add a single generic
classifier: a basename matching `\.[A-Za-z0-9]+\.\d{3,}$` is a numbered volume
whose **family extension** is the token immediately before the numeric run and
whose **base** is everything before that token.

Crucially this rule is applied **after** the existing specific patterns so their
behavior is preserved:
- `.7z.NNN` keeps family `7z` (specific rule first).
- `.tar.{gz,bz2,xz}.NNN` keeps base `name`, family `tar` (specific rule first).
- `.zip.NNN` keeps family `zip` (existing `\.zip\.\d+$` rule first).
- `.rar.NNN`, `.iso.NNN`, `.<ext>.NNN` fall through to the generic rule →
  family = `<ext>`.

Because both parts of a set yield the same `(base, family)`, they group via the
existing exact base+ext check — no change to grouping flow, only to parsing.

*Alternative considered:* enumerate each extension (`rar`, `iso`, `img`, …).
Rejected — 7-Zip splits *any* file, so enumeration is endless and brittle. A
single token-capturing rule covers all cases at zero marginal cost.

### D2 — Primary entry point is the `.001`; classification is filename-only

Extend the entry-point priority so a numbered first volume `\.[A-Za-z0-9]+\.0*1$`
ranks as a primary (high priority) and numbered continuations rank as
non-entry-points (zero). `multipart_regex` gains the generic numbered pattern so
`isMultiPart` becomes true; `first_part_regex` gains the numbered `.001` primary.
The continuation-skip logic in `archive_utils` and the candidate-key/primary
helpers gain the generic numbered patterns so continuations are relocated/skipped
(never recursed into, never chosen as entry).

The "require `.001`" rule from the scope decision is realized as: the `.001`
ranks above all numbered continuations, so whenever it is present it is chosen as
`mainArchiveFile`. If `.001` is absent, no high-priority numbered primary exists;
the set still groups, extraction is attempted and fails, and parts are retained
(safe — see D5).

### D3 — Native ZIPX / ARJ / ACE via family mapping (mirrors ZIP/RAR)

These behave like the existing ZIP (`.zip`/`.zNN`) and RAR (`.rar`/`.rNN`)
families: a non-numeric primary plus lettered continuations.

| Format | Primary | Continuation | Family key |
| --- | --- | --- | --- |
| ZIPX | `.zipx` | `.zxNN` | `zipx` |
| ARJ | `.arj` | `.aNN` | `arj` |
| ACE | `.ace` | `.cNN` | `ace` |

Implementation parallels the existing ZIP/RAR handling: family-map the
continuation suffix to the family ext in `get_archive_base_name`; map the primary
extension to the same family; add the continuation patterns to `multipart_regex`;
rank the primary in `_entry_point_priority` (same tier as `.zip`/`.rar`); add the
continuations to the `archive_utils` skip/candidate logic. The existing
`_derive_folder_name` already recognizes `[zrac][0-9]{2}`, so the `a`/`c`
conventions are already partially anticipated in the codebase.

### D4 — Centralize the new patterns in `regex.py`, reference them elsewhere

To limit the drift hazard, the new generic + ZIPX/ARJ/ACE patterns are defined as
named constants (and small predicate helpers) in `modules/regex.py`, and the
other three modules import them rather than re-spelling the regexes. Existing
duplicated patterns are left in place to keep the change atomic, but new coverage
goes through the shared definitions.

### D5 — Safety unchanged: success-only deletion absorbs false positives

We deliberately do **not** add an "is this really an archive?" gate at grouping
time. Ordinary numbered files (e.g. `report.2024.001`) may be classified as a
volume and an extraction attempt may be made, but originals are deleted only when
extraction *succeeds* (`_should_delete_original_archives`), and multipart sets are
retained on failure (`multipart-retention`). So the worst case for a false
positive is a wasted extraction attempt, never data loss.

### D6 — ACE recognized but not extractable

The bundled 7-Zip cannot decode ACE. ACE sets are grouped correctly (so they
don't fragment into wrong groups and the user sees one set), but extraction will
fail and the parts are retained via the normal failure path. This limitation is
documented in the spec and release notes; no special code path is needed.

## Risks / Trade-offs

- **Generic `\.[A-Za-z0-9]+\.\d{3,}$` over-matches ordinary numbered files**
  (e.g. `db.backup.001`) → Mitigation: require zero-padded ≥3 digits (matches
  7-Zip output, excludes `.1`/`.01`); deletion is success-only so misclassified
  non-archives are retained on the failed extraction attempt.
- **Single-letter `a\d{2}` / `c\d{2}` continuation patterns collide** with
  non-archive names like `clip.a01` → Mitigation: the convention is already
  embedded in the codebase (`[zrac][0-9]{2}`); impact is bounded by success-only
  deletion; only affects grouping, which is recoverable.
- **`tar.*` vs generic ordering regression** if the generic rule is mistakenly
  evaluated first (would reparse `a.tar.gz.001` as base `a.tar`, family `gz`) →
  Mitigation: explicit ordering (specific patterns first) plus regression tests
  pinning `a.tar.gz.001 → (a, tar)` and `a.7z.001 → (a, 7z)`.
- **ACE user confusion** (grouped but won't extract) → Mitigation: clear
  bilingual failure message path already exists (`ArchiveUnsupportedError`);
  documented limitation.

## Migration Plan

Pure classification/logic change; no data or config migration. Ship behind no
flag. Rollback = revert the commit. TDD throughout: each new pattern and each
touch point gets a failing test first, then the minimal change, with the full
existing suite kept green as the regression guard.

## Open Questions

- None blocking. Possible follow-ups (out of scope): bare-numeric `name.001`
  multipart support; centralizing the *existing* duplicated primary/continuation
  logic into `regex.py` helpers.
