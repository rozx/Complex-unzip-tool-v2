#!/usr/bin/env python3
import re

# Read the file
with open('complex_unzip_tool_v2/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the problematic print statement
content = re.sub(r'print\(".*?No cloaked files detected.*?"\)', 'safe_print("✓ No cloaked files detected | 未检测到伪装文件")', content, flags=re.DOTALL)

# Write back
with open('complex_unzip_tool_v2/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Unicode print statement")
