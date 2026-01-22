# Spec Delta: Output path normalization (flatten meaningless folders)

## ADDED Requirements

### Requirement: Flatten meaningless leading folders under the output root
The system SHALL normalize extracted file output paths by removing meaningless **leading** directory segments under the final output folder.

#### Scenario: Numeric-only folder is flattened
- **GIVEN** a file would be placed at `unzipped/1/aaa.jpg`
- **WHEN** the tool finalizes the destination path under the output root
- **THEN** the file SHALL be placed at `unzipped/aaa.jpg`

#### Scenario: Numeric+symbol folder chain is flattened
- **GIVEN** a file would be placed at `unzipped/1/5555+/222.jpg`
- **WHEN** the tool finalizes the destination path under the output root
- **THEN** the file SHALL be placed at `unzipped/222.jpg`

### Requirement: Meaningful folders MUST be preserved
The system SHALL NOT flatten folders that contain letters or CJK characters.

#### Scenario: Meaningful folder is preserved
- **GIVEN** a file would be placed at `unzipped/photos/1/aaa.jpg`
- **WHEN** the tool finalizes the destination path under the output root
- **THEN** the file SHALL remain under `unzipped/photos/1/aaa.jpg`

### Requirement: Collisions MUST be handled safely
If output-path normalization causes multiple files to map to the same destination path, the system SHALL preserve all files by applying existing name-collision handling.

#### Scenario: Two inputs collide after flattening
- **GIVEN** two different extracted files would be placed at `unzipped/1/aaa.jpg` and `unzipped/2/aaa.jpg`
- **WHEN** the tool applies output-path normalization
- **THEN** both files SHALL exist under the output root
- **AND** at least one of them SHALL be renamed with a suffix to avoid overwriting

## MODIFIED Requirements
(None)

## REMOVED Requirements
(None)
