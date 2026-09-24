# Design

## Context

All listing/extraction calls in `archive_utils.py` already share `_resolve_seven_zip_path`. Its default resolver and `scripts/build.py` separately hard-code `7z/7z.exe`. Existing archive commands use argument lists and portable filesystem APIs. Path sanitization operates only on relative fallback output paths, so it does not need replacing for this upgrade.

## Goals / Non-Goals

Goals: share native engine selection between runtime and build, preserve explicit path overrides and extraction APIs, and ship offline executables.

Non-goals: automatic downloading at runtime, arbitrary PATH fallback, 32-bit support, Windows ARM builds, cross-compilation, changing archive grouping/deletion behavior, or a GUI.

## Decisions

- A small runtime module owns OS/architecture selection and bundle-root resolution. Windows x64 retains `7z/7z.exe` plus `7z.dll`; macOS uses the official universal `7z/macos/7zz`; Linux uses the official static `7zzs` in `7z/linux-x64/` or `7z/linux-arm64/`. Recognize x86_64/AMD64 and aarch64/arm64 aliases. Reject unsupported combinations with the existing domain exception.
- Source roots derive from the module location, frozen roots from `sys._MEIPASS`; neither depends on current working directory. Explicit executable file paths still take priority. Require a regular executable file on POSIX and the companion DLL for bundled Windows use.
- CLI validation runs at the entry callback before extraction changes files. Direct extraction APIs keep their existing validation behavior. Help and version do not require the engine. Existing isolated pipeline tests remain independent of native binaries.
- The standalone builder reuses the same mapping, verifies required assets before cleaning old build output, includes native executables/DLLs as PyInstaller binaries, and includes upstream license texts as data. Build through the active Python interpreter. Only Windows uses `.exe` and the `.ico` icon. Build each artifact on its destination OS/architecture.
- Keep the Windows interactive standalone pause only when stdin is a terminal. POSIX standalone invocations and redirected stdin exit normally.
- Preserve upstream files unchanged. Record official URLs, release-asset SHA-256 values, and bundled-file hashes in `7z/` alongside redistribution notices. No installer execution is needed to obtain the Windows EXE/DLL; extract the official installer with the native console engine.

## Risks / Trade-offs

- More binary assets increase checkout size; native builds include only their own engine.
- macOS signing/quarantine policies still apply; distribution signing is outside this change. Validate the local PyInstaller executable.
- Linux desktop trash services vary; retain existing safe deletion behavior and failure handling.
- Windows cannot run natively on the current macOS host; use deterministic platform-selection/build tests and record this limit. Exercise both Linux binaries in Docker when available.

## Plan review

- Verified all archive subprocess paths use the shared resolver; explicit overrides flow through listing, extraction, and nested extraction.
- Verified bundled-root lookup must remain compatible with `_MEIPASS` and must not follow CWD.
- Closed gaps: build currently silently omits missing assets; require all native files and notices before deleting prior artifacts. CLI currently starts rename recovery before engine use; preflight at the callback prevents mutation when the engine is unavailable. Frozen exit currently always reads stdin; restrict the pause to Windows TTYs.
- Existing source retention and output normalization specs remain unchanged.
