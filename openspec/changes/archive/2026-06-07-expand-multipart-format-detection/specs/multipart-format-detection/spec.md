## ADDED Requirements

### Requirement: Recognize 7-Zip generic numbered volume splits for any base extension

The tool MUST recognize files named `name.{ext}.NNN` (a zero-padded numeric suffix of 3 or more digits) as one 7-Zip generic volume split, for any base extension `{ext}` (e.g. `zip`, `rar`, `iso`, `bin`). All parts of the set MUST be placed in one `ArchiveGroup`, the group MUST be marked multipart, and `mainArchiveFile` MUST be the `.001` part (the lowest numbered volume), regardless of the order the files are added. The existing behavior for `name.7z.NNN` and `name.tar.{gz,bz2,xz}.NNN` MUST be preserved unchanged.

#### Scenario: Split ZIP volumes group with the .001 as primary
- **WHEN** `create_groups_by_name` processes `a.zip.001` and `a.zip.002` in one directory
- **THEN** exactly one group is produced, it is multipart, and its `mainArchiveFile` is `a.zip.001`

#### Scenario: Split RAR volumes group with the .001 as primary
- **WHEN** `create_groups_by_name` processes `a.rar.001` and `a.rar.002` in one directory
- **THEN** exactly one group is produced, it is multipart, and its `mainArchiveFile` is `a.rar.001`

#### Scenario: Split ISO (arbitrary extension) volumes group with the .001 as primary
- **WHEN** `create_groups_by_name` processes `a.iso.001` and `a.iso.002` in one directory
- **THEN** exactly one group is produced, it is multipart, and its `mainArchiveFile` is `a.iso.001`

#### Scenario: Existing 7z and tar split parsing is preserved
- **WHEN** `get_archive_base_name` parses `a.7z.001` and `a.tar.gz.001`
- **THEN** `a.7z.001` yields base `a` and family `7z`, and `a.tar.gz.001` yields base `a` and family `tar`

#### Scenario: Primary selection is independent of insertion order
- **WHEN** a group is built by adding `a.zip.002` before `a.zip.001`
- **THEN** `mainArchiveFile` is still `a.zip.001`

### Requirement: Numbered continuation parts are never entry points or nested archives

A numbered continuation part `name.<ext>.NNN` with `NNN` not equal to 1 MUST NOT
be selected as `mainArchiveFile`, MUST NOT be treated as a nested archive during
recursive extraction, and MUST be relocated next to its primary or skipped like
other multipart continuations.

#### Scenario: Continuation discovered during nested extraction is not recursed into
- **WHEN** recursive extraction encounters `name.zip.002` among extracted files
- **THEN** it is relocated to its multipart group or recorded/skipped as a continuation, and is not extracted as a nested archive

#### Scenario: Continuation cannot win primary selection
- **WHEN** entry-point priority is evaluated for `a.iso.002`
- **THEN** it scores as a non-entry-point (lower than the `.001` primary)

### Requirement: Recognize WinZip ZIPX split sets

A set named `name.zipx` plus `name.zx01`, `name.zx02`, … MUST be recognized as a
single multipart set, grouped into one `ArchiveGroup`, marked multipart, with
`mainArchiveFile` set to `name.zipx`. The `.zxNN` files MUST be classified as
continuations.

#### Scenario: ZIPX split set groups with .zipx as primary
- **WHEN** `create_groups_by_name` processes `a.zipx`, `a.zx01`, and `a.zx02` in one directory
- **THEN** exactly one group is produced, it is multipart, and its `mainArchiveFile` is `a.zipx`

### Requirement: Recognize ARJ multi-volume sets

A set named `name.arj` plus `name.a01`, `name.a02`, … MUST be recognized as a
single multipart set, grouped into one `ArchiveGroup`, marked multipart, with
`mainArchiveFile` set to `name.arj`. The `.aNN` files MUST be classified as
continuations.

#### Scenario: ARJ multi-volume set groups with .arj as primary
- **WHEN** `create_groups_by_name` processes `a.arj`, `a.a01`, and `a.a02` in one directory
- **THEN** exactly one group is produced, it is multipart, and its `mainArchiveFile` is `a.arj`

### Requirement: Recognize ACE multi-volume sets (classification only)

A set named `name.ace` plus `name.c00`, `name.c01`, … MUST be recognized as a
single multipart set, grouped into one `ArchiveGroup`, marked multipart, with
`mainArchiveFile` set to `name.ace`, and the `.cNN` files classified as
continuations. Because the bundled 7-Zip engine cannot decode ACE, extraction of
such a set MUST fail through the normal failure path and the source parts MUST be
retained (no deletion).

#### Scenario: ACE multi-volume set groups with .ace as primary
- **WHEN** `create_groups_by_name` processes `a.ace`, `a.c00`, and `a.c01` in one directory
- **THEN** exactly one group is produced, it is multipart, and its `mainArchiveFile` is `a.ace`

#### Scenario: ACE extraction failure retains source parts
- **WHEN** extraction of an ACE multipart set fails because the engine cannot decode ACE
- **THEN** the source `.ace`/`.cNN` parts remain in place and are not deleted, recycled, or moved away

### Requirement: Distinct archive families sharing a base name are not merged

Files that share a base name and directory but belong to different archive families MUST NOT be grouped together; only files of the same family (including its continuation parts) may form a group.

#### Scenario: A standalone .7z is not merged into a spanned .zip set
- **WHEN** `create_groups_by_name` processes `foo.7z`, `foo.zip`, `foo.z01`, and `foo.z02` in one directory
- **THEN** two groups are produced: a single-archive group for `foo.7z`, and a multipart group for the spanned zip with `mainArchiveFile` `foo.zip`

### Requirement: Misclassified numbered non-archives are never deleted

The tool MUST NOT delete, recycle, or move away an ordinary numbered file (e.g. `report.2024.001`) that was classified as a volume but is not actually an archive; source deletion happens only after a successful extraction.

#### Scenario: A non-archive numbered file survives a failed extraction attempt
- **WHEN** a numbered file that is not a valid archive is processed as a multipart primary and extraction fails
- **THEN** the file remains in place and is not deleted, recycled, or moved away
