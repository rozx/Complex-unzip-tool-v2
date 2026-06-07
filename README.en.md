# Complex Unzip Tool v2

![GitHub Release](https://img.shields.io/github/v/release/rozx/Complex-unzip-tool-v2)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/rozx/Complex-unzip-tool-v2)

🌐 [中文](README.md) | **English**

**One-click extraction for disguised ("cloaked") archives downloaded from cloud drives — built for 百度网盘 / Baidu Netdisk.**

---

## 🤔 What problem does it solve?

Archives shared on 百度网盘 (Baidu Netdisk) and other cloud drives are often **cloaked**: their names are deliberately scrambled with junk characters to dodge content scanning — e.g. `movie.7z.001` becomes `movie.7z.00删1`, or a `.rar` is renamed to a random string. After downloading, these files **won't extract directly** and the multipart sets are broken apart.

This tool automatically **restores the real filenames (uncloaks)**, **regroups** split volumes, **tries your passwords**, and **recursively extracts** everything — including nested archives — in one pass.

> Inspired by: https://github.com/TR-Supowe/Complex-Unzip-Tool

---

## 🚀 Quick Start

1. **Download** the latest `complex-unzip-tool-v2.exe` from the **[Releases](https://github.com/rozx/Complex-unzip-tool-v2/releases)** page — no installation needed.
2. **Drag & drop** your archive files or folders onto the `.exe`.
3. **Done** — it uncloaks, groups, and extracts everything automatically.

> 🖱️ Drag & drop is the easiest way to use it.

---

## 📖 Usage Guide

### Basic usage

```powershell
# Extract every archive inside a folder
complex-unzip-tool-v2.exe "D:\Downloads\Archives"

# Extract specific files (multipart parts can be listed together)
complex-unzip-tool-v2.exe "D:\file.zip" "D:\movie.7z.001" "D:\movie.7z.002"
```

Extracted contents are written to an `unzipped/` folder. On success, original archives are moved to the **Recycle Bin** (recoverable).

### Passwords

Many netdisk archives are password-protected. Put your passwords in a `passwords.txt` file and the tool tries each one automatically (the empty password is tried first).

**Two locations are supported and merged automatically:**

1. **Target directory** — place `passwords.txt` in the folder you pass to the tool (or next to the file you pass). Best for passwords specific to that batch of files.
2. **Tool directory** — place `passwords.txt` next to the `.exe` (its working directory) as a global password book used for every run.

**File format** (one password per line; blank lines ignored; duplicates removed automatically):

```text
123456
www.example.com
mypassword
```

- 📝 **Auto-learn**: passwords cracked during a run are written back to the tool-directory `passwords.txt` for reuse next time.
- 🈶 **Encoding-aware**: auto-detects UTF-8 / GBK / GB2312 / Big5 / UTF-16 (with BOM), so Chinese passwords work without mojibake.

### Options

| Option | Description |
| --- | --- |
| `--version`, `-v` | Show version |
| `--permanent-delete` | Permanently delete originals instead of moving them to the Recycle Bin |
| `--help` | Show help |

> 🛡️ **Safe by default**: originals are never deleted when a password fails or a multipart set is incomplete.

---

## ✨ Features

- 🎭 **Filename uncloaking** — restores scrambled names via configurable rules (`config/cloaked_file_rules.json`); renames are reverted if extraction fails.
- 📦 **Multipart support** — `.001/.002`, `.part1/.part2`, `.rar/.r00`, `.zip/.z01`, and more; finds and regroups scattered parts.
- 🔐 **Smart passwords** — tries a password book automatically and caches successful ones.
- 🏗️ **Nested extraction** — recursively extracts archives inside archives.
- 🖱️ **Drag & drop + standalone** — single self-contained `.exe` (Python + 7-Zip bundled), no install.
- 🌐 **Bilingual UI** — clear progress output in English and 中文.

---

## 🛠️ Development

Requires Python 3.11+ and [Poetry](https://python-poetry.org/). Windows only (bundles `7z/7z.exe`).

```powershell
git clone https://github.com/rozx/Complex-unzip-tool-v2.git
cd Complex-unzip-tool-v2
poetry install

poetry run main "D:\path\to\archives"   # run the tool (alias: poetry run cuz)
poetry run pytest -q                     # run tests
poetry run build                         # build the standalone .exe -> dist/
```

See [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) for architecture, conventions, and the extraction pipeline.

---

## 🤝 Contributing

Issues and pull requests are welcome. Please keep changes small, tested, and follow the TDD workflow described in [CLAUDE.md](CLAUDE.md).

## 📄 License

MIT License — see [LICENSE](LICENSE).

## 👤 Author

**Rozx** — [GitHub](https://github.com/rozx)
