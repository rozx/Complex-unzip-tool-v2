# Proposal

## Why

The archive engine and standalone builder hard-code Windows executables. Official 7-Zip now supplies native macOS and Linux console binaries, and the bundled Windows engine needs updating to the current official release.

## What Changes

- Bundle official 7-Zip 26.03 for Windows x64, macOS Intel/Apple Silicon, and Linux x64/ARM64, with licenses and verifiable provenance.
- Select the native bundled engine consistently in source runs and PyInstaller builds, retaining explicit executable-path overrides.
- Build standalone command-line executables on each supported host platform and document their usage.
- Fail clearly before CLI extraction if the bundled engine is missing, not executable, or the platform is unsupported.

## Capabilities

### New Capabilities

- `cross-platform-runtime`: Offline native engine selection, distribution, and standalone builds across supported operating systems.

### Modified Capabilities

None. Existing extraction, password, rename recovery, and source-retention contracts remain unchanged.

## Impact

`archive_utils.py`, a shared runtime helper, CLI startup validation, `scripts/build.py`, bundled `7z/` files, regression tests, and bilingual/project documentation. No new application dependencies or runtime downloads. Windows x64 keeps `7z/7z.exe` and `7z/7z.dll`.
