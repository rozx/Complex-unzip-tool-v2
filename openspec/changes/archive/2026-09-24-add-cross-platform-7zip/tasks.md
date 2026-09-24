# Tasks

## 1. Runtime and bundled engine

- [x] 1.1 Add native engine selection using TDD at the archive listing/extraction boundary; verify supported OS/architecture mappings, frozen roots, explicit overrides, and unavailable engines.
- [x] 1.2 Replace Windows assets and add macOS/Linux engines from official 26.03 packages; verify upstream SHA-256 digests, bundled-file hashes, architecture, and licenses.
- [x] 1.3 Add CLI preflight and platform-aware exit behavior with failing-then-passing CLI tests; verify input preservation and help/version availability.

## 2. Build and documentation

- [x] 2.1 Use native runtime assets in the standalone builder with failing-then-passing build tests; verify native binary selection, notices, output names, and missing-asset behavior.
- [x] 2.2 Update both READMEs and project guidance; verify platform matrix and source/build commands match implementation.

## 3. Validation and closure

- [x] 3.1 Run the full existing suite, CLI smoke, formatting/lint/type checks; distinguish pre-existing failures from regressions in a validation record.
- [x] 3.2 Perform real archive/password/multipart smoke checks on macOS and available Linux containers and build/run the native macOS executable; record native Windows validation limits.
- [x] 3.3 Validate OpenSpec, sync the new capability, and archive the completed change.
