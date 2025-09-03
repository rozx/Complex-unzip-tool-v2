OUTPUT_FOLDER = "unzipped"

# Files to ignore when scanning directories
# 扫描目录时忽略的文件
IGNORED_FILES = {".DS_Store", "thumbs.db", "desktop.ini", "passwords.txt"}

# Multi-part archive patterns for detecting split archives
# 多部分档案模式，用于检测分割档案
MULTI_PART_PATTERNS = [
    r'\.7z\.\d+$',           # .7z.001, .7z.002, etc.
    r'\.rar\.part\d+$',      # .rar.part1, .rar.part2, etc.
    r'\.zip\.\d+$',          # .zip.001, .zip.002, etc.
    r'\.tar\.gz\.\d+$',      # .tar.gz.001, etc.
    r'\.tar\.bz2\.\d+$',     # .tar.bz2.001, etc.
    r'\.tar\.xz\.\d+$',      # .tar.xz.001, etc.
    r'\.\w+\.part\d+$',      # generic .ext.part1 format
]