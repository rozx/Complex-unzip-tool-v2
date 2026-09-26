## ADDED Requirements

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
