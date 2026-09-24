# Proposal

## Why

The new native platforms are only verified locally. Maintainers need automatic tests, native standalone builds, and a complete GitHub release when a labeled release PR merges.

## What Changes

- Add reusable CI for Windows x64, macOS x64/ARM64, and Linux x64/ARM64, with tests, real archive smoke checks, standalone builds, and downloadable archives.
- Publish only after a `release/*` PR with the `release` label merges into `main`.
- Derive a `vX.Y.Z` tag from the consistent project version, bind all artifacts to the merge commit, and publish only when all five builds succeed.
- Read release bodies from the matching `ReleaseNotes/RELEASE_NOTES_vX.Y.Z.md` in the merge commit, requiring a nonempty file.
- Include licenses and checksums; resume an interrupted draft without changing published releases or moving existing tags.

## Capabilities

### New Capabilities

- `github-release-ci`: Automated multi-platform validation and merge-triggered GitHub release publication.

### Modified Capabilities

None. Native runtime behavior remains governed by `cross-platform-runtime`.

## Impact

GitHub Actions workflows, small release/package and smoke helpers under `scripts/`, regression tests, and bilingual contributor documentation. No application dependency changes or release version bump. Workflows become active after being pushed; no live release is created during implementation.
