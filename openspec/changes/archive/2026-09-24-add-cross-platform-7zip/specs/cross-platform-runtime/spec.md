# Spec Delta

## Purpose

Provide offline archive extraction and standalone command-line distribution using native 7-Zip engines on supported Windows, macOS, and Linux systems.

## ADDED Requirements

### Requirement: Native offline archive engine
The system SHALL bundle official 7-Zip 26.03 for Windows x64, macOS x64/ARM64, and Linux x64/ARM64 and automatically select the compatible engine without network access or a system installation. Existing explicit executable-path overrides SHALL remain supported.

#### Scenario: Source and standalone execution
- **WHEN** the application lists or extracts an archive on a supported platform from any working directory
- **THEN** it SHALL use the matching bundled native engine in both source and standalone execution
- **AND** password, multipart, nested extraction, and source retention behavior SHALL be preserved

#### Scenario: Explicit executable override
- **WHEN** a caller supplies an executable file path
- **THEN** listing and extraction SHALL use that file instead of the bundled default

### Requirement: Engine errors precede CLI file mutations
The CLI SHALL report an actionable error and exit unsuccessfully before modifying input files when its bundled engine is missing, lacks execute permission, lacks required companion files, or the platform is unsupported. Help and version SHALL remain available without an engine.

#### Scenario: Missing or unusable engine
- **WHEN** extraction is requested with an unavailable engine
- **THEN** input names and contents SHALL remain unchanged
- **AND** the CLI SHALL identify the engine or platform problem

### Requirement: Platform-native standalone distribution
The build command SHALL produce a standalone console program for the host platform, including only its native engine and required redistribution notices. It SHALL validate required assets before removing previous build output.

#### Scenario: Building on macOS or Linux
- **WHEN** the build command runs on a supported macOS or Linux host
- **THEN** it SHALL produce `dist/complex-unzip-tool-v2` with an executable bundled engine

#### Scenario: Building on Windows
- **WHEN** the build command runs on Windows x64
- **THEN** it SHALL produce `dist/complex-unzip-tool-v2.exe` with the updated engine and its DLL

#### Scenario: Incomplete build inputs
- **WHEN** a required engine file or license is missing
- **THEN** the build SHALL fail clearly without deleting existing output

### Requirement: Terminal-compatible exit
Standalone programs SHALL pause on exit only for interactive Windows terminals.

#### Scenario: POSIX or redirected invocation
- **WHEN** a macOS/Linux standalone command completes or Windows stdin is redirected
- **THEN** the application SHALL exit without requesting an additional Enter key
