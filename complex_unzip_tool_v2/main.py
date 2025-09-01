"""Main CLI interface for Complex Unzip Tool v2."""

import sys
import typer
from pathlib import Path
from typing import List, Optional

app = typer.Typer(help="Complex Unzip Tool v2 - Advanced Archive Extraction Utility")

@app.command()
def version() -> None:
    """Show version information."""
    from . import __version__
    typer.echo(f"Complex Unzip Tool v2 {__version__}")


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

