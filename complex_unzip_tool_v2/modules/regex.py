# Check for multipart archives
multipartRegex = r"\.(?:part\d+\.rar|r\d{2,3}|z\d{2,3}|\d{3}|7z\.\d{3}|zip\.\d{3}|tar\.\d{3})$|\.(?:rar|zip|7z)\.part\d+$"

# Check if it's the first part of a multipart archive
firstPartRegex = r"\.(?:part0*1\.rar|r0*0|z0*1|0*1|7z\.0*1|zip\.0*1|tar\.0*1)$|\.(?:rar|zip|7z)\.part0*1$"

