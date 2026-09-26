# contained-zip-rar-autogrouping Specification

## Purpose
Register multi-volume sets (spanned ZIP, RAR, ZIPX, ARJ, ACE and generic numbered splits) that appear after extracting a container as multipart groups, so they are extracted in the same run.
## Requirements
### Requirement: Auto-group spanned ZIP sets discovered from containers

When a spanned ZIP set is discovered in the output folder (typically after extracting a container in Step 7), the tool MUST create a multipart group for it so Step 8 can attempt multipart extraction in the same run. Because `.zip` is ambiguous, the tool MUST NOT auto-group a `.zip` unless at least one `.zNN` continuation part is present.

#### Scenario: Create a multipart group when both `.zip` and `.z01` exist
Given Step 7 has moved files into the output folder and `ensure_contained_multipart_groups(file_paths, groups)` is invoked
And a directory bucket contains `X.zip` and at least one `X.zNN` continuation part (e.g., `X.z01`)
When auto-grouping runs
Then a new multipart `ArchiveGroup` MUST be created for base `X` (if no existing group for the same (dir, base) exists)
And the group MUST include the `.zip` and the discovered `.zNN` parts
And the group’s `mainArchiveFile` MUST be set to `X.zip`.

#### Scenario: Do not create a multipart group for a standalone `.zip`
Given Step 7 has moved files into the output folder and `ensure_contained_multipart_groups(file_paths, groups)` is invoked
And a directory bucket contains `X.zip` but no `X.zNN` continuation parts
When auto-grouping runs
Then no new multipart group MUST be created for `X` based on that `.zip` alone.

### Requirement: Auto-group RAR volume sets discovered from containers

When a RAR volume set is discovered in the output folder (typically after extracting a container in Step 7), the tool MUST create a multipart group for it so Step 8 can attempt multipart extraction in the same run. Because `.rar` is ambiguous, the tool MUST NOT auto-group a `.rar` unless at least one `.rNN` continuation part is present.

#### Scenario: Create a multipart group when both `.rar` and `.r00` exist
Given Step 7 has moved files into the output folder and `ensure_contained_multipart_groups(file_paths, groups)` is invoked
And a directory bucket contains `X.rar` and at least one `X.rNN` continuation part (e.g., `X.r00`)
When auto-grouping runs
Then a new multipart `ArchiveGroup` MUST be created for base `X` (if no existing group for the same (dir, base) exists)
And the group MUST include the `.rar` and the discovered `.rNN` parts
And the group’s `mainArchiveFile` MUST be set to `X.rar`.

#### Scenario: Do not create a multipart group for a standalone `.rar`
Given Step 7 has moved files into the output folder and `ensure_contained_multipart_groups(file_paths, groups)` is invoked
And a directory bucket contains `X.rar` but no `X.rNN` continuation parts
When auto-grouping runs
Then no new multipart group MUST be created for `X` based on that `.rar` alone.

### Requirement: Auto-group generic numbered volume sets discovered from containers

`ensure_contained_multipart_groups` MUST create a multipart group for a generic 7-Zip numbered volume set discovered in the output folder (typically after extracting a container in Step 7) so Step 8 can attempt extraction in the same run. A `name.{ext}.001` part is an unambiguous primary, so the group MAY be created from the `.001` alone (no continuation required), with `mainArchiveFile` set to the `.001`.

#### Scenario: Create a multipart group from a contained split ZIP volume set
- **WHEN** Step 7 has moved `X.zip.001` (and any `X.zip.002`, …) into the output folder and `ensure_contained_multipart_groups(file_paths, groups)` is invoked
- **THEN** a new multipart `ArchiveGroup` is created for base `X` (if none exists for the same dir+base) including the discovered numbered parts, with `mainArchiveFile` set to `X.zip.001`

#### Scenario: Create a multipart group from a contained split set of arbitrary extension
- **WHEN** Step 7 has moved `X.iso.001` and `X.iso.002` into the output folder and `ensure_contained_multipart_groups(file_paths, groups)` is invoked
- **THEN** a new multipart `ArchiveGroup` is created for base `X` with `mainArchiveFile` set to `X.iso.001`

### Requirement: Auto-group ZIPX, ARJ, and ACE sets discovered from containers

`ensure_contained_multipart_groups` MUST create a multipart group for a ZIPX, ARJ, or ACE multi-volume set discovered in the output folder. Because the `.zipx`, `.arj`, and `.ace` primaries are ambiguous (they can also be standalone single archives), the tool MUST NOT auto-group one of them unless at least one of its continuation parts (`.zxNN`, `.aNN`, `.cNN` respectively) is present in the same bucket.

#### Scenario: Create a multipart group when both .zipx and .zx01 exist
- **WHEN** a directory bucket contains `X.zipx` and at least one `X.zxNN` continuation part and auto-grouping runs
- **THEN** a new multipart `ArchiveGroup` is created for base `X` (if none exists for the same dir+base) including the `.zipx` and the discovered `.zxNN` parts, with `mainArchiveFile` set to `X.zipx`

#### Scenario: Create a multipart group when both .arj and .a01 exist
- **WHEN** a directory bucket contains `X.arj` and at least one `X.aNN` continuation part and auto-grouping runs
- **THEN** a new multipart `ArchiveGroup` is created for base `X` with `mainArchiveFile` set to `X.arj`

#### Scenario: Do not auto-group a standalone .arj
- **WHEN** a directory bucket contains `X.arj` but no `X.aNN` continuation parts and auto-grouping runs
- **THEN** no new multipart group is created for `X` based on that `.arj` alone

#### Scenario: Create a multipart group when both .ace and .c00 exist
- **WHEN** a directory bucket contains `X.ace` and at least one `X.cNN` continuation part and auto-grouping runs
- **THEN** a new multipart `ArchiveGroup` is created for base `X` with `mainArchiveFile` set to `X.ace`

