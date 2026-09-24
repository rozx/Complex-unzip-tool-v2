# Tasks

## 1. Build helpers

- [x] 1.1 Implement version validation, archive packaging, and complete release checksum validation with failing-then-passing pytest coverage.
- [x] 1.2 Add a reusable real archive smoke command and verify both source and standalone runs locally.

## 2. GitHub workflows

- [x] 2.1 Add five-platform CI and reuse it for the immutable release merge commit; validate YAML and expressions with actionlint.
- [x] 2.2 Implement the labeled merge trigger and bounded draft publication; exercise trigger, conflict, retry, and upload-failure cases without remote writes.

- [x] 2.3 Read exact-version repository notes, reject missing/empty files in preflight, and verify body preservation for new releases and draft retries.

## 3. Validation and documentation

- [x] 3.1 Document version preparation, release trigger, outputs, and retry behavior in both READMEs; verify commands and artifact names match implementation.
- [x] 3.2 Run full tests and local build/package/smoke checks, record unavailable native runner validation, and archive the validated OpenSpec change.
