# 复杂解压工具 v2 | Complex Unzip Tool v2

![GitHub Release](https://img.shields.io/github/v/release/rozx/Complex-unzip-tool-v2)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/rozx/Complex-unzip-tool-v2)

🌐 **中文** | [English](README.en.md)

**一键解压从网盘下载的"伪装"压缩包 —— 专为百度网盘等网盘场景打造。**

**v1.3.0**：新增 macOS / Linux 支持，内置 7-Zip 26.03，修复密码本位置、单文件分卷清理和 Windows 重定向输出。详见 [1.3.0 发布说明](ReleaseNotes/RELEASE_NOTES_v1.3.0.md)。

---

## 🤔 解决什么问题？

网盘（尤其是百度网盘）上分享的压缩包常被**伪装**：文件名被故意加入乱码以规避内容审查 —— 例如 `movie.7z.001` 变成 `movie.7z.00删1`，或把 `.rar` 改名成一串随机字符。下载后这些文件**无法直接解压**，分卷也被打散。

本工具会自动**还原真实文件名（解伪装）**、**重新分组**分卷、**逐一尝试密码**，并**递归解压**所有内容（含嵌套压缩包），一次搞定。

> 受启发自：https://github.com/TR-Supowe/Complex-Unzip-Tool

---

## 🚀 快速开始

1. **下载**：从 **[Releases](https://github.com/rozx/Complex-unzip-tool-v2/releases)** 页面选择对应系统和架构的发布包。Windows 解开 `.zip` 后得到 `complex-unzip-tool-v2.exe`。
2. **拖拽**：在 Windows 上，将压缩包文件或文件夹拖拽到 `.exe` 上。
3. **完成**：工具会自动解伪装、分组并解压所有内容。

macOS / Linux 下载对应的 `.tar.gz`，解开后在终端运行。以下以 Apple Silicon Mac 为例，其他平台请替换包名：

```bash
tar -xzf complex-unzip-tool-v2-v1.3.0-macos-arm64.tar.gz
./complex-unzip-tool-v2 "$HOME/Downloads/Archives"
```

| 平台 | v1.3.0 发布包 | 内置 7-Zip 26.03 |
| --- | --- | --- |
| Windows x64 | `complex-unzip-tool-v2-v1.3.0-windows-x64.zip` | `7z.exe` + `7z.dll` |
| macOS Intel | `complex-unzip-tool-v2-v1.3.0-macos-x64.tar.gz` | 通用二进制 `7zz` |
| macOS Apple Silicon | `complex-unzip-tool-v2-v1.3.0-macos-arm64.tar.gz` | 通用二进制 `7zz` |
| Linux x64 | `complex-unzip-tool-v2-v1.3.0-linux-x64.tar.gz` | 静态二进制 `7zzs` |
| Linux ARM64 | `complex-unzip-tool-v2-v1.3.0-linux-arm64.tar.gz` | 静态二进制 `7zzs` |

发布包已包含 Python 和 7-Zip，无需另行安装，运行时不联网下载引擎。每个包附带说明和许可证，Release 另附 `SHA256SUMS`。二进制来源、校验值和许可证见 [7z/README.md](7z/README.md)。

macOS 的应用分别按 Intel 和 Apple Silicon 架构构建。Linux 独立包在 Ubuntu 24.04 上构建，需要兼容的系统库；macOS 签名及公证、Windows 发行者签名尚未配置。也可按下方「开发」步骤从源码运行或自行构建。

---

## 📖 使用指南

### 基本用法

```powershell
# 解压文件夹内的所有压缩包
complex-unzip-tool-v2.exe "D:\Downloads\Archives"

# 解压指定文件（只传主卷即可自动收集同目录的同组分卷）
complex-unzip-tool-v2.exe "D:\file.zip" "D:\movie.7z.001"
```

解压结果输出到 `unzipped/` 文件夹。成功后原始压缩包会被移到系统的**回收站 / 废纸篓**（可恢复）。Linux 需要可用的桌面废纸篓目录；回收失败时保留原文件。

只传入一个分卷文件时，会收集同目录、同一命名格式的同组分卷；成功后统一清理，解压或密码失败时全部保留。Windows 下重定向到文件或管道的输出使用 UTF-8，完成后无需按回车退出。

### 密码

很多网盘压缩包带密码。把密码写进 `passwords.txt`，工具会自动逐一尝试（空密码会最先尝试）。

**支持两个位置，二者会自动合并：**

1. **目标目录（待解压文件夹）** —— 把 `passwords.txt` 放在你传给工具的文件夹里，或与待解压文件同级目录。适合「这批文件专用」的密码。
2. **工具目录** —— 把 `passwords.txt` 放在可执行文件旁（Windows 为 `.exe`；macOS / Linux 为 `complex-unzip-tool-v2`）。源码运行时使用项目根目录。该位置不受当前工作目录或拖放启动方式影响。

**文件格式**（每行一个密码，空行忽略，自动去重）：

```text
123456
www.example.com
mypassword
```

- 📝 **自动记忆**：运行中新破解出的密码会自动写回工具目录的 `passwords.txt`，下次直接复用。
- 目标目录的密码本仅作为读取来源（与工具目录相同时除外）。工具目录不可写时会提示保存失败，仍会完成解压收尾；请将程序放到可写目录以保存新密码。构建不会将个人密码本内嵌到程序中。
- 🈶 **编码自适应**：自动识别 UTF-8 / GBK / GB2312 / Big5 / UTF-16（含 BOM），中文密码无需担心乱码。

从旧版本升级时，如果密码本曾被写到桌面、下载目录等启动目录，请将需要长期使用的条目合并到新程序旁的 `passwords.txt`。

### 命令行选项

| 选项 | 说明 |
| --- | --- |
| `--version`, `-v` | 显示版本 |
| `--permanent-delete` | 永久删除原文件而非移入回收站 |
| `--help` | 显示帮助 |

> 🛡️ **默认安全**：当密码错误或分卷缺失时，原文件绝不会被删除。

---

## ✨ 主要特性

- 🎭 **文件名解伪装** —— 通过可配置规则（`config/cloaked_file_rules.json`）还原乱码文件名；解压失败时自动撤销重命名。
- 📦 **多分卷支持** —— 支持 `.001/.002`、`.part1/.part2`、`.rar/.r00`、`.zip/.z01` 等格式，自动查找并重组散落的分卷。
- 🔐 **智能密码** —— 自动尝试密码本并缓存成功密码。
- 🏗️ **嵌套解压** —— 递归解压压缩包中的压缩包。
- 🖱️ **独立运行** —— 各平台可构建内置 Python 与 7-Zip 的单文件程序；Windows 还支持拖拽到 `.exe`。
- 🌐 **中英双语界面** —— 清晰的中英文进度输出。

---

## 🛠️ 开发

需要 Python 3.11+ 与 [Poetry](https://python-poetry.org/)。支持上表所列平台及架构。

```powershell
git clone https://github.com/rozx/Complex-unzip-tool-v2.git
cd Complex-unzip-tool-v2
poetry install

poetry run main "D:\path\to\archives"   # 运行（别名 cuz）
poetry run pytest -q                     # 运行测试
poetry run build                         # 构建当前平台的独立程序 -> dist/
```

macOS / Linux 运行示例：

```bash
poetry run main "$HOME/Downloads/Archives"
poetry run pytest -q
poetry run build
./dist/complex-unzip-tool-v2 --help
```

构建需在目标操作系统和架构上进行。Windows 输出 `.exe`，macOS / Linux 输出无扩展名的可执行文件；构建只包含当前平台的引擎。macOS 的应用本身按当前 Python 架构构建，内置 7-Zip 为通用二进制。当前构建不配置发行者签名或公证。

从源码运行时，若 Unix 引擎的执行权限在复制过程中丢失，可对相应文件执行 `chmod +x 7z/macos/7zz`、`chmod +x 7z/linux-x64/7zzs` 或 `chmod +x 7z/linux-arm64/7zzs`。引擎缺失或不可执行时，工具会在修改输入文件前报错。

架构、约定与解压流程详见 [AGENTS.md](AGENTS.md) 与 [CLAUDE.md](CLAUDE.md)。

### GitHub CI 与自动发布

[CI](.github/workflows/ci.yml) 在推送或提交 PR 到 `main`、`release/**` 时运行。五个平台分别执行完整测试、原生引擎校验、真实压缩包冒烟测试、独立程序构建及构建产物冒烟测试。每个平台的发布包在 Actions artifacts 中保留 14 天。

[Release](.github/workflows/release.yml) 仅在以下条件同时满足时自动发布：

1. PR 的来源分支为 `release/*`，例如 `release/v1.3`。
2. PR 在合并时带有 `release` 标签。
3. PR 被合并到 `main`。

合并前，确认 `pyproject.toml`、包内 `__version__` 和 `.bumpversion.cfg` 使用一致且尚未发布的 `X.Y.Z`。准备后续版本时，可通过 `poetry run bump-minor`、`poetry run bump-patch` 等命令升版。分支名只控制触发，发布标签取自项目版本，例如 `v1.3.0`。同一 PR 必须包含对应的发布说明；1.3.0 的说明位于 [ReleaseNotes/RELEASE_NOTES_v1.3.0.md](ReleaseNotes/RELEASE_NOTES_v1.3.0.md)。文件缺失或为空时，会在平台构建前报错。

提交前可本地检查版本和发布说明：

```powershell
poetry run python -m scripts.release version
poetry run python -m scripts.release verify-notes
```

发布流程会从该 PR 的确切合并提交重新构建全部平台；全部成功后创建 GitHub Release，以 `ReleaseNotes/RELEASE_NOTES_vX.Y.Z.md` 的原文作为正文，并上传上方列出的五个平台发布包和 `SHA256SUMS`。

工作流需先存在于 `main`，之后符合条件的合并才会触发自动发布。标签应在合并前添加；仅关闭 PR、合并后补标签或直接推送 tag 都不会发布。使用内置 `GITHUB_TOKEN`，仅最终发布任务拥有 `contents: write`。

失败时可在 Actions 中重新运行失败任务。上传中断会保留草稿；同版本、同合并提交的草稿可以继续上传，并以该提交中对应版本的说明文件更新正文。校验全部远端文件后才公开发布；已公开的 Release 不会覆盖，指向其他提交的已有 tag 或草稿会报错。

---

## 🤝 参与贡献

欢迎提交 Issue 与 PR。请保持改动小而有测试，并遵循 [CLAUDE.md](CLAUDE.md) 中的 TDD 流程。

## 📄 许可证

MIT 许可证 —— 详见 [LICENSE](LICENSE)。

## 👤 作者

**Rozx** —— [GitHub](https://github.com/rozx)
