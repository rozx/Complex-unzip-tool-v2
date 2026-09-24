# Design

## Context

`scripts/build.py` builds a native standalone executable, and the repository has 234 passing tests but no workflows. Versions are duplicated in `pyproject.toml`, the package initializer, and `.bumpversion.cfg`. Tags already use `vX.Y.Z`; the current `1.2.2` tag exists. Source branches such as `release/v1.3` are not necessarily complete semantic versions.

## Goals / Non-Goals

Provide one build pipeline reused by ordinary CI and release publication. Keep extraction logic unchanged. Do not auto-bump versions, derive versions from branch suffixes, sign/notarize binaries, publish packages to registries, or push repository changes during implementation.

## Decisions

- CI runs on PRs and pushes targeting `main` or `release/**`, and can be called by the release workflow. Five explicit hosted runners use Python 3.11: Windows x64 (`windows-2025`), macOS x64 (`macos-15-intel`), macOS ARM64 (`macos-15`), Linux x64 (`ubuntu-24.04`), and Linux ARM64 (`ubuntu-24.04-arm`). Pin official actions to release commit SHAs and install locked dependencies with Poetry.
- Release uses `pull_request_target: closed` on `main`, gated by `merged`, the `release/` head prefix, and the `release` label from that event. It checks out only `merge_commit_sha`, never an unmerged PR head or a moving branch. This supports merged fork PRs too, while the ordinary CI token remains read-only. Only the final publishing job receives `contents: write`; checkout does not persist credentials.
- Validate all three version declarations and accept stable `X.Y.Z` versions. Require the exact version's nonempty UTF-8 notes file during prepare, before platform builds; the publisher reads that file again and applies it both to new releases and resumed drafts. Rename the historical misspelled `RelaseNotes/` directory to `ReleaseNotes/`, preserving file contents. Branch names are a release gate only. Maintainers bump the version in the release PR using the existing bump commands.
- Every matrix job validates bundled-file hashes, runs pytest and source smoke, builds, then runs the same real ZIP/nested/password smoke against the standalone CLI from a temporary working directory. Outputs are Windows ZIP and Unix tar.gz files, preserving executable bits, with project/upstream licenses, README files, and 7-Zip provenance. A sidecar hash accompanies each artifact.
- Publishing downloads only this workflow run's five build artifacts, verifies their exact versioned names and checksums, and writes `SHA256SUMS`. A GitHub draft gets the verbatim body from `ReleaseNotes/RELEASE_NOTES_vX.Y.Z.md` in the merge commit, the exact merged commit as target, and all six public assets. It becomes public only after upload and remote digest verification. A rerun can resume a draft for the same commit. Published releases remain untouched; an existing tag pointing elsewhere or a mismatched draft fails. Publication concurrency is grouped by version without cancelling an active publisher.
- The new workflow must be present on `main` before subsequent eligible merges can trigger the base-branch release workflow. Labels must be applied before merging. No separate tag push or manual event publishes a release.

## Plan review

- Verified native platform mapping and `_MEIPASS` lookup already exist; each build must use a native runner, not pretend the universal 7-Zip binary makes the Python application universal.
- Closed gap: directly uploading Unix executables as Actions artifacts loses executable permissions. Archive them as tar.gz before upload.
- Closed gap: `github.sha` on a target PR event is not the release's immutable identity. Pass `merge_commit_sha` through metadata, every checkout, and publication.
- Closed gap: versions currently describe an already released tag. Keep version bump explicit and reject overwrite instead of guessing a new version.
- Closed gap: whole-project lint/type checks have pre-existing failures. CI gates the passing tests, compilation, real engine checks, builds, and smoke tests; it does not pretend existing lint debt is clean.
- Closed gap: PyInstaller ignores `PYTHONUTF8` from the environment. Bake `X utf8` into the executable so Chinese output remains encodable when Windows CI redirects stdout. The generated build configuration has a regression assertion for this runtime option.

## Risks / Trade-offs

- Five native jobs cost runner time; reuse one pipeline so CI/release checks do not drift.
- Linux standalone compatibility inherits the Ubuntu 24.04 build environment; document that baseline. macOS/Windows outputs remain unsigned.
- Live GitHub event/permissions behavior and unavailable local platforms can only be proven after pushing. Validate workflows with actionlint and exercise helpers locally without publishing.
