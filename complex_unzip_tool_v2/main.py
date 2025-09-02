"""Main CLI interface for Complex Unzip Tool v2."""

from ctypes import cast
import os
import shutil
import sys
import typer
from pathlib import Path
from typing import List, Optional, Annotated

from .modules import passwordUtil
from .modules import fileUtils
from .modules import archiveExtensionUtils
from .modules import archiveUtils
from .modules import const

app = typer.Typer(help="Complex Unzip Tool v2 - Advanced Archive Extraction Utility")

@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    paths: Annotated[Optional[List[str]], typer.Argument(help="Archive paths to extract")] = None,
    version: bool = typer.Option(False, "--version", "-v", help="Show version information")
) -> None:
    """Complex Unzip Tool v2 - Advanced Archive Extraction Utility."""
    if version:
        from . import __version__
        typer.echo(f"Complex Unzip Tool v2 {__version__}")
        raise typer.Exit()
    
    # If no command is provided, run the default extract command
    if ctx.invoked_subcommand is None:
        if paths:
            # Call extract_files directly instead of extract command
            extract_files(paths)
        else:
            # Show help when no paths are provided
            typer.echo(ctx.get_help())
            raise typer.Exit(0)

@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    typer.echo(f"Complex Unzip Tool v2 {__version__}")

def extract(paths: Annotated[List[str], typer.Argument(help="Paths to the archives to extract")]) -> None:
    """Extract files from an archive."""
    extract_files(paths)

