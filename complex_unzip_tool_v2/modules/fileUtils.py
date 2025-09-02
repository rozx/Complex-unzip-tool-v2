import os
import re
import struct
from ..classes.ArchiveGroup import ArchiveGroup
from .utils import string_similarity


def readDir(file_paths: list[str]) -> list[str]:
    """ Read directory contents """
    result = []
    for path in file_paths:
        if os.path.isdir(path):
            # Read files from directory
            for root, dirs, files in os.walk(path):
                for filename in files:
                    result.append(os.path.join(root, filename))
        else:
            result.append(path)

    # make sure the result is unique
    return list(set(result))

def renameFile(old_path: str, new_path: str) -> None:
    """
    Rename a file or directory
    For example, "old_name.txt" to "new_name.txt"
    """
    try:
        os.rename(old_path, new_path)
    except Exception as e:
        print(f"Error renaming file {old_path} to {new_path}: {e}")

def createGroupsByName(file_paths: list[str]) -> list[ArchiveGroup]:
    """ Create Archive Groups by name """
    groups: list[ArchiveGroup] = []
    for path in file_paths:
        # get base name and directory name

        base_name = os.path.basename(path)
        name, ext = os.path.splitext(base_name)
        dir_name = os.path.dirname(path).split(os.path.sep)[-1]
        group_name = f"{dir_name}-{name}"

        # Check basename's similarity to a group, it is greater than 0.8 then add it to the group, if not then create a existing group
        found_group = False
        for group in groups:
            # if group's name is similar to the file's base name and it is in the same directory
            if string_similarity(group_name, group.name) >= 0.8:
                group.addFile(path)
                found_group = True
                break
                

        if not found_group:
            new_group = ArchiveGroup(group_name)
            new_group.addFile(path)
            groups.append(new_group)

    # and finally sort it by name
    for group in groups:
        group.files.sort()

    return groups



