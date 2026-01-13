# Spec Delta: Contained ZIP/RAR auto-grouping

## ADDED Requirements

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

## MODIFIED Requirements

None.

## REMOVED Requirements

None.
