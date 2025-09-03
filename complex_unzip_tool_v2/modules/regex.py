# Check for multipart archives
# For RAR: only if filename contains "rar" + digits pattern
# For ZIP: only if filename contains "zip" or "z" + digits pattern  
# For other types (7z, tar, etc.): use existing patterns
multipart_regex = r"\.(?:7z\.\d{3}|tar\.\d{3})$|\.(?:7z|tar)\.part\d+$|rar\d+.*\.(?:rar|r\d{2,3})$|(?:zip\d+|z\d+).*\.(?:zip|z\d{2,3})$|\.part\d+\.rar$|\.r\d{2}$"

# Check if it's the first part of a multipart archive
# Updated to match the new multipart logic
first_part_regex = r"\.(?:7z\.0*1|tar\.0*1)$|\.(?:7z|tar)\.part0*1$|rar0*1.*\.(?:rar|r0*0)$|(?:zip0*1|z0*1).*\.(?:zip|z0*1)$|\.part0*1\.rar$|\.r0*0$"

