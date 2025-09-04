"""
Regex patterns for multi-part archive detection and file naming.
用于多部分档案检测和文件命名的正则表达式模式。

Note: These patterns handle the base case only - files that are already properly 
formatted after cloaked file detection and renaming. For cloaked file detection,
see the rule-based system in cloaked_file_detector.py.
注意：这些模式仅处理基本情况 - 在隐藏文件检测和重命名后已经正确格式化的文件。
对于隐藏文件检测，请参见 cloaked_file_detector.py 中基于规则的系统。
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

# Check for multipart archives (base case only - after cloaked files have been renamed)
# These patterns match different multipart archive conventions:
# - .7z.001, .7z.002, etc. (7z multipart with .00X)
# - .r00, .r01, .r02, etc. (RAR continuation parts)
# - .z01, .z02, .z03, etc. (ZIP continuation parts)  
# - .tar.gz.001, .tar.bz2.001, etc. (TAR multipart)
# - .part1.rar, .part2.rar, etc. (RAR part notation)
# Note: .rar and .zip are ambiguous (could be single files or first parts)
multipart_regex = r"\.(?:7z\.\d{1,3}|tar\.(?:gz|bz2|xz)\.\d{1,3}|r\d{2}|z\d{2}|part\d+\.rar)$"

# Check if it's the first part of a multipart archive (base case only)
# These patterns match the first part of different multipart conventions:
# - .7z.001, .tar.gz.001, etc. (first part with .001)
# - .r00 (RAR first continuation part)  
# - .z01 (ZIP first continuation part)
# - .part1.rar (RAR part1 notation - only part1, not part01 or part001)
# Note: .rar and .zip are excluded as they're ambiguous
first_part_regex = r"\.(?:7z\.0*1|tar\.(?:gz|bz2|xz)\.0*1|r0*0|z0*1|part1\.rar)$"

