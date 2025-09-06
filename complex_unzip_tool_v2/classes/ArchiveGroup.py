import re

from complex_unzip_tool_v2.modules.regex import multipart_regex, first_part_regex
from complex_unzip_tool_v2.modules.archive_extension_utils import (
    detect_archive_extension,
)


class ArchiveGroup:
    def __init__(self, name: str):
        self.name = name
        self.files = []
        self.mainArchiveFile = ""
        self.isMultiPart = False

    def add_file(self, file: str):
        self.files.append(file)
        # if it is a multipart archive
        if re.search(multipart_regex, file):
            self.isMultiPart = True

        # check if the archive is the first part of the multipart
        # prioritize first part over any existing main archive
        if re.search(first_part_regex, file):
            self.set_main_archive(file)
        elif not self.mainArchiveFile:
            # only set as main archive if no main archive is set yet
            self.set_main_archive(file)

    def set_main_archive(self, archive: str):
        # Verify the archive has a valid signature before setting as main
        detected_type = detect_archive_extension(archive)
        if not detected_type:
            # Look for other files in the group with valid signatures
            valid_archive = self._find_valid_archive_in_group()
            if valid_archive:
                self.mainArchiveFile = valid_archive
                if re.search(multipart_regex, valid_archive):
                    self.isMultiPart = True
                return
            else:
                # No valid archive found in the group - throw error
                raise ValueError(
                    f"No valid archive signature found in group '{self.name}'. "
                    f"Attempted main archive '{archive}' has no recognizable archive signature, "
                    f"and no other files in the group have valid signatures."
                )

        # Archive has valid signature - set as main
        self.mainArchiveFile = archive
        if re.search(multipart_regex, archive):
            self.isMultiPart = True

    def _find_valid_archive_in_group(self) -> str:
        """
        Look for a file in the current group that has a valid archive signature.
        Returns the first valid archive found, or empty string if none found.
        """
        for file_path in self.files:
            if detect_archive_extension(file_path):
                return file_path
        return ""
