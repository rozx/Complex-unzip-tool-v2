#!/usr/bin/env python3
"""
Build script for creating standalone executable of Complex Unzip Tool v2
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def generate_spec_content(project_root: Path, scripts_dir: Path) -> str:
    """Generate the PyInstaller spec file content dynamically."""
    
    # Define paths
    main_script = scripts_dir / "standalone_main.py"
    
    # Define data files to include
    data_files = []
    
    # Add 7z binaries if they exist
    seven_zip_files = [
        (project_root / "7z" / "7z.exe", "7z"),
        (project_root / "7z" / "7z.dll", "7z"),
        (project_root / "7z" / "License.txt", "7z"),
    ]
    
    for src_path, dest_dir in seven_zip_files:
        if src_path.exists():
            data_files.append(f'    (r"{src_path}", "{dest_dir}"),')
    
    # Add passwords.txt if it exists
    passwords_file = project_root / "passwords.txt"
    if passwords_file.exists():
        data_files.append(f'    (r"{passwords_file}", "."),')
    
    data_files_str = "\n".join(data_files)
    
    # Check for icon file
    icon_path = project_root / "icons" / "app_icon.ico"
    icon_line = f'r"{icon_path}"' if icon_path.exists() else 'None'
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# This file is generated automatically by the build script

import os

# Project paths
project_root = r"{project_root}"
scripts_dir = r"{scripts_dir}"
main_script = r"{main_script}"

# Data files to include
datas = [
{data_files_str}
]

a = Analysis(
    [main_script],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'complex_unzip_tool_v2',
        'complex_unzip_tool_v2.main',
        'complex_unzip_tool_v2.modules.archive_utils',
        'complex_unzip_tool_v2.modules.file_utils',
        'complex_unzip_tool_v2.modules.password_util',
        'complex_unzip_tool_v2.modules.rich_utils',
        'complex_unzip_tool_v2.modules.const',
        'complex_unzip_tool_v2.modules.utils',
        'complex_unzip_tool_v2.modules.regex',
        'complex_unzip_tool_v2.modules.archive_extension_utils',
        'complex_unzip_tool_v2.classes.ArchiveGroup',
        'complex_unzip_tool_v2.classes.PasswordBook',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='complex-unzip-tool-v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon_line},
)
'''
    return spec_content

def main():
    # Get project root directory (parent of scripts directory)
    project_root = Path(__file__).parent.parent.absolute()
    scripts_dir = Path(__file__).parent.absolute()
    
    # Clean previous builds
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    print("🧹 Cleaning previous builds...")
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # Verify 7z files exist
    seven_zip_exe = project_root / "7z" / "7z.exe"
    seven_zip_dll = project_root / "7z" / "7z.dll"
    
    if not seven_zip_exe.exists():
        print(f"❌ Error: 7z.exe not found at {seven_zip_exe}")
        return 1
    
    if not seven_zip_dll.exists():
        print(f"❌ Error: 7z.dll not found at {seven_zip_dll}")
        return 1
    
    print("✅ 7z binaries found")
    
    # Generate spec file dynamically
    print("📝 Generating PyInstaller spec file...")
    spec_content = generate_spec_content(project_root, scripts_dir)
    spec_file = scripts_dir / "build_standalone_generated.spec"
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ Spec file generated: {spec_file}")
    
    # Run PyInstaller
    print("🔨 Building standalone executable...")
    try:
        result = subprocess.run([
            "poetry", "run", "pyinstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ], cwd=project_root, check=True)
        
        print("✅ Build completed successfully!")
        
        # Check if executable was created
        exe_path = dist_dir / "complex-unzip-tool-v2.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📦 Executable created: {exe_path}")
            print(f"📏 Size: {size_mb:.1f} MB")
            print(f"🎯 You can now distribute this single file!")
        else:
            print("❌ Error: Executable not found in dist folder")
            return 1
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with error code {e.returncode}")
        return 1
    
    finally:
        # Clean up generated spec file
        if spec_file.exists():
            print("🧹 Cleaning up generated spec file...")
            spec_file.unlink()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
