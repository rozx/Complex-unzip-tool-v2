## Why

Zip-based documents and packages were kept by file extension alone. A plain zip renamed to a document extension, such as `资源.zip.docx` or `game.apk`, is a common way to disguise an archive on cloud drives. It was therefore kept unextracted, and nothing in the cloaked-file rules renames single fake extensions like these.

## What Changes

- A zip whose extension is a known document or package format is kept only if it also contains that format's required root entry:
  - `[Content_Types].xml` for Office Open XML, XPS, 3MF, APPX/MSIX, VSIX and NuGet
  - `mimetype` for OpenDocument (`mimetype` or `META-INF` for EPUB)
  - `META-INF` or `WEB-INF` for Java archives
  - `AndroidManifest.xml` for APK/AAR
  - `Payload` for IPA
  - `Index`, `Index.zip` or `index.xml` for Apple iWork
  - `*.dist-info` for wheels
  - `*.kml` for KMZ
  - `manifest.json` or `install.rdf` for browser extensions
  - `BundleConfig.pb`, `manifest.json` and `toc.pb` for AAB, XAPK and APKS
- The check uses the entry list that `7z l -slt` already returns, so no extra 7-Zip call is needed. Backslash-separated (Windows) paths and letter case are normalized.
- A zip without the marker is treated as a disguised archive and extracted.

## Impact

- Code: `modules/archive_utils.py` (`_ZIP_DOCUMENT_MARKERS`, `_is_zip_document`, `is_valid_archive`).
- Behavior: disguised archives named like documents are extracted again. A malformed real document that lacks its marker is extracted too, which is the pre-1.3.1 behavior; it remains recoverable because nested cleanup uses the Recycle Bin by default.
