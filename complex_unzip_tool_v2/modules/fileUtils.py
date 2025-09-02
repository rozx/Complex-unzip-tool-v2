import os
import re
import shutil
import struct
import typer

from click import group


from ..classes.ArchiveGroup import ArchiveGroup
from .utils import getStringSimilarity
from .archiveExtensionUtils import detectArchiveExtension


def getArchiveBaseName(file_path: str) -> tuple[str, str]:
    """
    Get the base name and archive extension from a file path,
    handling multi-part archives like .7z.001, .rar.part1, etc.
    Returns (base_name, archive_extension)
    """
    base_name = os.path.basename(file_path)
    
    # Common multi-part archive patterns
    multi_part_patterns = [
        r'\.7z\.\d+$',           # .7z.001, .7z.002, etc.
        r'\.rar\.part\d+$',      # .rar.part1, .rar.part2, etc.
        r'\.zip\.\d+$',          # .zip.001, .zip.002, etc.
        r'\.tar\.gz\.\d+$',      # .tar.gz.001, etc.
        r'\.tar\.bz2\.\d+$',     # .tar.bz2.001, etc.
        r'\.tar\.xz\.\d+$',      # .tar.xz.001, etc.
        r'\.\w+\.part\d+$',      # generic .ext.part1 format
    ]
    
    for pattern in multi_part_patterns:
        match = re.search(pattern, base_name, re.IGNORECASE)
        if match:
            # Remove the part number/suffix to get the base name
            name_without_part = base_name[:match.start()]
            archive_ext = base_name[match.start()+1:].split('.')[0]  # Get the archive extension
            return name_without_part, archive_ext
    
    # Fallback to regular splitext if no multi-part pattern found
    name, ext = os.path.splitext(base_name)
    return name, ext.lstrip('.')

def readDir(file_paths: list[str]) -> list[str]:
    """ Read directory contents """
    result = []

    # ignore system files and passwords.txt
    ignored_files = {".DS_Store", "thumbs.db", "desktop.ini", "passwords.txt"}

    for path in file_paths:
        if os.path.isdir(path):
            # Read files from directory
            for root, dirs, files in os.walk(path):
                for filename in files:
                    result.append(os.path.join(root, filename))
        else:
            # Check if the file is ignored
            if os.path.basename(path) not in ignored_files:
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
        # get base name and directory name using the new function
        name, ext = getArchiveBaseName(path)
        dir_name = os.path.dirname(path).split(os.path.sep)[-1]
        group_name = f"{dir_name}-{name}"

        # Check basename's similarity to a group, it is greater than 0.8 then add it to the group, if not then create a existing group
        found_group = False
        for group in groups:
            # if group's name is similar to the file's base name and it is in the same directory
            if getStringSimilarity(group_name, group.name) >= 0.8:
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

def uncloakFileExtensionForGroups(groups: list[ArchiveGroup]) -> None:
    """ Uncloak file extensions for groups """
    
    for group in groups:
        for i, file in enumerate(group.files):
            true_ext = detectArchiveExtension(file)
            if true_ext:
                # rename the file to have the true extension
                name, current_ext = getArchiveBaseName(file)
                new_name = f"{name}.{true_ext}"
                new_path = os.path.join(os.path.dirname(file), new_name)

                if new_path != file:
                    renameFile(file, new_path)
                    group.files[i] = new_path
                    if group.mainArchiveFile == file:
                        group.mainArchiveFile = new_path

def addFileToGroups(file: str, groups: list[ArchiveGroup]) -> ArchiveGroup | None:
    """
    Check if a file belongs to a specific multi-part archive group, then add it to the group.
    """

    fileBaseName = os.path.basename(file)

    for group in groups:
        if group.isMultiPart:

            mainArchiveBaseName = os.path.basename(group.mainArchiveFile)

            if getStringSimilarity(fileBaseName, mainArchiveBaseName) >= 0.8:
                # move file to group's main archive's location
                new_path = os.path.join(os.path.dirname(group.mainArchiveFile), fileBaseName)
                shutil.move(file, new_path)
                group.addFile(new_path)
                return group

    return None


def moveFilesPreservingStructure(
    file_paths: list[str], 
    source_root: str, 
    destination_root: str,
    verbose: bool = False
) -> list[str]:
    """
    Move files from source to destination while preserving directory structure.
    
    Args:
        file_paths: List of file paths to move
        source_root: Root directory to calculate relative paths from
        destination_root: Root directory to move files to
    
    Returns:
        List of relative paths that were successfully moved
    """
    moved_files = []
    
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                # Calculate relative path from source root to preserve structure
                relative_path = os.path.relpath(file_path, source_root)
                destination = os.path.join(destination_root, relative_path)
                
                # Create destination directory if it doesn't exist
                destination_dir = os.path.dirname(destination)
                os.makedirs(destination_dir, exist_ok=True)
                
                # Handle duplicate filenames while preserving directory structure
                counter = 1
                original_destination = destination
                while os.path.exists(destination):
                    name, ext = os.path.splitext(original_destination)
                    destination = f"{name}_{counter}{ext}"
                    counter += 1
                
                shutil.move(file_path, destination)
                moved_files.append(relative_path)
                if verbose: typer.echo(f" - Moved: {relative_path}")
                
            except Exception as e:
                typer.echo(f" - Error moving {file_path}: {e}")
    
    return moved_files
