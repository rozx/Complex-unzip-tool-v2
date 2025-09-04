import re
from ..modules.regex import multipart_regex, first_part_regex


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
        self.mainArchiveFile = archive

        # if it is a multipart archive
        if re.search(multipart_regex, archive):
            self.isMultiPart = True



    