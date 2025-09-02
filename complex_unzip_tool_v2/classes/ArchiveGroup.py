import re
from ..modules.regex import multipartRegex, firstPartRegex


class ArchiveGroup:
    def __init__(self, name: str):
        self.name = name
        self.files = []
        self.mainArchiveFile = ""
        self.isMultiPart = False

    def addFile(self, file: str):
        self.files.append(file)
        # if it is a multipart archive
        if re.search(multipartRegex, file):
            self.isMultiPart = True

        # check if the archive is the first part of the multipart
        if re.search(firstPartRegex, file) or not self.mainArchiveFile:
            self.setMainArchive(file)

    def setMainArchive(self, archive: str):
        self.mainArchiveFile = archive

        # if it is a multipart archive
        if re.search(multipartRegex, archive):
            self.isMultiPart = True



    