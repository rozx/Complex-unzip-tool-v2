import re

from complex_unzip_tool_v2.modules.regex import multipart_regex, first_part_regex


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
        # Set the archive as main - validation will happen during extraction
        self.mainArchiveFile = archive
        if re.search(multipart_regex, archive):
            self.isMultiPart = True

    def get_alternative_main_archives(self) -> list[str]:
        """
        Get list of alternative files in the group that could be the main archive.
        This is used when the default main archive fails extraction.
        Returns files in priority order (first part files first, then others).
        """
        alternatives = []

        # First, try to find files that match first part patterns
        first_part_files = []
        other_files = []

        for file_path in self.files:
            if file_path != self.mainArchiveFile:  # Skip current main archive
                if re.search(first_part_regex, file_path):
                    first_part_files.append(file_path)
                else:
                    other_files.append(file_path)

        # Return first part files first, then other files
        alternatives.extend(first_part_files)
        alternatives.extend(other_files)

        return alternatives

    def try_set_alternative_main_archive(self) -> bool:
        """
        Try to set an alternative file as the main archive.
        Only considers files that actually exist.
        Returns True if an alternative was found and set, False otherwise.
        """
        import os

        alternatives = self.get_alternative_main_archives()
        for alternative in alternatives:
            if os.path.exists(alternative):
                # Found an existing alternative, set it as main
                self.set_main_archive(alternative)
                return True

        # No existing alternatives found
        return False
