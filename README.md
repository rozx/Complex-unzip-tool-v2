# Complex Unzip Tool v2

A powerful and flexible tool for extracting complex archive files with support for:

- Multiple archive formats (ZIP, RAR, 7Z, TAR, etc.)
- Password-protected archives
- Multipart archives
- Automatic file organization
- Batch processing
- Progress tracking

## Installation

### Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd complex-unzip-tool-v2

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Using pip

```bash
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Extract a single archive
complex-unzip archive.zip

# Extract with password
complex-unzip archive.zip --password mypassword

# Extract multiple archives
complex-unzip *.zip

# Extract with custom output directory
complex-unzip archive.zip --output /path/to/output

# Extract with file organization
complex-unzip archive.zip --organize
```

### Python API

```python
from complex_unzip_tool_v2 import ArchiveExtractor

extractor = ArchiveExtractor()
extractor.extract('archive.zip', output_dir='extracted', password='secret')
```

## Features

- **Multi-format Support**: Handles ZIP, RAR, 7Z, TAR, GZ, BZ2, and more
- **Password Management**: Automatic password detection and custom password lists
- **Multipart Archives**: Seamless handling of split archives
- **File Organization**: Intelligent file sorting and organization
- **Progress Tracking**: Real-time extraction progress with visual indicators
- **Error Handling**: Robust error recovery and detailed logging
- **CLI and API**: Both command-line and programmatic interfaces

## Development

### Setup Development Environment

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black .

# Type checking
poetry run mypy .

# Linting
poetry run flake8 .
```

### Building

```bash
# Build wheel
poetry build

# Build executable (if PyInstaller is configured)
poetry run python build_exe.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.
