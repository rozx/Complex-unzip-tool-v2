# cloaked-rename-collision Specification

## Purpose
TBD - created by archiving change handle-cloaked-rename-collision. Update Purpose after archive.
## Requirements
### Requirement: Collision-safe cloaked normalization
When normalizing cloaked archive filenames, the system SHALL treat rename collisions as non-fatal and continue processing using the already-normalized target file.

#### Scenario: Cloaked and normalized parts coexist
- **GIVEN** a folder contains `9.7z(1).001` and `9.7z.001`
- **WHEN** cloaked normalization runs
- **THEN** the system SHALL not fail due to a rename error
- **AND** the normalized file (`9.7z.001`) SHALL be preferred for grouping and extraction
- **AND** the cloaked duplicate SHALL be renamed to a unique name
- **AND** a warning about the duplicate SHALL be recorded

