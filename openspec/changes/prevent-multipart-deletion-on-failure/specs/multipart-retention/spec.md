# Multipart Retention

## ADDED Requirements

### Requirement: Preserve multipart source volumes on extraction failure
When extracting multipart archives, if extraction fails for any reason (missing volumes, bad password, I/O error), the tool MUST NOT delete, recycle, or move away the source multipart files. Only temporary files created by the tool during the current run MAY be cleaned.

#### Scenario: 7z volumes missing continuation
Given: A directory containing `data.7z.001` but missing `data.7z.002`
When: The tool attempts multipart extraction and fails due to missing continuation
Then: `data.7z.001` remains in place (not deleted/recycled), and any tool‑created temp files are cleaned; log states failure and retention of source parts

#### Scenario: RAR multi‑part missing later part
Given: A directory containing `archive.part1.rar` but missing `archive.part2.rar`
When: Extraction fails due to missing part2
Then: `archive.part1.rar` remains; no source parts are deleted; temp cleanup applies only to tool‑created paths; log clarifies retained items

#### Scenario: ZIP spanned set with missing `.z01`
Given: `set.zip` exists but `set.z01` is missing
When: Extraction fails
Then: `set.zip` remains untouched; no source deletions occur; temp dirs may be cleaned; logs indicate retention
