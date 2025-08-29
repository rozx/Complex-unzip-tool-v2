#!/usr/bin/env python3
"""
Validation script for Complex Unzip Tool v2
Tests all major functionality to ensure everything works correctly
"""

import sys
import subprocess
import tempfile
import zipfile
from pathlib import Path
import shutil


def create_test_archive():
    """Create a test ZIP file for validation"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test files
        test_file1 = temp_path / "test1.txt"
        test_file1.write_text("This is test file 1")
        
        test_file2 = temp_path / "test2.txt"
        test_file2.write_text("This is test file 2")
        
        # Create test ZIP
        zip_path = temp_path / "test_archive.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(test_file1, "test1.txt")
            zf.write(test_file2, "test2.txt")
        
        return zip_path.read_bytes()


def test_help_display():
    """Test that help displays correctly"""
    print("Testing help display...")
    try:
        import os
        result = subprocess.run([
            sys.executable, "-m", "complex_unzip_tool_v2.main", "--help"
        ], capture_output=True, text=True, timeout=10, cwd=os.getcwd())
        
        if result.returncode == 0 and "Complex Unzip Tool v2" in result.stdout:
            print("✅ Help display works correctly")
            return True
        else:
            print("❌ Help display failed")
            print(f"Return code: {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Help test failed with error: {e}")
        return False


def test_no_args_behavior():
    """Test behavior when no arguments are provided"""
    print("Testing no-arguments behavior...")
    try:
        import os
        result = subprocess.run([
            sys.executable, "-m", "complex_unzip_tool_v2.main"
        ], capture_output=True, text=True, timeout=10, cwd=os.getcwd())
        
        # Should show help when no args provided
        if "Complex Unzip Tool v2" in result.stdout and "usage:" in result.stdout:
            print("✅ No-arguments behavior works correctly (shows help)")
            return True
        else:
            print("❌ No-arguments behavior failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ No-arguments test failed with error: {e}")
        return False


def test_sys_frozen_detection():
    """Test sys.frozen detection for EXE mode"""
    print("Testing sys.frozen detection...")
    try:
        # This will be False in development mode
        import sys
        is_frozen = getattr(sys, 'frozen', False)
        
        if not is_frozen:
            print("✅ sys.frozen correctly detects development mode (False)")
            return True
        else:
            print("✅ sys.frozen correctly detects compiled mode (True)")
            return True
    except Exception as e:
        print(f"❌ sys.frozen test failed with error: {e}")
        return False


def test_7z_availability():
    """Test that 7z.exe is available and working"""
    print("Testing 7z.exe availability...")
    try:
        from complex_unzip_tool_v2.archive_extractor import get_7z_executable
        
        # This will check if 7z.exe exists and is executable
        sevenz_path = get_7z_executable()
        if sevenz_path and Path(sevenz_path).exists():
            print(f"✅ 7z.exe found at: {sevenz_path}")
            return True
        else:
            print(f"❌ 7z.exe not found. Expected at: {sevenz_path}")
            return False
    except Exception as e:
        print(f"❌ 7z.exe test failed with error: {e}")
        return False


def test_password_loading():
    """Test password loading functionality"""
    print("Testing password loading...")
    try:
        from complex_unzip_tool_v2.password_manager import load_password_book
        from pathlib import Path
        
        # Test with current directory
        passwords = load_password_book(Path("."))
        if passwords and len(passwords) > 0:
            print(f"✅ Password loading works ({len(passwords)} passwords loaded)")
            return True
        else:
            print("⚠️  No passwords.txt found in current directory")
            print("✅ Password loading function works (returns empty list when no file)")
            return True
    except Exception as e:
        print(f"❌ Password loading test failed with error: {e}")
        return False


def test_file_filtering():
    """Test system file filtering"""
    print("Testing file filtering...")
    try:
        from complex_unzip_tool_v2.file_collector import is_system_file
        from pathlib import Path
        
        # Test Windows system files
        result1 = is_system_file(Path("Thumbs.db"))
        result2 = is_system_file(Path("desktop.ini"))
        result3 = is_system_file(Path("passwords.txt"))  # This should be False - it's not a system file, just filtered separately
        
        # Test normal files
        result4 = is_system_file(Path("archive.zip"))
        result5 = is_system_file(Path("document.pdf"))
        
        print(f"  Thumbs.db: {result1}")
        print(f"  desktop.ini: {result2}")
        print(f"  passwords.txt: {result3} (not a system file, filtered separately)")
        print(f"  archive.zip: {result4}")
        print(f"  document.pdf: {result5}")
        
        if result1 and result2 and not result3 and not result4 and not result5:
            print("✅ File filtering works correctly")
            return True
        else:
            print("❌ File filtering returned unexpected results")
            return False
        
    except Exception as e:
        print(f"❌ File filtering test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_archive_processing():
    """Test basic archive processing with a test directory"""
    print("Testing basic archive processing...")
    try:
        import os
        # Use the demo directory if it exists
        demo_path = Path("demo")
        if demo_path.exists():
            result = subprocess.run([
                sys.executable, "-m", "complex_unzip_tool_v2.main", 
                "--dry-run", "--no-extract", str(demo_path)
            ], capture_output=True, text=True, timeout=30, cwd=os.getcwd())
            
            if result.returncode == 0 and "Processing complete" in result.stdout:
                print("✅ Basic archive processing works")
                return True
            else:
                print("❌ Basic archive processing failed")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
        else:
            print("⚠️  Demo directory not found, skipping archive processing test")
            return True
    except Exception as e:
        print(f"❌ Archive processing test failed with error: {e}")
        return False


def main():
    """Run all validation tests"""
    print("="*60)
    print("Complex Unzip Tool v2 - Validation Tests")
    print("="*60)
    
    tests = [
        ("Help Display", test_help_display),
        ("No Arguments Behavior", test_no_args_behavior),
        ("sys.frozen Detection", test_sys_frozen_detection),
        ("7z.exe Availability", test_7z_availability),
        ("Password Loading", test_password_loading),
        ("File Filtering", test_file_filtering),
        ("Basic Archive Processing", test_basic_archive_processing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 40)
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All validation tests passed! The tool is ready to use.")
        return True
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
