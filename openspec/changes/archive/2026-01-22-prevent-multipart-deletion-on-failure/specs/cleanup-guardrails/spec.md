# Cleanup Guardrails

## ADDED Requirements

### Requirement: Limit deletion to tool‑created temporary paths
Cleanup routines MUST only delete or recycle files and directories known to be created by the tool (e.g., staging/work temp dirs for the current run) during the current run. Source directories and original archive volumes (including multipart group directories) MUST be excluded from cleanup scopes.

#### Scenario: Failure during nested extraction with relocated continuations
Given: Continuation parts were relocated into the group directory during nested extraction
When: A later extraction step fails
Then: Cleanup must not remove relocated continuations or any source volumes; only temp dirs are cleaned; logs distinguish cleaned vs retained items

#### Scenario: Partial output directory exists after failure
Given: A partially extracted output directory was created within a staging location
When: Extraction fails
Then: Only contents under tool‑created temp/staging locations are cleaned; original source archives and group directories remain untouched; logging clarifies cleanup scope
