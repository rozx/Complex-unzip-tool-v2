"""Console utilities for safe Unicode output on Windows."""

import sys


def safe_print(*args, **kwargs):
    """Print function that safely handles Unicode characters on Windows.
    
    Falls back to ASCII-safe alternatives if Unicode encoding fails.
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Convert to ASCII-safe version
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace Unicode characters with ASCII alternatives
                safe_arg = (arg
                    .replace('📁', '[DIR]')
                    .replace('📄', '[FILE]')
                    .replace('📖', '[BOOK]')
                    .replace('🎯', '[TARGET]')
                    .replace('📦', '[ARCHIVE]')
                    .replace('🚀', '[START]')
                    .replace('✅', '[OK]')
                    .replace('❌', '[FAIL]')
                    .replace('⚠️', '[WARN]')
                    .replace('🎉', '[SUCCESS]')
                    .replace('📊', '[STATS]')
                    .replace('🔐', '[LOCK]')
                    .replace('💾', '[SAVE]')
                    .replace('🗂️', '[FOLDER]')
                    .replace('🔍', '[SEARCH]')
                    .replace('⏰', '[TIME]')
                    .replace('🎊', '[DONE]')
                    .replace('✓', '[OK]')
                    .replace('•', '*')
                    .replace('→', '->')
                )
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)


def get_safe_char(unicode_char: str, fallback: str) -> str:
    """Get a Unicode character if supported, otherwise return fallback.
    
    Args:
        unicode_char: The Unicode character to try
        fallback: ASCII fallback character
        
    Returns:
        Unicode character if supported, otherwise fallback
    """
    try:
        # Test if the character can be encoded to the current console encoding
        unicode_char.encode(sys.stdout.encoding or 'utf-8')
        return unicode_char
    except (UnicodeEncodeError, LookupError):
        return fallback
