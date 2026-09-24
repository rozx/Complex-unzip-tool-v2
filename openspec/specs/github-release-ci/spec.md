# github-release-ci Specification

## Purpose
Automatically validate native builds and publish complete, versioned downloads when maintainers merge an explicitly labeled release pull request.

## Requirements

### Requirement: Five native build targets
CI SHALL test and build Windows x64, macOS x64/ARM64, and Linux x64/ARM64 using native hosted runners. Each build SHALL verify the bundled engines, the existing test suite, and real source/standalone archive extraction before uploading an artifact.

#### Scenario: A platform fails
- **WHEN** any platform's tests, build, or smoke check fails
- **THEN** the run SHALL fail and SHALL NOT publish a release

#### Scenario: A newer commit supersedes ordinary CI
- **WHEN** another push or PR update starts checks for the same event and ref
- **THEN** the older ordinary CI run SHALL be cancelled
- **AND** reusable release builds SHALL remain isolated from ordinary CI cancellation and publish only artifacts from their own workflow run

### Requirement: Release trigger is an eligible merged PR
Publication SHALL occur only after a PR from `release/*` merges into `main` with the `release` label present at merge time. Every release build and tag SHALL correspond to that PR's merge commit.

#### Scenario: Eligible merge
- **WHEN** a labeled `release/v1.3` PR merges into `main`
- **THEN** the release pipeline SHALL build all five targets from that merge commit

#### Scenario: Non-release event
- **WHEN** a PR is closed without merging, lacks the label, uses another source branch, or targets another base branch
- **THEN** no release SHALL be published

### Requirement: Consistent version and complete downloadable assets
The release SHALL use `vX.Y.Z` from the consistent project version declarations, include five platform archives and a checksum index, preserve Unix execute permissions, and include redistribution notices. Missing assets, inconsistent versions, or checksum mismatches SHALL block publication.

#### Scenario: All builds succeed
- **WHEN** all five verified platform archives are available for one version
- **THEN** the release SHALL publish them together with release notes and `SHA256SUMS`

### Requirement: Safe publication retries
An interrupted draft for the same version and merge commit SHALL be resumable. Published releases SHALL remain unchanged, and existing tags SHALL never move to another commit.

#### Scenario: Conflicting version
- **WHEN** a version's existing tag or draft belongs to a different commit
- **THEN** publication SHALL fail without replacing that tag or release

#### Scenario: Retry after upload failure
- **WHEN** publication is rerun for its own unpublished draft and identical merge commit
- **THEN** the complete asset set SHALL be uploaded and verified before the draft becomes public

### Requirement: Version-specific repository release notes
The release body SHALL use the exact Markdown contents of `ReleaseNotes/RELEASE_NOTES_vX.Y.Z.md` from the same merge commit being built. Missing or empty notes SHALL fail before platform builds begin. GitHub-generated notes and files for other versions SHALL NOT be used as fallbacks.

#### Scenario: Matching release notes exist
- **WHEN** the project version is `1.3.0` and `ReleaseNotes/RELEASE_NOTES_v1.3.0.md` is nonempty
- **THEN** a new release or resumed draft SHALL publish that file's contents as its body

#### Scenario: Release notes are missing or empty
- **WHEN** the exact version's release notes file is missing or contains only whitespace
- **THEN** the release workflow SHALL fail during prepare without building or creating a release
