"""Archive extraction functionality."""

import os
import zipfile
import tarfile
import gzip
import bz2
import subprocess
from pathlib import Path
from typing import List, Optional, Callable, Union, Set
import logging

from .password_manager import PasswordManager
from .multipart_detector import MultipartDetector
from .path_validator import PathValidator


logger = logging.getLogger(__name__)


class ArchiveExtractor:
    """Main class for extracting various archive formats."""
    
    SUPPORTED_FORMATS = {
        '.zip', '.jar', '.war', '.ear',  # ZIP-based
        '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2', '.tar.xz',  # TAR-based
        '.gz', '.bz2', '.xz',  # Compressed files
        '.7z', '.rar',  # Requires external tools
    }
    
    def __init__(self, use_7zip: bool = True):
        """Initialize the extractor.
        
        Args:
            use_7zip: Whether to use 7-Zip for extraction when available
        """
        self.use_7zip = use_7zip
        self.multipart_detector = MultipartDetector()
        self.path_validator = PathValidator()
        self._7zip_path = self._find_7zip()
    
    def _find_7zip(self) -> Optional[Path]:
        """Find 7-Zip executable."""
        possible_paths = [
            Path("7z/7z.exe"),  # Local 7z folder
            Path("C:/Program Files/7-Zip/7z.exe"),
            Path("C:/Program Files (x86)/7-Zip/7z.exe"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Try system PATH
        try:
            result = subprocess.run(['7z'], capture_output=True, text=True)
            if result.returncode != 127:  # Command found
                return Path('7z')
        except FileNotFoundError:
            pass
        
        return None
    
    def extract(
        self,
        archive_path: Union[str, Path],
        output_dir: Union[str, Path],
        password_manager: Optional[PasswordManager] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Path]:
        """Extract an archive to the specified directory.
        
        Args:
            archive_path: Path to the archive file
            output_dir: Directory to extract files to
            password_manager: Manager for handling passwords
            progress_callback: Callback for progress updates (current, total)
        
        Returns:
            List of extracted file paths
        
        Raises:
            ValueError: If archive format is not supported
            FileNotFoundError: If archive file doesn't exist
            Exception: For extraction errors
        """
        archive_path = Path(archive_path)
        output_dir = Path(output_dir)
        
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        
        # Check if it's a multipart archive
        if self.multipart_detector.is_multipart(archive_path):
            archive_path = self.multipart_detector.get_first_part(archive_path)
        
        # Validate archive format
        if not self._is_supported_format(archive_path):
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Choose extraction method
        if self.use_7zip and self._7zip_path:
            return self._extract_with_7zip(archive_path, output_dir, password_manager, progress_callback)
        else:
            return self._extract_with_python(archive_path, output_dir, password_manager, progress_callback)
    
    def _is_supported_format(self, archive_path: Path) -> bool:
        """Check if the archive format is supported."""
        suffix = archive_path.suffix.lower()
        
        # Handle compound extensions
        if archive_path.name.endswith(('.tar.gz', '.tar.bz2', '.tar.xz')):
            return True
        
        return suffix in self.SUPPORTED_FORMATS
    
    def _extract_with_7zip(
        self,
        archive_path: Path,
        output_dir: Path,
        password_manager: Optional[PasswordManager],
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract using 7-Zip."""
        logger.info(f"Extracting {archive_path} using 7-Zip")
        
        # Try extraction with different passwords
        passwords = password_manager.get_passwords() if password_manager else ['']
        
        for password in passwords:
            try:
                cmd = [str(self._7zip_path), 'x', str(archive_path), f'-o{output_dir}', '-y']
                if password:
                    cmd.append(f'-p{password}')
                else:
                    cmd.append('-p')  # Empty password
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Extract successful, get list of extracted files
                return self._get_extracted_files(output_dir)
            
            except subprocess.CalledProcessError as e:
                if password == passwords[-1]:  # Last password attempt
                    logger.error(f"7-Zip extraction failed: {e.stderr}")
                    raise Exception(f"Failed to extract with 7-Zip: {e.stderr}")
                continue
        
        return []
    
    def _extract_with_python(
        self,
        archive_path: Path,
        output_dir: Path,
        password_manager: Optional[PasswordManager],
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract using Python built-in libraries."""
        logger.info(f"Extracting {archive_path} using Python libraries")
        
        suffix = archive_path.suffix.lower()
        name_lower = archive_path.name.lower()
        
        if suffix == '.zip' or suffix in ['.jar', '.war', '.ear']:
            return self._extract_zip(archive_path, output_dir, password_manager, progress_callback)
        elif name_lower.endswith(('.tar.gz', '.tgz')):
            return self._extract_tar_gz(archive_path, output_dir, progress_callback)
        elif name_lower.endswith(('.tar.bz2', '.tbz2')):
            return self._extract_tar_bz2(archive_path, output_dir, progress_callback)
        elif suffix == '.tar':
            return self._extract_tar(archive_path, output_dir, progress_callback)
        elif suffix == '.gz':
            return self._extract_gz(archive_path, output_dir, progress_callback)
        elif suffix == '.bz2':
            return self._extract_bz2(archive_path, output_dir, progress_callback)
        else:
            raise ValueError(f"Unsupported format for Python extraction: {suffix}")
    
    def _extract_zip(
        self,
        archive_path: Path,
        output_dir: Path,
        password_manager: Optional[PasswordManager],
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract ZIP file."""
        passwords = password_manager.get_passwords() if password_manager else [None]
        
        for password in passwords:
            try:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    members = zip_ref.infolist()
                    total_files = len(members)
                    extracted_files = []
                    
                    for i, member in enumerate(members):
                        # Validate extraction path
                        if not self.path_validator.is_safe_path(member.filename, output_dir):
                            logger.warning(f"Skipping unsafe path: {member.filename}")
                            continue
                        
                        # Extract member
                        if password:
                            zip_ref.extract(member, output_dir, pwd=password.encode())
                        else:
                            zip_ref.extract(member, output_dir)
                        
                        extracted_path = output_dir / member.filename
                        extracted_files.append(extracted_path)
                        
                        if progress_callback:
                            progress_callback(i + 1, total_files)
                    
                    return extracted_files
            
            except (zipfile.BadZipFile, RuntimeError) as e:
                if password == passwords[-1]:  # Last password attempt
                    raise Exception(f"Failed to extract ZIP: {e}")
                continue
        
        return []
    
    def _extract_tar(
        self,
        archive_path: Path,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract TAR file."""
        with tarfile.open(archive_path, 'r') as tar_ref:
            members = tar_ref.getmembers()
            total_files = len(members)
            extracted_files = []
            
            for i, member in enumerate(members):
                # Validate extraction path
                if not self.path_validator.is_safe_path(member.name, output_dir):
                    logger.warning(f"Skipping unsafe path: {member.name}")
                    continue
                
                tar_ref.extract(member, output_dir)
                extracted_path = output_dir / member.name
                extracted_files.append(extracted_path)
                
                if progress_callback:
                    progress_callback(i + 1, total_files)
            
            return extracted_files
    
    def _extract_tar_gz(
        self,
        archive_path: Path,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract TAR.GZ file."""
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            return self._extract_tar_members(tar_ref, output_dir, progress_callback)
    
    def _extract_tar_bz2(
        self,
        archive_path: Path,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract TAR.BZ2 file."""
        with tarfile.open(archive_path, 'r:bz2') as tar_ref:
            return self._extract_tar_members(tar_ref, output_dir, progress_callback)
    
    def _extract_tar_members(
        self,
        tar_ref: tarfile.TarFile,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract TAR file members."""
        members = tar_ref.getmembers()
        total_files = len(members)
        extracted_files = []
        
        for i, member in enumerate(members):
            if not self.path_validator.is_safe_path(member.name, output_dir):
                logger.warning(f"Skipping unsafe path: {member.name}")
                continue
            
            tar_ref.extract(member, output_dir)
            extracted_path = output_dir / member.name
            extracted_files.append(extracted_path)
            
            if progress_callback:
                progress_callback(i + 1, total_files)
        
        return extracted_files
    
    def _extract_gz(
        self,
        archive_path: Path,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract GZ file."""
        output_file = output_dir / archive_path.stem
        
        with gzip.open(archive_path, 'rb') as gz_file:
            with open(output_file, 'wb') as out_file:
                out_file.write(gz_file.read())
        
        if progress_callback:
            progress_callback(1, 1)
        
        return [output_file]
    
    def _extract_bz2(
        self,
        archive_path: Path,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Path]:
        """Extract BZ2 file."""
        output_file = output_dir / archive_path.stem
        
        with bz2.open(archive_path, 'rb') as bz2_file:
            with open(output_file, 'wb') as out_file:
                out_file.write(bz2_file.read())
        
        if progress_callback:
            progress_callback(1, 1)
        
        return [output_file]
    
    def _get_extracted_files(self, output_dir: Path) -> List[Path]:
        """Get list of extracted files from output directory."""
        extracted_files = []
        
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                extracted_files.append(Path(root) / file)
        
        return extracted_files
