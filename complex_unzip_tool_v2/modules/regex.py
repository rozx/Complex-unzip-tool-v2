"""
Regex patterns for multi-part archive detection and file naming.
用于多部分档案检测和文件命名的正则表达式模式。
"""

# Part number patterns for extensionless files that might be archive parts
# 用于可能是档案部分的无扩展名文件的部分编号模式
PART_NUMBER_PATTERNS = [
    (r'(\d{3})$', 3),  # 3 digits like 001, 002, 003
    (r'(\d{2})$', 2),   # 2 digits like 01, 02, 03
    (r'(\d{1})$', 1),   # 1 digit like 1, 2, 3
]

# Multi-part archive format patterns (files that already have proper extensions)
# 多部分档案格式模式（已经有正确扩展名的文件）
MULTIPART_EXTENSION_PATTERNS = [
    r'\.(\d{3})$',  # .001, .002, .003, etc.
    r'\.(\d{2})$',  # .01, .02, .03, etc.
    r'\.(\d{1})$',  # .1, .2, .3, etc.
]

# Check for multipart archives
# Enhanced to include generic multi-part patterns like .xxx.001, .xxx.002, etc.
# Patterns covered:
# - .7z.001, .tar.002, etc. (specific archive types with digits)
# - .7z.part1, .tar.part2, etc. (specific archive types with part notation)
# - .part1.rar, .r01, etc. (other RAR patterns)
# - .xxx.001, .pdf.002, .xls.001, etc. (GENERIC multi-part patterns with extension)
# - xxx.001, archive.002, file.003, etc. (GENERIC multi-part patterns without extension)
multipart_regex = r"\.(?:7z\.\d{3}|tar\.\d{3})$|\.(?:7z|tar)\.part\d+$|\.part\d+\.rar$|\.r\d{2}$|\.\w+\.\d{1,3}$|\w+\.\d{1,3}$"

# Check if it's the first part of a multipart archive
# Enhanced to include generic first parts like .xxx.001, .xxx.01, .xxx.1
# Patterns covered:
# - .7z.001, .tar.001, etc. (specific archive types, first part)
# - .7z.part1, .tar.part1, etc. (specific archive types, first part with part notation)
# - .part1.rar, .r00, etc. (other RAR first parts)
# - .xxx.001, .pdf.001, .xls.001, etc. (GENERIC first parts with extension)
# - xxx.001, archive.001, file.001, etc. (GENERIC first parts without extension)
first_part_regex = r"\.(?:7z\.0*1|tar\.0*1)$|\.(?:7z|tar)\.part0*1$|\.part0*1\.rar$|\.r0*0$|\.\w+\.0*1$|\w+\.0*1$"

