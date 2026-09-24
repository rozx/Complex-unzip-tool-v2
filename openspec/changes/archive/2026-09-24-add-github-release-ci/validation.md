# Validation — 2026-09-24

## Release notes follow-up

- Release notes now come verbatim from `ReleaseNotes/RELEASE_NOTES_vX.Y.Z.md` in the merge commit. Prepare rejects missing or empty files before the build matrix starts; the publisher enforces the same requirement for new drafts and retries, with no generated-note fallback.
- Renamed `RelaseNotes/` to `ReleaseNotes/`; SHA-256 comparison verified all seven historical files remained byte-identical.
- Regression tests first failed for the missing notes reader and GitHub-generated/missing draft bodies. After implementation, both macOS and Linux ARM64 passed the full **256-test** suite; actionlint, JavaScript syntax, focused formatting/lint/type checks, and strict spec validation passed.

## Original CI validation

- `actionlint .github/workflows/ci.yml .github/workflows/release.yml`: passed.
- `pytest -q`: **251 passed** on macOS ARM64 and a Linux ARM64 container.
- New release helper tests were written before implementation and failed for the missing module, then passed. Seven mocked GitHub API cases failed before the publisher existed, then passed: new release, draft retry, conflicting tag, conflicting draft, published release, upload failure, and remote digest mismatch.
- The generated standalone spec initially failed four assertions for its missing UTF-8 runtime option; adding the documented PyInstaller option made them pass.
- Evaluated the actual release job condition with synthetic merged/labeled, wrong-source, wrong-base, unmerged, and missing-label payloads: all five behaved as intended. Actual GitHub event delivery remains untested until the workflow is on `main`.
- Black, flake8, and mypy checks for the new Python helpers/tests passed. JavaScript syntax checking and `git diff --check` passed. Existing unrelated whole-project lint/type debt is unchanged in scope.
- Real source and frozen CLI smoke passed on macOS ARM64 and Linux ARM64: help/version with redirected stdin, Chinese filenames, nested ZIPs, encrypted 7z with a Unicode password, wrong-password rejection, split-volume 7z, byte-identical outputs, and successful source cleanup within temporary fixtures.
- Both native standalone builds and release packaging completed. Unix archive tests verified executable mode preservation; package tests verified license/doc inclusion and SHA-256 sidecars. Complete-asset validation tests rejected missing, modified, and extra files before publishing.
- Linux used a writable copy in a disposable container and installed the native PyInstaller 6.15.0 wheel; it did not modify the mounted source checkout. macOS frozen execution required leaving the Codex sandbox because PyInstaller uses a system semaphore blocked there.
- Windows x64, Intel macOS, and Linux x64 native Actions builds are configured but were not run on GitHub. Windows/Intel/Linux target selection has existing deterministic coverage. No live release/tag/API mutation, push, or version bump was performed.

## Release behavior and prerequisites

The trigger is `pull_request_target: closed` targeting `main`, guarded by merged state, the `release/` source prefix, and the `release` label. All build checkouts and publication target the payload's exact merge SHA. The workflow needs to exist on `main` before eligible future merges. An existing version tag at another commit fails before the five builds begin. The repository currently declares the already released `1.2.2`, so a release PR must bump the three version declarations before merging.

Only the publication job gets `contents: write`. It verifies all five archives, stages a draft, verifies remote asset digests, and then publishes. Published releases are left unchanged; rerunning an already published version stops with a clear error. Matching drafts can be resumed.

## Authoritative references checked

- [GitHub workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target)
- [Hosted runner labels](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
- [Release API and latest-version semantics](https://docs.github.com/en/rest/releases/releases)
- [Release asset digests](https://docs.github.com/en/rest/releases/assets)
- [PyInstaller interpreter options](https://pyinstaller.org/en/stable/spec-files.html#specifying-python-interpreter-options)

Official action release tags and commit SHAs were resolved through the GitHub API: checkout v7.0.1, setup-python v7.0.0, upload-artifact v7.0.1, download-artifact v8.0.1, and github-script v9.0.0. Workflow pins use the resolved commit SHAs.
