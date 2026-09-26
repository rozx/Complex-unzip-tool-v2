# nested-archive-classification Specification

## Purpose
Decide which files found inside extracted archives are themselves archives, so that only real containers are extracted and every other file (executables, documents, media) is kept intact, and keep nested cleanup recoverable.

## Requirements

### Requirement: Classify archives by 7-Zip archive-level type
The system SHALL decide whether a file is an archive from the archive-level `Type =` field that `7z l -slt` prints in its header block (before the first `----------` line), using the innermost header `Type` when several are present. Only container formats on the archive allowlist SHALL be classified as archives; any other type SHALL be treated as a regular file.

#### Scenario: Plain executable inside an archive
- **WHEN** a nested file's `7z l -slt` header reports `Type = PE`
- **THEN** the file SHALL be classified as a regular file, kept unchanged, and SHALL NOT be extracted or deleted

#### Scenario: Self-extracting archive inside an archive
- **WHEN** a nested `.exe` header reports `Type = 7z` with `Offset = 215040`
- **THEN** the file SHALL be classified as an archive and extracted

#### Scenario: Executable with unrecognized overlay
- **WHEN** 7-Zip reports `Cannot open the file as archive` for a nested `.exe`
- **THEN** the file SHALL be classified as a regular file

#### Scenario: Split volume
- **WHEN** a `.7z.001` header reports `Type = Split` followed by `Type = 7z`
- **THEN** the innermost type `7z` SHALL be used and the file classified as an archive

#### Scenario: Entry-level Type after the header
- **WHEN** the header reports `Type = PE` and a listed entry later reports `Type = 7z`
- **THEN** only the header type SHALL be considered and the file classified as a regular file

#### Scenario: Password-protected archive
- **WHEN** listing fails with a password error
- **THEN** the file SHALL still be classified as an archive

### Requirement: Recoverable nested cleanup
Removal of processed nested archives SHALL follow the user's deletion mode: moved to the Recycle Bin by default, permanently deleted only when `--permanent-delete` is given.

#### Scenario: Default run
- **WHEN** extraction runs without `--permanent-delete` and a nested archive is cleaned up
- **THEN** the nested archive SHALL be sent to the Recycle Bin

#### Scenario: Permanent delete requested
- **WHEN** extraction runs with `--permanent-delete`
- **THEN** processed nested archives SHALL be permanently deleted

### Requirement: Keep zip-based documents and packages as files
The system SHALL classify a file as a regular file, not an archive, when its archive-level 7-Zip type is `zip` and its final extension (case-insensitive) is a known zip-based document or package extension (Office Open XML, OpenDocument, EPUB/XPS, Java/Android/iOS/Windows/browser/IDE packages). Files of any other type, and zip files with any other extension, SHALL be classified as before.

#### Scenario: Office document inside an archive
- **WHEN** a nested `report.docx` reports `Type = zip`
- **THEN** the file SHALL be kept unchanged as a regular file and SHALL NOT be extracted or deleted

#### Scenario: Package with upper-case extension
- **WHEN** a nested `LIB.JAR` reports `Type = zip`
- **THEN** the file SHALL be classified as a regular file

#### Scenario: Zip disguised with a media extension
- **WHEN** a nested `photo.jpg` reports `Type = zip`
- **THEN** the file SHALL be classified as an archive and extracted

#### Scenario: Non-zip container named like a document
- **WHEN** a nested `pack.docx` reports `Type = 7z`
- **THEN** the file SHALL be classified as an archive and extracted

#### Scenario: Comic book archive
- **WHEN** a nested `issue1.cbz` reports `Type = zip`
- **THEN** the file SHALL be classified as an archive and extracted

#### Scenario: Top-level document in a scanned folder
- **WHEN** a folder scan yields `report.docx` reporting `Type = zip`
- **THEN** the file SHALL NOT be extracted or deleted, and the user SHALL be told it was kept as a document/package
