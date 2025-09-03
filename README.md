# Complex Unzip Tool v2 | 复杂解压工具

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/rozx/Complex-unzip-tool-v2)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/rozx/Complex-unzip-tool-v2)
[![Standalone](https://img.shields.io/badge/standalone-executable-brightgreen.svg)](https://github.com/rozx/Complex-unzip-tool-v2/releases)

## 🚀 Quick Start | 快速开始

**Want to use it right away? Download the standalone executable!**  
**想立即使用？下载独立可执行文件！**

➡️ **[Download complex-unzip-tool-v2.exe](https://github.com/rozx/Complex-unzip-tool-v2/releases)** ⬅️

**🖱️ Super Easy: Just Drag & Drop!**
**🖱️ 超级简单：直接拖拽即可！**

1. Download the executable | 下载可执行文件
2. Drag your archive files or folders onto it | 将档案文件或文件夹拖拽到程序上
3. Watch it automatically extract everything! | 观看它自动提取所有内容！

No installation required - just download and run! | 无需安装 - 下载即可运行！

## 📖 Description | 项目简介

Complex Unzip Tool v2 is a powerful and intelligent archive extraction utility designed to handle complex archive scenarios. It provides advanced features for extracting password-protected archives, multipart archives, and nested archive structures with intelligent password management and automatic organization. The tool includes smart features like drag & drop support, filename uncloaking, and automatic detection of missing archive parts.

复杂解压工具 v2 是一个功能强大且智能的档案提取实用程序，专为处理复杂的档案场景而设计。它提供了提取受密码保护的档案、多部分档案和嵌套档案结构的高级功能，具有智能密码管理和自动组织功能。该工具包含智能功能，如拖拽支持、文件名解隐和自动检测缺失档案部分。

## ✨ Features | 主要特性

- **🖱️ Drag & Drop Support | 拖拽支持**: Simply drag files or folders onto the executable for instant processing | 将文件或文件夹拖拽到可执行文件上即可立即处理
- **📋 Standalone Executable | 独立可执行文件**: No installation required, includes everything needed | 无需安装，包含所需的一切
- **🔐 Smart Password Management | 智能密码管理**: Automatically tries multiple passwords from a password book | 自动从密码本中尝试多个密码
- **📦 Multipart Archive Support | 多部分档案支持**: Handles split archives (.001/.002, .part1/.part2, .rar/.r01) | 处理分割档案 (.001/.002, .part1/.part2, .rar/.r01)
- **🔍 Missing Part Detection | 缺失部分检测**: Automatically finds and reconstructs incomplete multipart archives | 自动查找并重建不完整的多部分档案
- **🎭 Filename Uncloaking | 文件名解隐**: Reveals obfuscated filenames like "aaa.7deletemez.0aaaa0bbb1" → "aaa.7z.001" | 揭示混淆文件名，如 "aaa.7deletemez.0aaaa0bbb1" → "aaa.7z.001"
- **🏗️ Nested Archive Extraction | 嵌套档案提取**: Recursively extracts archives within archives | 递归提取档案中的档案
- **🎯 Intelligent Grouping | 智能分组**: Automatically groups related archive files with cross-reference detection | 自动分组相关档案文件，支持交叉引用检测
- **📊 Rich Progress Display | 丰富的进度显示**: Beautiful command-line interface with progress bars | 美观的命令行界面和进度条
- **🌐 Multilingual Support | 多语言支持**: English and Chinese interface | 中英文界面
- **⚡ High Performance | 高性能**: Efficient extraction with progress tracking | 高效提取并支持进度跟踪
- **🛡️ Error Recovery | 错误恢复**: Robust error handling and recovery mechanisms | 强大的错误处理和恢复机制
- **🔧 Batch Processing | 批量处理**: Handle multiple files and folders in one operation | 在一次操作中处理多个文件和文件夹

## 📋 Requirements | 系统要求

### For Running the Standalone Executable | 运行独立可执行文件的要求
- Windows OS (64-bit recommended) | Windows 操作系统（推荐 64 位）
- No additional dependencies required | 无需额外依赖

### For Development | 开发环境要求
- Python 3.11 or higher | Python 3.11 或更高版本
- Windows OS (includes 7z.exe for extraction) | Windows 操作系统（包含用于提取的 7z.exe）
- Poetry (for dependency management) | Poetry（用于依赖管理）

## 🚀 Installation | 安装方法

### Method 1: Download Standalone Executable (Recommended) | 方法一：下载独立可执行文件（推荐）

Download the latest `complex-unzip-tool-v2.exe` from the [Releases](https://github.com/rozx/Complex-unzip-tool-v2/releases) page. No installation required - just run the executable!

从 [Releases](https://github.com/rozx/Complex-unzip-tool-v2/releases) 页面下载最新的 `complex-unzip-tool-v2.exe`。无需安装 - 直接运行可执行文件即可！

```bash
# Extract archives in a directory | 提取目录中的档案
complex-unzip-tool-v2.exe "C:\path\to\archives"

# Show version | 显示版本
complex-unzip-tool-v2.exe --version
```

### Method 2: Using Poetry (For Development) | 方法二：使用 Poetry（用于开发）

```bash
# Clone the repository | 克隆仓库
git clone https://github.com/rozx/Complex-unzip-tool-v2.git
cd Complex-unzip-tool-v2

# Install dependencies using Poetry | 使用 Poetry 安装依赖
poetry install

# Activate the virtual environment | 激活虚拟环境
poetry shell
```

### Method 3: Manual Installation | 方法三：手动安装

```bash
# Clone the repository | 克隆仓库
git clone https://github.com/rozx/Complex-unzip-tool-v2.git
cd Complex-unzip-tool-v2

# Install dependencies | 安装依赖
pip install typer rich

# Run directly with Python | 直接使用 Python 运行
python -m complex_unzip_tool_v2 [paths | 路径]
```

## 📖 Usage | 使用方法

### Standalone Executable Usage | 独立可执行文件使用

```bash
# Extract archives in a directory | 提取目录中的档案
complex-unzip-tool-v2.exe "C:\path\to\archives"

# Extract specific archive files | 提取特定的档案文件
complex-unzip-tool-v2.exe "C:\archive1.zip" "C:\archive2.rar"

# Show version information | 显示版本信息
complex-unzip-tool-v2.exe --version

# Show help | 显示帮助
complex-unzip-tool-v2.exe --help
```

**💡 Drag & Drop Usage | 拖拽使用方法**

The easiest way to use the tool is by drag and drop:

最简单的使用方法是拖拽操作：

1. **Drag files or folders | 拖拽文件或文件夹**: Simply drag archive files or folders containing archives onto `complex-unzip-tool-v2.exe` | 直接将档案文件或包含档案的文件夹拖拽到 `complex-unzip-tool-v2.exe` 上
2. **Automatic processing | 自动处理**: The tool will automatically detect and extract all archives | 工具会自动检测并提取所有档案
3. **Smart grouping | 智能分组**: Related archive parts will be grouped and processed together | 相关的档案部分会被分组并一起处理

### Development Environment Usage | 开发环境使用

```bash
# Extract archives in a directory | 提取目录中的档案
poetry run main "C:\path\to\archives"

# Or using the alias | 或使用别名
poetry run cuz "C:\path\to\archives"

# Extract specific archive files | 提取特定的档案文件
poetry run main "C:\archive1.zip" "C:\archive2.rar"
```

### Command Line Options | 命令行选项

```bash
# Show version information | 显示版本信息
complex-unzip-tool-v2.exe --version  # For standalone | 独立版本
poetry run main --version           # For development | 开发版本

# Show help | 显示帮助
complex-unzip-tool-v2.exe --help    # For standalone | 独立版本
poetry run main --help              # For development | 开发版本
```

## 🔨 Building Standalone Executable | 构建独立可执行文件

The project includes a comprehensive build system that creates a fully self-contained executable with all dependencies embedded, including Python runtime and 7-Zip binaries.

该项目包含一个完整的构建系统，可创建一个完全独立的可执行文件，包含所有嵌入的依赖项、Python 运行时和 7-Zip 二进制文件。

### Quick Build | 快速构建

```bash
# Build using the poetry script (Recommended) | 使用 poetry 脚本构建（推荐）
poetry run build
```

### Build Methods | 构建方法

#### Method 1: Using Poetry Script (Recommended) | 方法一：使用 Poetry 脚本（推荐）

```bash
# Ensure dependencies are installed | 确保已安装依赖项
poetry install

# Build using the poetry script | 使用 poetry 脚本构建
poetry run build
```

#### Method 2: Using the Build Script | 方法二：使用构建脚本

```bash
# Run the build script directly | 直接运行构建脚本
poetry run python scripts/build.py

# Or on Windows, use the batch file | 或在 Windows 上使用批处理文件
scripts\build.bat
```

#### Method 3: Manual Build | 方法三：手动构建

```bash
# Install PyInstaller (already included in dev dependencies) | 安装 PyInstaller（已包含在开发依赖中）
poetry install

# Run the build script to generate spec and build | 运行构建脚本以生成规范并构建
poetry run python scripts/build.py
```

### Build Output | 构建输出

The standalone executable will be created in the `dist/` folder as `complex-unzip-tool-v2.exe`. This single file is completely self-contained and includes:

独立可执行文件将在 `dist/` 文件夹中创建为 `complex-unzip-tool-v2.exe`。这个单一文件是完全独立的，包含：

- **Python Runtime | Python 运行时**: Complete Python 3.11+ interpreter | 完整的 Python 3.11+ 解释器
- **All Dependencies | 所有依赖项**: Typer, Rich, and all required packages | Typer、Rich 和所有必需的包
- **7-Zip Binaries | 7-Zip 二进制文件**: 
  - `7z.exe` - The main extraction engine | 主要提取引擎
  - `7z.dll` - Required library | 必需的库文件
  - `License.txt` - 7-Zip license | 7-Zip 许可证
- **Application Code | 应用程序代码**: All project modules and classes | 所有项目模块和类
- **Default Passwords | 默认密码**: `passwords.txt` file if present | `passwords.txt` 文件（如果存在）

### Build Features | 构建特性

- **📦 Single File Distribution | 单文件分发**: Everything bundled into one executable | 所有内容捆绑到一个可执行文件中
- **🚀 Fast Startup | 快速启动**: Optimized for quick application launch | 针对快速应用程序启动进行优化
- **🔒 Secure Packaging | 安全打包**: All dependencies are verified and included | 所有依赖项都经过验证并包含在内
- **📊 Progress Tracking | 进度跟踪**: Build process shows detailed progress | 构建过程显示详细进度
- **🎯 Icon Integration | 图标集成**: Includes application icon if available | 包含应用程序图标（如果可用）

### Standalone Usage | 独立版本使用

```bash
# Extract archives | 提取档案
complex-unzip-tool-v2.exe "C:\path\to\archives"

# Extract specific files with multiple passwords | 使用多个密码提取特定文件
complex-unzip-tool-v2.exe "C:\file1.zip" "C:\file2.rar"

# Show version | 显示版本
complex-unzip-tool-v2.exe --version

# Show help | 显示帮助
complex-unzip-tool-v2.exe --help
```

### Distribution | 分发

The standalone executable can be distributed without any installation requirements:

独立可执行文件可以在无需任何安装要求的情况下分发：

- **No Python Required | 无需 Python**: Recipients don't need Python installed | 接收者无需安装 Python
- **No Dependencies | 无依赖**: All libraries are embedded | 所有库都已嵌入
- **Portable | 便携式**: Can be run from any location | 可从任何位置运行
- **Self-Contained | 自包含**: Includes all necessary tools (7-Zip) | 包含所有必要工具（7-Zip）

## 🔐 Password Management | 密码管理

### For Standalone Executable | 独立可执行文件

1. Create a `passwords.txt` file in the same directory as the executable | 在可执行文件的同一目录中创建 `passwords.txt` 文件
2. Add one password per line | 每行添加一个密码
3. The tool will automatically detect and use this file | 工具会自动检测并使用此文件

### For Development Environment | 开发环境

1. Create or edit the `passwords.txt` file in the project root | 在项目根目录创建或编辑 `passwords.txt` 文件
2. Add one password per line | 每行添加一个密码
3. The tool will automatically try these passwords for protected archives | 工具会自动为受保护的档案尝试这些密码

### Password File Example | 密码文件示例

Example `passwords.txt` | `passwords.txt` 示例:
```
password123
mypassword
archive_password
www.example.com
123456
admin
guest
```

### Smart Password Features | 智能密码功能

- **Automatic Detection | 自动检测**: Automatically tries all passwords in sequence | 自动按顺序尝试所有密码
- **Fast Processing | 快速处理**: Optimized password testing algorithm | 优化的密码测试算法
- **Progress Tracking | 进度跟踪**: Shows which passwords are being tested | 显示正在测试的密码
- **Success Caching | 成功缓存**: Remembers successful passwords for similar archives | 为相似档案记住成功的密码

## 🏗️ Project Structure | 项目结构

```
Complex-unzip-tool-v2/
├── complex_unzip_tool_v2/        # Main package | 主包
│   ├── __init__.py               # Package initialization | 包初始化
│   ├── __main__.py               # Entry point for python -m | python -m 入口点
│   ├── main.py                   # Main CLI interface | 主 CLI 接口
│   ├── classes/                  # Core classes | 核心类
│   │   ├── ArchiveGroup.py       # Archive grouping logic | 档案分组逻辑
│   │   └── PasswordBook.py       # Password management | 密码管理
│   └── modules/                  # Utility modules | 实用模块
│       ├── archive_extension_utils.py
│       ├── archive_utils.py      # Archive extraction logic | 档案提取逻辑
│       ├── const.py              # Constants | 常量
│       ├── file_utils.py         # File operations | 文件操作
│       ├── password_util.py      # Password utilities | 密码工具
│       ├── regex.py              # Regular expressions | 正则表达式
│       ├── rich_utils.py         # UI formatting | UI 格式化
│       └── utils.py              # General utilities | 通用工具
├── scripts/                      # Build and utility scripts | 构建和实用脚本
│   ├── build.py                  # Main build script | 主构建脚本
│   ├── build.bat                 # Windows build batch file | Windows 构建批处理文件
│   ├── standalone_main.py        # Standalone entry point | 独立入口点
│   └── generate_icon.py          # Icon generation utility | 图标生成工具
├── 7z/                           # 7-Zip binaries | 7-Zip 二进制文件
│   ├── 7z.exe                    # 7-Zip executable | 7-Zip 可执行文件
│   ├── 7z.dll                    # 7-Zip library | 7-Zip 库文件
│   └── License.txt               # 7-Zip license | 7-Zip 许可证
├── icons/                        # Application icons | 应用程序图标
│   ├── app_icon.ico              # Windows icon | Windows 图标
│   └── app_icon.svg              # Vector icon | 矢量图标
├── dist/                         # Built executables | 构建的可执行文件
│   └── complex-unzip-tool-v2.exe # Standalone executable | 独立可执行文件
├── build/                        # Build artifacts | 构建产物
├── passwords.txt                 # Password list | 密码列表
├── pyproject.toml               # Poetry configuration | Poetry 配置
├── build_standalone.spec        # PyInstaller spec file | PyInstaller 规范文件
└── README.md                    # This file | 本文件
```

## 🔧 Configuration | 配置说明

The tool uses intelligent defaults but can be customized | 工具使用智能默认设置，但可以自定义：

- **Password File | 密码文件**: Edit `passwords.txt` to add your commonly used passwords | 编辑 `passwords.txt` 添加常用密码
- **7-Zip Path | 7-Zip 路径**: The tool uses the bundled 7z.exe by default | 工具默认使用捆绑的 7z.exe
- **Output Directory | 输出目录**: Archives are extracted to their parent directory by default | 档案默认提取到其父目录


## 📝 Examples | 使用示例

### Standalone Executable Examples | 独立可执行文件示例

#### Example 1: Drag & Drop (Recommended) | 示例一：拖拽操作（推荐）
```
Simply drag files or folders onto complex-unzip-tool-v2.exe
直接将文件或文件夹拖拽到 complex-unzip-tool-v2.exe 上
```

#### Example 2: Extract all archives in a folder | 示例二：提取文件夹中的所有档案
```bash
complex-unzip-tool-v2.exe "D:\Downloads\Archives"
```

#### Example 3: Extract specific files | 示例三：提取特定文件
```bash
complex-unzip-tool-v2.exe "D:\file1.zip" "D:\file2.rar" "D:\multipart.001"
```

#### Example 4: Missing partial archive detection | 示例四：缺失分割档案检测
```bash
# When you have movie.part1.rar, movie.part3.rar but missing movie.part2.rar
# The tool will search for and find movie.part2.rar from other archives or folders
# 当你有 movie.part1.rar、movie.part3.rar 但缺少 movie.part2.rar 时
# 工具会搜索并从其他档案或文件夹中找到 movie.part2.rar
complex-unzip-tool-v2.exe "D:\Downloads\Archives\movie.part1.rar" "D:\Downloads\Archives\movie.part3.rar" "D:\Downloads\Archives\movie-part2.rar"

# Also works with .001, .002, .003 format
# 也适用于 .001、.002、.003 格式
# Missing: archive.002, but has archive.001 and archive.003
# 缺失：archive.002，但有 archive.001 和 archive.003
complex-unzip-tool-v2.exe "D:\incomplete_multipart_archives.7z.001" "D:\incomplete_multipart_archives.7z.002" "D:\003part_here.7z"
```

#### Example 5: Filename uncloaking | 示例五：文件名解隐
```bash
# Reveals obfuscated filenames like:
# "aaa.7deletemez.0aaaa0bbb1" → "aaa.7z.001"
# "document.pdfdeleteme.xyz123" → "document.pdf"
# "video.mp4hiddentext.part1" → "video.mp4.part1"
# 揭示混淆的文件名，例如：
# "aaa.7deletemez.0aaaa0bbb1" → "aaa.7z.001"
# "document.pdfdeleteme.xyz123" → "document.pdf"
# "video.mp4hiddentext.part1" → "video.mp4.part1"
complex-unzip-tool-v2.exe "D:\document.pdfdeleteme.xyz123"

# Works with various obfuscation patterns:
# 适用于各种混淆模式：
# - Random text insertion | 随机文本插入
# - Character substitution | 字符替换
# - Extension hiding | 扩展名隐藏
complex-unzip-tool-v2.exe "D:\aaa.7deletemez.0aaaa0bbb1"
```

#### Example 6: Extract with custom password file | 示例六：使用自定义密码文件提取
```bash
# Place passwords.txt in the same directory as the exe | 将 passwords.txt 放在 exe 相同目录中
complex-unzip-tool-v2.exe "D:\protected_archive.zip"
```

#### Example 7: Show version and help | 示例七：显示版本和帮助信息
```bash
complex-unzip-tool-v2.exe --version
complex-unzip-tool-v2.exe --help
```

### Development Environment Examples | 开发环境示例

#### Example 1: Extract all archives in a folder | 示例一：提取文件夹中的所有档案
```bash
poetry run main "D:\Downloads\Archives"
```

#### Example 2: Extract specific files | 示例二：提取特定文件
```bash
poetry run main "D:\file1.zip" "D:\file2.rar" "D:\multipart.001"
```

#### Example 3: Using the short alias | 示例三：使用短别名
```bash
poetry run cuz "D:\Downloads\Archives"
```

## 🤝 Contributing | 参与贡献

1. Fork the repository | Fork 本仓库
2. Create your feature branch | 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. Commit your changes | 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch | 推送到分支 (`git push origin feature/AmazingFeature`)
5. Open a Pull Request | 开启一个 Pull Request

## 📄 License | 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

本项目基于 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👤 Author | 作者

- **Rozx** - [GitHub](https://github.com/rozx)
- Email | 邮箱: lisida900710@gmail.com


