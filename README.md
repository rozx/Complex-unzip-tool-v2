# Complex Unzip Tool v2

A powerful command-line tool designed to extract archives with enhanced detection capabilities, including support for cloaked/disguised files. Features drag-and-drop support when compiled as an executable.

## Features

- **Enhanced Archive Detection**: Detects archives even when disguised with different extensions
- **Cloaked File Support**: Identifies archives hidden as images, documents, or other file types
- **Multiple Archive Formats**: Supports ZIP, RAR, 7Z, TAR, and many other formats via 7-Zip
- **Password Management**: Automatically tries common passwords and supports password files
- **Smart File Grouping**: Groups related archive parts automatically
- **Recursive Processing**: Processes directories and subdirectories by default
- **System File Filtering**: Automatically excludes system files and common non-archive files
- **Drag-and-Drop Support**: Easy-to-use interface when compiled as an EXE
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### For Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Complex-unzip-tool-v2
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   # Windows (PowerShell)
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   
   # macOS/Linux
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**:
   ```bash
   poetry install
   ```

### For End Users

Download the pre-compiled executable from the releases section, or build it yourself using the instructions below.

## Usage

### Command Line Interface

```bash
# Process files/directories (recursive by default)
poetry run python -m complex_unzip_tool_v2.main <path1> <path2> ...

# Show help
poetry run python -m complex_unzip_tool_v2.main --help

# Non-recursive processing
poetry run python -m complex_unzip_tool_v2.main --no-recursive <path>

# Strict archive detection only
poetry run python -m complex_unzip_tool_v2.main --strict <path>
```

### Executable Usage

When using the compiled EXE:

1. **Drag and Drop**: Simply drag files or folders onto the `Complex-Unzip-Tool-v2.exe`
2. **Command Line**: Use the EXE like any other command-line tool
3. **Double Click**: Double-click the EXE to see help and instructions

### Examples

```bash
# Extract all archives in current directory
poetry run python -m complex_unzip_tool_v2.main .

# Process specific files
poetry run python -m complex_unzip_tool_v2.main archive.zip hidden_archive.jpg

# Process multiple directories
poetry run python -m complex_unzip_tool_v2.main dir1/ dir2/ dir3/

# Use strict detection only (faster, but may miss cloaked files)
poetry run python -m complex_unzip_tool_v2.main --strict suspicious_files/
```

## Building Executable

### Current Limitation

**Important**: PyInstaller doesn't support Python 3.13 yet, so executable building is not available in the current environment. 

### For Building EXE Files

To build an executable, you'll need:

1. **Python 3.8 to 3.12** (separate installation)
2. **PyInstaller** compatible environment

### Setup for EXE Building

```bash
# Option 1: Use a separate Python 3.12 environment
# Install Python 3.12 from python.org
# Create a new Poetry project with Python 3.12

# Option 2: Use pyenv (Linux/macOS) or pyenv-win (Windows)
pyenv install 3.12.0
pyenv local 3.12.0
poetry env use python3.12

# Option 3: Use conda
conda create -n complex-unzip python=3.12
conda activate complex-unzip
pip install poetry
poetry install
```

### Build Methods (Once Python 3.12 is available)

#### Method 1: Using Build Batch File (Windows)

```batch
# After setting up Python 3.12 environment
build.bat
```

#### Method 2: Manual Build

```bash
# In Python 3.12 environment
poetry add --group dev pyinstaller
poetry run python build_exe.py
```

### Build Output

The executable will be created in the `dist/` directory:
- `dist/Complex-Unzip-Tool-v2.exe` (Windows)
- File size: ~15-20 MB (includes 7-Zip binaries)

## Password Management

The tool supports automatic password detection:

1. **Default Passwords**: Tries common passwords automatically
2. **Password File**: Place passwords in `passwords.txt` (one per line)
3. **Custom Password File**: Use files named `passwords.txt` in the same directory as archives

Example `passwords.txt`:
```
password
123456
secret
archive_password
```

## Archive Detection

### Strict Mode
- Fast detection based on file extensions and magic numbers
- Reliable for properly named archives

### Enhanced Mode (Default)
- Deep content analysis for cloaked files
- Detects archives disguised as other file types
- Slower but more comprehensive

## File Filtering

The tool automatically excludes:

### System Files
- Windows: `Thumbs.db`, `desktop.ini`, `$RECYCLE.BIN`, etc.
- macOS: `.DS_Store`, `.AppleDouble`, `__MACOSX`, etc.
- Linux: `.Trash-*`, `.directory`, etc.

### Common Non-Archives
- Password files: `passwords.txt`, `password.txt`
- Temporary files and caches
- Hidden system directories

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=complex_unzip_tool_v2

# Run specific test file
poetry run pytest tests/test_archive_extractor.py
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run flake8

# Type checking
poetry run mypy complex_unzip_tool_v2/
```

### Project Structure

```
complex_unzip_tool_v2/
├── __init__.py
├── main.py              # Main CLI interface
├── archive_extractor.py # Archive detection and extraction
├── display_utils.py     # Output formatting and display
├── file_collector.py    # File discovery and filtering
├── file_grouper.py      # Archive part grouping
├── file_renamer.py      # File name handling
├── filename_utils.py    # File name utilities
├── password_manager.py  # Password handling
└── path_validator.py    # Path validation
```

## Troubleshooting

### Common Issues

1. **"7z.exe not found"**: Ensure the `7z/` directory is present with 7-Zip binaries
2. **Permission errors**: Run with administrator privileges if needed
3. **Large files hang**: Use `--strict` mode for faster processing of large directories
4. **Executable won't run**: Ensure all dependencies are bundled correctly

### Debug Mode

Enable verbose output by modifying the logging level in `main.py`:

```python
# Change logging level to DEBUG
logging.basicConfig(level=logging.DEBUG)
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## Changelog

### v2.0.0
- Enhanced archive detection for cloaked files
- Added drag-and-drop EXE support
- Implemented comprehensive system file filtering
- Made recursive processing the default
- Added password management system
- Improved user interface and error handling
