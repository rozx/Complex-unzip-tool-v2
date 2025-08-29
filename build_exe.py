#!/usr/bin/env python3
"""
Build script for Complex Unzip Tool v2
Creates a standalone executable with PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def build_exe():
    """Build the executable using PyInstaller"""
    
    # Check Python version compatibility
    import sys
    if sys.version_info >= (3, 13):
        print("WARNING: PyInstaller doesn't support Python 3.13 yet.")
        print("Please use Python 3.8-3.12 for building the executable.")
        print("You can install Python 3.12 and configure Poetry to use it:")
        print("  poetry env use python3.12")
        return False
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    # Paths
    main_script = project_root / "complex_unzip_tool_v2" / "main.py"
    sevenz_dir = project_root / "7z"
    icon_path = None  # You can add an icon file if desired
    
    # Output directory
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    print("Building Complex Unzip Tool v2 executable...")
    print(f"Project root: {project_root}")
    print(f"Main script: {main_script}")
    print(f"7z directory: {sevenz_dir}")
    
    # Check if main script exists
    if not main_script.exists():
        print(f"Error: Main script not found at {main_script}")
        return False
    
    # Check if 7z directory exists
    if not sevenz_dir.exists():
        print(f"Error: 7z directory not found at {sevenz_dir}")
        return False
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--onefile",  # Create a single executable file
        "--clean",    # Clean PyInstaller cache
        "--noconfirm",  # Replace output directory without asking
        f"--name=Complex-Unzip-Tool-v2",  # Name of the executable
        f"--distpath={dist_dir}",  # Output directory
        f"--workpath={build_dir}",  # Build directory
        f"--add-data={sevenz_dir};7z",  # Include 7z directory
        "--console",  # Console application (not windowed)
        str(main_script)
    ]
    
    # Add icon if available
    if icon_path and Path(icon_path).exists():
        cmd.extend([f"--icon={icon_path}"])
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(result.stdout)
        
        # Check if executable was created
        exe_path = dist_dir / "Complex-Unzip-Tool-v2.exe"
        if exe_path.exists():
            print(f"Executable created: {exe_path}")
            print(f"Size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
            return True
        else:
            print("Error: Executable not found after build")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def clean_build():
    """Clean build artifacts"""
    project_root = Path(__file__).parent
    
    # Directories to clean
    clean_dirs = [
        project_root / "build",
        project_root / "dist",
        project_root / "__pycache__",
        project_root / "complex_unzip_tool_v2" / "__pycache__",
    ]
    
    # Files to clean
    clean_files = [
        project_root / "Complex-Unzip-Tool-v2.spec",
    ]
    
    print("Cleaning build artifacts...")
    
    for dir_path in clean_dirs:
        if dir_path.exists():
            print(f"Removing directory: {dir_path}")
            shutil.rmtree(dir_path)
    
    for file_path in clean_files:
        if file_path.exists():
            print(f"Removing file: {file_path}")
            file_path.unlink()
    
    print("Clean complete.")


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_build()
    else:
        # Clean first, then build
        clean_build()
        success = build_exe()
        
        if success:
            print("\n" + "="*50)
            print("BUILD SUCCESSFUL!")
            print("="*50)
            print("Your executable is ready in the 'dist' directory.")
            print("You can now distribute Complex-Unzip-Tool-v2.exe")
            print("Users can drag and drop files/folders onto the EXE.")
        else:
            print("\n" + "="*50)
            print("BUILD FAILED!")
            print("="*50)
            sys.exit(1)


if __name__ == "__main__":
    main()
