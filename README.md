# Complex Unzip Tool v2 | 复杂解压工具 v2

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/rozx/Complex-unzip-tool-v2)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

## 📖 Description | 项目简介

Complex Unzip Tool v2 is a powerful and intelligent archive extraction utility designed to handle complex archive scenarios. It provides advanced features for extracting password-protected archives, multipart archives, and nested archive structures with intelligent password management and automatic organization.

复杂解压工具 v2 是一个功能强大且智能的档案提取实用程序，专为处理复杂的档案场景而设计。它提供了提取受密码保护的档案、多部分档案和嵌套档案结构的高级功能，具有智能密码管理和自动组织功能。

## ✨ Features | 主要特性

- **🔐 Smart Password Management | 智能密码管理**: Automatically tries multiple passwords from a password book | 自动从密码本中尝试多个密码
- **📦 Multipart Archive Support | 多部分档案支持**: Handles split archives (.001, .002, etc.) | 处理分割档案 (.001, .002 等)
- **🏗️ Nested Archive Extraction | 嵌套档案提取**: Recursively extracts archives within archives | 递归提取档案中的档案
- **🎯 Intelligent Grouping | 智能分组**: Automatically groups related archive files | 自动分组相关的档案文件
- **📊 Rich Progress Display | 丰富的进度显示**: Beautiful command-line interface with progress bars | 美观的命令行界面和进度条
- **🌐 Multilingual Support | 多语言支持**: English and Chinese interface | 中英文界面
- **⚡ High Performance | 高性能**: Efficient extraction with progress tracking | 高效提取并支持进度跟踪
- **🛡️ Error Recovery | 错误恢复**: Robust error handling and recovery mechanisms | 强大的错误处理和恢复机制

## 📋 Requirements | 系统要求

- Python 3.11 or higher | Python 3.11 或更高版本
- Windows OS (includes 7z.exe for extraction) | Windows 操作系统（包含用于提取的 7z.exe）
- Poetry (for dependency management) | Poetry（用于依赖管理）

## 🚀 Installation | 安装方法

### Method 1: Using Poetry (Recommended) | 方法一：使用 Poetry（推荐）

```bash
# Clone the repository | 克隆仓库
git clone https://github.com/rozx/Complex-unzip-tool-v2.git
cd Complex-unzip-tool-v2

# Install dependencies using Poetry | 使用 Poetry 安装依赖
poetry install

# Activate the virtual environment | 激活虚拟环境
poetry shell
```

### Method 2: Manual Installation | 方法二：手动安装

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

### Basic Usage | 基本用法

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
poetry run main --version
poetry run main -v

# Show help | 显示帮助
poetry run main --help
```

## 🔨 Building Standalone Executable | 构建独立可执行文件

To create a standalone executable that includes all dependencies and the 7z binaries:

要创建包含所有依赖项和 7z 二进制文件的独立可执行文件：

### Method 1: Using Poetry Script (Recommended) | 方法一：使用 Poetry 脚本（推荐）

```bash
# Build using the poetry script | 使用 poetry 脚本构建
poetry run build
```

### Method 2: Using the Build Script | 方法二：使用构建脚本

```bash
# Run the build script directly | 直接运行构建脚本
poetry run python scripts/build.py

# Or on Windows, use the batch file | 或在 Windows 上使用批处理文件
scripts\build.bat
```

### Method 3: Manual Build | 方法三：手动构建

```bash
# Install PyInstaller (already included in dev dependencies) | 安装 PyInstaller（已包含在开发依赖中）
poetry install

# Run the build script to generate spec and build | 运行构建脚本以生成规范并构建
poetry run python scripts/build.py
```

The standalone executable will be created in the `dist/` folder as `complex-unzip-tool-v2.exe`. This single file contains everything needed to run the tool, including:

独立可执行文件将在 `dist/` 文件夹中创建为 `complex-unzip-tool-v2.exe`。这个单一文件包含运行工具所需的一切，包括：

- Python runtime | Python 运行时
- All Python dependencies | 所有 Python 依赖项
- 7z.exe and 7z.dll | 7z.exe 和 7z.dll
- Application code | 应用程序代码

Usage of standalone executable | 独立可执行文件的使用：

```bash
# Extract archives | 提取档案
complex-unzip-tool-v2.exe "C:\path\to\archives"

# Show version | 显示版本
complex-unzip-tool-v2.exe --version
```

### Password Management | 密码管理

1. Create or edit the `passwords.txt` file in the project root | 在项目根目录创建或编辑 `passwords.txt` 文件
2. Add one password per line | 每行添加一个密码
3. The tool will automatically try these passwords for protected archives | 工具会自动为受保护的档案尝试这些密码

Example `passwords.txt` | `passwords.txt` 示例:
```
password123
mypassword
archive_password
www.example.com
```

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
├── 7z/                           # 7-Zip binaries | 7-Zip 二进制文件
│   ├── 7z.exe
│   └── 7z.dll
├── passwords.txt                 # Password list | 密码列表
├── pyproject.toml               # Poetry configuration | Poetry 配置
└── README.md                    # This file | 本文件
```

## 🔧 Configuration | 配置说明

The tool uses intelligent defaults but can be customized | 工具使用智能默认设置，但可以自定义：

- **Password File | 密码文件**: Edit `passwords.txt` to add your commonly used passwords | 编辑 `passwords.txt` 添加常用密码
- **7-Zip Path | 7-Zip 路径**: The tool uses the bundled 7z.exe by default | 工具默认使用捆绑的 7z.exe
- **Output Directory | 输出目录**: Archives are extracted to their parent directory by default | 档案默认提取到其父目录

## 📝 Examples | 使用示例

### Example 1: Extract all archives in a folder | 示例一：提取文件夹中的所有档案
```bash
poetry run main "D:\Downloads\Archives"
```

### Example 2: Extract specific files | 示例二：提取特定文件
```bash
poetry run main "D:\file1.zip" "D:\file2.rar" "D:\multipart.001"
```

### Example 3: Show version | 示例三：显示版本信息
```bash
poetry run main --version
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


