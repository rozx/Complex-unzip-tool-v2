# 复杂解压工具 v2 | Complex Unzip Tool v2

![GitHub Release](https://img.shields.io/github/v/release/rozx/Complex-unzip-tool-v2)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/rozx/Complex-unzip-tool-v2)

🌐 **中文** | [English](README.en.md)

**一键解压从网盘下载的"伪装"压缩包 —— 专为百度网盘等网盘场景打造。**

---

## 🤔 解决什么问题？

网盘（尤其是百度网盘）上分享的压缩包常被**伪装**：文件名被故意加入乱码以规避内容审查 —— 例如 `movie.7z.001` 变成 `movie.7z.00删1`，或把 `.rar` 改名成一串随机字符。下载后这些文件**无法直接解压**，分卷也被打散。

本工具会自动**还原真实文件名（解伪装）**、**重新分组**分卷、**逐一尝试密码**，并**递归解压**所有内容（含嵌套压缩包），一次搞定。

> 受启发自：https://github.com/TR-Supowe/Complex-Unzip-Tool

---

## 🚀 快速开始

1. **下载**：从 **[Releases](https://github.com/rozx/Complex-unzip-tool-v2/releases)** 页面下载最新的 `complex-unzip-tool-v2.exe`，无需安装。
2. **拖拽**：将压缩包文件或文件夹拖拽到 `.exe` 上。
3. **完成**：工具会自动解伪装、分组并解压所有内容。

> 🖱️ 拖拽是最简单的使用方式。

---

## 📖 使用指南

### 基本用法

```powershell
# 解压文件夹内的所有压缩包
complex-unzip-tool-v2.exe "D:\Downloads\Archives"

# 解压指定文件（分卷可一起列出）
complex-unzip-tool-v2.exe "D:\file.zip" "D:\movie.7z.001" "D:\movie.7z.002"
```

解压结果输出到 `unzipped/` 文件夹。成功后原始压缩包会被移到**回收站**（可恢复）。

### 密码

很多网盘压缩包带密码。把密码写进 `passwords.txt`，工具会自动逐一尝试（空密码会最先尝试）。

**支持两个位置，二者会自动合并：**

1. **目标目录（待解压文件夹）** —— 把 `passwords.txt` 放在你传给工具的文件夹里，或与待解压文件同级目录。适合「这批文件专用」的密码。
2. **工具目录** —— 把 `passwords.txt` 放在 `.exe` 同目录（即运行目录），作为常用密码本，对所有任务生效。

**文件格式**（每行一个密码，空行忽略，自动去重）：

```text
123456
www.example.com
mypassword
```

- 📝 **自动记忆**：运行中新破解出的密码会自动写回工具目录的 `passwords.txt`，下次直接复用。
- 🈶 **编码自适应**：自动识别 UTF-8 / GBK / GB2312 / Big5 / UTF-16（含 BOM），中文密码无需担心乱码。

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
- 🖱️ **拖拽即用、独立运行** —— 单文件 `.exe`（内置 Python 与 7-Zip），无需安装。
- 🌐 **中英双语界面** —— 清晰的中英文进度输出。

---

## 🛠️ 开发

需要 Python 3.11+ 与 [Poetry](https://python-poetry.org/)，仅支持 Windows（内置 `7z/7z.exe`）。

```powershell
git clone https://github.com/rozx/Complex-unzip-tool-v2.git
cd Complex-unzip-tool-v2
poetry install

poetry run main "D:\path\to\archives"   # 运行（别名 cuz）
poetry run pytest -q                     # 运行测试
poetry run build                         # 构建独立 exe -> dist/
```

架构、约定与解压流程详见 [AGENTS.md](AGENTS.md) 与 [CLAUDE.md](CLAUDE.md)。

---

## 🤝 参与贡献

欢迎提交 Issue 与 PR。请保持改动小而有测试，并遵循 [CLAUDE.md](CLAUDE.md) 中的 TDD 流程。

## 📄 许可证

MIT 许可证 —— 详见 [LICENSE](LICENSE)。

## 👤 作者

**Rozx** —— [GitHub](https://github.com/rozx)