def extract_files(paths: List[str]) -> None:
    """Shared extraction logic."""

    # get output folder, it should at the first path
    if(os.path.isdir(paths[0])):
        output_folder = os.path.join(paths[0], const.OUTPUT_FOLDER)
    else:
        output_folder = os.path.join(os.path.dirname(paths[0]), const.OUTPUT_FOLDER)
    os.makedirs(output_folder, exist_ok=True)

    passwordBook = passwordUtil.loadAllPasswords(paths)
    user_provided_passwords = []


    typer.echo(f"Loaded {len(passwordBook.getPasswords())} unique passwords.")

    typer.echo(f"Extracting files from: {paths}")
    contents = fileUtils.readDir(paths)

    typer.echo(f"Found {len(contents)} files.")

    # Create archive groups
    groups = fileUtils.createGroupsByName(contents)

    typer.echo(f"Created {len(groups)} archive groups.")

    typer.echo("Processing archive groups...")

    # Rename archive files to have the correct extensions
    typer.echo("Uncloaking file extensions...")
    fileUtils.uncloakFileExtensionForGroups(groups)

    for group in groups:
        typer.echo(f"Group: {group.name}")
        for item in group.files:
            typer.echo(f" - {item}")

        if group.mainArchiveFile:
            typer.echo(f"   (Main archive: {group.mainArchiveFile})")

    # Processing single archives first to find out containers for multi-part archives
    typer.echo(f"Processing single archive to extract containers...")

    for group in groups.copy():
        if not group.isMultiPart:
            typer.echo(f"Extracting single archive: {group.name}")

            dir = os.path.dirname(group.mainArchiveFile)
            extractionTempPath = os.path.join(dir, f'temp.{group.name}')
            typer.echo(f"Extraction temp path: {extractionTempPath}")

            try:
                result = archiveUtils.extractNestedArchives(
                    archive_path=group.mainArchiveFile,
                    output_path=extractionTempPath,
                    password_list=passwordBook.getPasswords(),
                    max_depth=10,
                    cleanup_archives=True
                )

                # Check if extraction was successful and result contains expected data
                if result and result.get("success", False):

                    # add user provided passwords
                    user_provided_passwords.extend(result.get("user_provided_passwords", []))

                    # Successfully extracted nested archives
                    final_files_raw = result.get("final_files", [])
                    
                    # Type guard to ensure we have a list
                    if isinstance(final_files_raw, list):
                        final_files = final_files_raw.copy()  # Make a copy to safely modify
                        
                        typer.echo(f"Successfully extracted {group.name}")
                        typer.echo("Checking extracted files...")

                        # Process each extracted file
                        files_to_remove = []
                        for file_path in final_files:
                            if os.path.exists(file_path):
                                if fileUtils.addFileToGroups(file_path, groups):
                                    typer.echo(f" - {os.path.basename(file_path)} is part of multi-part archive, moved to the location of group")
                                    files_to_remove.append(file_path)
                            else:
                                typer.echo(f" - Warning: File not found: {file_path}")
                                files_to_remove.append(file_path)
                        
                        # Remove processed files from the list
                        for file_path in files_to_remove:
                            final_files.remove(file_path)

                        # Move remaining files to output folder
                        if final_files:
                            typer.echo(f"Moving {len(final_files)} remaining files to output folder...")
                            moved_files = fileUtils.moveFilesPreservingStructure(
                                final_files, 
                                extractionTempPath, 
                                output_folder
                            )
                            typer.echo(f"Moved {len(moved_files)} remaining files to: {output_folder}")
                        
                        # Remove the original archive file
                        try:
                            if os.path.exists(group.mainArchiveFile):
                                os.remove(group.mainArchiveFile)
                                typer.echo(f"Removed original archive: {os.path.basename(group.mainArchiveFile)}")
                        except Exception as e:
                            typer.echo(f"Warning: Could not remove original archive {group.mainArchiveFile}: {e}")

                        # Remove the temporary extraction folder
                        try:
                            if os.path.exists(extractionTempPath):
                                shutil.rmtree(extractionTempPath)
                                typer.echo(f"Cleaned up temporary folder: {extractionTempPath}")
                        except Exception as e:
                            typer.echo(f"Warning: Could not remove temp folder {extractionTempPath}: {e}")

                        # Remove the group from processing
                        groups.remove(group)
                        
                    else:
                        typer.echo(f"Error: Expected list of files for {group.name}, got {type(final_files_raw)}")
                        groups.remove(group)
                
                else:
                    typer.echo(f"Failed to extract {group.name}")
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                    groups.remove(group)
                    
            except Exception as e:
                typer.echo(f"Error processing {group.name}: {e}")
                # Clean up temp folder if it exists
                try:
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                except:
                    pass
                finally:
                    groups.remove(group)
                continue

    # add user provided passwords to password book
    passwordBook.addPasswords(user_provided_passwords)


    # Then handle multipart archives
    for group in groups.copy():
        if group.isMultiPart:
            typer.echo(f"Handling multipart archive: {group.name}")

            dir = os.path.dirname(group.mainArchiveFile)
            extractionTempPath = os.path.join(dir, f'temp.{group.name}')

            try:
                result = archiveUtils.extractNestedArchives(
                    archive_path=group.mainArchiveFile,
                    output_path=extractionTempPath,
                    password_list=passwordBook.getPasswords(),
                    max_depth=10,
                    cleanup_archives=True
                )

                if result and result.get("success", False):

                    # add user provided passwords
                    user_provided_passwords.extend(result.get("user_provided_passwords", []))

                    # Successfully extracted nested archives
                    final_files_raw = result.get("final_files", [])

                    # Type guard to ensure we have a list
                    if isinstance(final_files_raw, list):
                        typer.echo(f"Successfully extracted {group.name}")

                        final_files = final_files_raw.copy()  # Make a copy to safely modify

                        # Move files to output folder
                        if final_files:
                            typer.echo(f"Moving {len(final_files)} files to output folder...")
                            moved_files = fileUtils.moveFilesPreservingStructure(
                                final_files, 
                                extractionTempPath, 
                                output_folder
                            )
                            typer.echo(f"Moved {len(moved_files)} files to: {output_folder}")

                            # Remove the original archive file
                            try:
                                for archive_file in group.files:
                                    if os.path.exists(archive_file):
                                        os.remove(archive_file)
                                        typer.echo(f"Removed original archive: {os.path.basename(archive_file)}")
                            except Exception as e:
                                typer.echo(f"Warning: Could not remove original archive {group.mainArchiveFile}: {e}")

                            # Remove the temporary extraction folder
                            try:
                                if os.path.exists(extractionTempPath):
                                    shutil.rmtree(extractionTempPath)
                                    typer.echo(f"Cleaned up temporary folder: {extractionTempPath}")
                            except Exception as e:
                                typer.echo(f"Warning: Could not remove temp folder {extractionTempPath}: {e}")

                            # Remove the group from processing
                            groups.remove(group)

                    else:
                        typer.echo(f"Error: Expected list of files for {group.name}, got {type(final_files_raw)}")
                        groups.remove(group)
                else:
                    typer.echo(f"Failed to extract {group.name}")
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                    groups.remove(group)


            except Exception as e:
                typer.echo(f"Error processing {group.name}: {e}")
                # Clean up temp folder if it exists
                try:
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                except:
                    pass
                finally:
                    groups.remove(group)
                continue

    
    # add user provided password to password book
    passwordBook.addPasswords(user_provided_passwords)

    # Show remaining unable to process files
    if groups:
        typer.echo("Remaining groups unable to process:")
        for group in groups:
            typer.echo(f" - {group.name}")

    # save user provided passwords
    passwordBook.savePasswords()


def cli() -> None:
    """Command line interface entry point."""
    app()


def main() -> None:
    """Entry point for the application."""
    try:
        cli()
    except KeyboardInterrupt:
        typer.echo("\n✗ Operation cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        typer.echo(f"✗ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

