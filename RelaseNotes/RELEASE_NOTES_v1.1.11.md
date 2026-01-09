# Release Notes v1.1.11

## Bug Fixes
- Prevent accidental deletion of source multipart parts when extraction fails (e.g., missing continuation or incorrect password). Source volumes are retained; only tool‑created temporary folders are cleaned.
- Added explicit logging on failure paths: "Retained source multipart parts due to extraction failure".

## Notes
- Behavior change is conservative and scoped: successful extractions continue to remove originals per user preference; failures retain source parts for safe retry.
