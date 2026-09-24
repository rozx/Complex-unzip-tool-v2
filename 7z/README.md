# Bundled 7-Zip

Version **26.03**, released **2026-09-03**. Files are unmodified binaries from the
[official download page](https://www.7-zip.org/download.html) and
[upstream release](https://github.com/ip7z/7zip/releases/tag/26.03).

| Platform | Engine | Required companion |
| --- | --- | --- |
| Windows x64 | `windows-x64/7z.exe` | `windows-x64/7z.dll` |
| macOS Intel / Apple Silicon | `macos/7zz` (universal) | None |
| Linux x64 | `linux-x64/7zzs` (static) | None |
| Linux ARM64 | `linux-arm64/7zzs` (static) | None |

All platform assets live in subdirectories; only this README and `manifest.json`
are stored at the root of `7z/`. Each engine directory contains its upstream
`License.txt`. These notices include
the GNU LGPL, BSD licenses, and unRAR restriction; they must accompany redistributed
engines. Corresponding source is available in `7z2603-src.tar.xz` on the linked
upstream release. Keep executable permissions on the Unix engines.

`manifest.json` records each original download URL, its SHA-256 digest from the
GitHub release API, and SHA-256 digests of the bundled files. To update:

1. Check the official release for all supported platforms.
2. Download the Windows x64 installer and macOS/Linux console tarballs; verify
   their digests against the official release metadata.
3. Extract the Windows installer with 7-Zip (no installation is needed), retaining
   `7z.exe`, `7z.dll`, and `License.txt` in `windows-x64/`. Do not substitute `7za`,
   which supports fewer formats.
4. Copy macOS `7zz` and Linux `7zzs`, each with its own `License.txt`, preserving
   mode bits. Refresh the manifest and version references in the documentation.
5. Run the test suite, native archive smoke checks, and standalone builds on the
   supported platforms. The application never downloads an engine at runtime.
