# Release Notes v1.3.1 / 发布说明 v1.3.1

Version 1.3.1 stops executables inside archives from being unpacked and deleted, makes nested-archive cleanup recoverable, and adds `#` comments to `passwords.txt`.

1.3.1 修复了档案内的可执行文件被误解压并删除的问题，让嵌套档案的清理可以恢复，并支持在 `passwords.txt` 中使用 `#` 注释。

## New Features / 新功能

### Comments in `passwords.txt` / `passwords.txt` 支持注释 — [#22](https://github.com/rozx/Complex-unzip-tool-v2/issues/22)

Lines starting with `#` are now comments and are not tried as passwords. When newly learned passwords are saved, they are appended to the existing file, so comments, blank lines and the original order are kept.

以 `#` 开头的行现在视为注释，不会被当作密码尝试。保存新学到的密码时会追加到原文件末尾，注释、空行和原有顺序均保持不变。

## Bug Fixes / 错误修复

### Executables inside archives are no longer unpacked / 档案内的可执行文件不再被误解压 — [#21](https://github.com/rozx/Complex-unzip-tool-v2/issues/21)

A file found inside an extracted archive is now extracted only when 7-Zip identifies it as a real container (7z, RAR, ZIP, TAR, gzip, CAB, ISO, …). Plain `.exe`/`.dll` files, which 7-Zip can open to list their PE sections, are now kept unchanged instead of becoming `NAME.dll_2\` folders. The same applies to other formats 7-Zip merely opens, such as ELF/Mach-O binaries, `.msi`/`.doc` (Compound) files, NSIS installers and FLV videos. Self-extracting archives, where 7-Zip reports the embedded container, are still extracted.

Processed nested archives now follow the deletion mode: they go to the Recycle Bin by default and are deleted permanently only with `--permanent-delete`.

解压出的文件现在只有在 7-Zip 识别为真正的档案容器（7z、RAR、ZIP、TAR、gzip、CAB、ISO 等）时才会继续解压。普通 `.exe`/`.dll` 虽然能被 7-Zip 打开并列出 PE 节区，但现在会原样保留，不再变成 `NAME.dll_2\` 目录。ELF/Mach-O 程序、`.msi`/`.doc`（Compound）文件、NSIS 安装包和 FLV 视频等 7-Zip 仅能“打开”的格式同样保留。7-Zip 能识别出内嵌容器的自解压包仍会正常解压。

已处理的嵌套档案现在遵循删除模式：默认移入回收站，只有使用 `--permanent-delete` 时才永久删除。
