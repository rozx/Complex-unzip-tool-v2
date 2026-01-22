# Spec Delta: Contained multipart preservation

## ADDED Requirements

### Requirement: Preserve multipart parts extracted from containers
The system SHALL ensure multipart archive parts that are extracted from within a container archive (including continuation parts such as `.7z.002+`, `.r00/.r01+`, `.z01/.z02+`, `.part2+.rar`, `.tar.gz.002+`) are not lost due to temporary directory cleanup.

#### Scenario: Try extraction first, then preserve on failure
- **GIVEN** an outer archive is extracted into a temporary extraction directory
- **AND** the extracted contents include a multipart set containing `x.7z.001` and `x.7z.002`
- **WHEN** the tool attempts to extract `x.7z.001` and extraction fails
- **AND** matching the extracted candidate parts to missing volumes does not make extraction succeed
- **THEN** `x.7z.002` SHALL be moved to the target output folder before the temp directory is removed
- **AND** `x.7z.002` SHALL exist on disk after the run completes

#### Scenario: Candidate part is cleaned after enabling successful extraction
- **GIVEN** an outer archive is extracted into a temporary extraction directory
- **AND** the extracted contents include a multipart set containing `x.7z.001` and `x.7z.002`
- **WHEN** extracting `x.7z.001` initially fails due to missing parts
- **AND** the tool matches `x.7z.002` to the current archive’s missing multipart volumes
- **AND** extraction succeeds after matching
- **THEN** `x.7z.002` SHALL be eligible for cleanup as a temporary, tool-extracted artifact

#### Scenario: Continuation part is relocated
- **GIVEN** nested scanning identifies a continuation part extracted from a container
- **AND** a `group_relocator` callback is provided
- **WHEN** `group_relocator` returns `True` for that file
- **THEN** the system SHALL treat the continuation part as relocated
- **AND** it SHALL NOT be processed as a nested archive
- **AND** it SHALL NOT be deleted due to temp cleanup

### Requirement: Skipping recursion MUST NOT imply deletion
The system SHALL ensure that skipping a file from recursive nested extraction does not implicitly delete the file, unless the file is a tool-created temporary artifact.

#### Scenario: Temp cleanup runs after nested extraction
- **GIVEN** nested extraction returns and the caller removes the temp extraction directory
- **WHEN** files were skipped from recursion for policy reasons (e.g., multipart continuation parts)
- **THEN** those skipped files SHALL already have been preserved to a persistent output location or relocated

## MODIFIED Requirements
(None)

## REMOVED Requirements
(None)
