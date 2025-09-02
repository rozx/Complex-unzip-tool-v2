"""Main CLI interface for Complex Unzip Tool v2."""

import os
import sys
import typer
from pathlib import Path
from typing import List, Optional, Annotated

from .modules import passwordUtil
from .modules import fileUtils
from .modules import archiveExtensionUtils
from .modules import archiveUtils

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

    passwordBook = passwordUtil.loadAllPasswords(paths)
    passwords = passwordBook.getPasswords()

    typer.echo(f"Loaded {len(passwords)} unique passwords.")

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

        for container in group.containers:
            typer.echo(f"   (Container: {container})")


    # Processing single archives first to find out containers for multi-part archives

    typer.echo(f"Processing single archive to extract containers...")

    for group in groups:
        if not group.isMultiPart:
            typer.echo(f"Extracting single archive: {group.name}")




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

