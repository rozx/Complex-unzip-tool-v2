# Standalone Build Documentation | 独立构建文档

## Overview | 概述

The Complex Unzip Tool v2 standalone build creates a single executable file that contains:

复杂解压工具 v2 的独立构建创建一个包含以下内容的单个可执行文件：

- Python runtime | Python 运行时
- All Python dependencies (typer, rich, etc.) | 所有 Python 依赖项 (typer, rich 等)
- Application code | 应用程序代码
- 7z.exe and 7z.dll binaries | 7z.exe 和 7z.dll 二进制文件
- License files | 许可证文件

## Build Process | 构建过程

### Prerequisites | 先决条件

1. Python 3.11-3.14
2. Poetry installed | 已安装 Poetry
3. Project dependencies installed: `poetry install` | 已安装项目依赖项：`poetry install`

### Building | 构建

#### Method 1: Using Build Script (Recommended) | 方法一：使用构建脚本（推荐）

```bash
# Windows
poetry run python build.py
# or | 或者
build.bat
```

#### Method 2: Manual Build | 方法二：手动构建

```bash
poetry install  # Ensure PyInstaller is installed | 确保已安装 PyInstaller
poetry run python scripts/build.py  # Generate spec and build | 生成规范并构建
```

### Output | 输出

- Executable: `dist/complex-unzip-tool-v2.exe` | 可执行文件：`dist/complex-unzip-tool-v2.exe`
- Size: ~16.5 MB | 大小：约 16.5 MB
- No external dependencies required | 无需外部依赖项

## Architecture | 架构

### File Structure in Standalone Build | 独立构建中的文件结构

```
complex-unzip-tool-v2.exe
├── Python Runtime | Python 运行时
├── Dependencies | 依赖项
│   ├── typer
│   ├── rich
│   └── other packages | 其他包
├── Application Code | 应用程序代码
│   ├── complex_unzip_tool_v2/
│   │   ├── main.py
│   │   ├── modules/
│   │   └── classes/
│   └── scripts/standalone_main.py (entry point | 入口点)
└── Bundled Resources | 捆绑资源
    ├── 7z/
    │   ├── 7z.exe
    │   ├── 7z.dll
    │   └── License.txt
    └── passwords.txt (if exists | 如果存在)
```

### Project Structure (Development) | 项目结构（开发）

```
Complex-unzip-tool-v2/
├── complex_unzip_tool_v2/          # Main application package | 主应用程序包
├── scripts/                       # Build and utility scripts | 构建和实用脚本
│   ├── build.py                   # Main build script (generates spec) | 主构建脚本（生成规范）
│   ├── build.bat                  # Windows batch launcher | Windows 批处理启动器
│   └── standalone_main.py         # Standalone entry point | 独立入口点
├── 7z/                           # 7-Zip binaries | 7-Zip 二进制文件
├── build.py                      # Root build launcher | 根构建启动器
├── build.bat                     # Root batch launcher | 根批处理启动器
└── dist/                         # Build output directory | 构建输出目录
```

### 7z Path Resolution | 7z 路径解析

The application automatically detects whether it's running in:

应用程序会自动检测其运行环境：

1. **Development mode | 开发模式**: Uses `project_root/7z/7z.exe` | 使用 `project_root/7z/7z.exe`
2. **Standalone mode | 独立模式**: Uses bundled 7z from PyInstaller's temporary directory | 使用 PyInstaller 临时目录中的捆绑 7z

This is handled by the `_get_default_7z_path()` function in `archive_utils.py`.

这由 `archive_utils.py` 中的 `_get_default_7z_path()` 函数处理。

## Distribution | 分发

The standalone executable can be distributed as a single file without requiring:

独立可执行文件可以作为单个文件分发，无需：

- Python installation | Python 安装
- Dependency management | 依赖管理
- 7z installation | 7z 安装
- Configuration files | 配置文件

## Usage | 使用方法

Same as the development version:

与开发版本相同：

```bash
# Show version | 显示版本
complex-unzip-tool-v2.exe --version

# Extract archives | 提取档案
complex-unzip-tool-v2.exe "C:\path\to\archives"

# Show help | 显示帮助
complex-unzip-tool-v2.exe --help
```

## Technical Details | 技术细节

### PyInstaller Specification | PyInstaller 规范

The build script dynamically generates a PyInstaller spec file (`build_standalone_generated.spec`) that:

构建脚本动态生成 PyInstaller 规范文件 (`build_standalone_generated.spec`)：

- Uses `scripts/standalone_main.py` as entry point to avoid import issues | 使用 `scripts/standalone_main.py` 作为入口点以避免导入问题
- Automatically detects and includes 7z binaries as data files | 自动检测并将 7z 二进制文件包含为数据文件
- Includes passwords.txt if available | 如果可用，包含 passwords.txt
- Creates a one-file distribution with UPX compression | 创建带有 UPX 压缩的单文件分发
- Adapts to the current project structure and available files | 适应当前项目结构和可用文件

The spec file is generated dynamically to ensure:

动态生成规范文件以确保：

- Always up-to-date with current project structure | 始终与当前项目结构保持同步
- Automatic detection of available resources | 自动检测可用资源
- No manual maintenance required | 无需手动维护
- Consistent builds across different environments | 在不同环境中的一致构建

### Entry Point Resolution | 入口点解析

- `scripts/standalone_main.py`: Main entry point for PyInstaller builds | PyInstaller 构建的主入口点
- Handles sys.path setup for bundled applications | 处理捆绑应用程序的 sys.path 设置
- Imports and calls the main Typer application | 导入并调用主 Typer 应用程序

### Resource Access | 资源访问

The bundled 7z executables are accessed through PyInstaller's `sys._MEIPASS` temporary directory when running as a standalone executable.

当作为独立可执行文件运行时，通过 PyInstaller 的 `sys._MEIPASS` 临时目录访问捆绑的 7z 可执行文件。

### Dynamic Spec Generation Benefits | 动态规范生成的优势

- **Automatic Resource Detection | 自动资源检测**: Automatically finds and includes available 7z binaries and password files | 自动查找并包含可用的 7z 二进制文件和密码文件
- **Environment Adaptation | 环境适应**: Adapts to different development environments and file structures | 适应不同的开发环境和文件结构
- **No Manual Maintenance | 无需手动维护**: Spec file is always current with the actual project state | 规范文件始终与实际项目状态保持同步
- **Reduced Errors | 减少错误**: Eliminates path mismatch issues and missing file errors | 消除路径不匹配问题和文件缺失错误
- **Clean Repository | 清洁仓库**: Generated spec files are not committed to version control | 生成的规范文件不会提交到版本控制

## Troubleshooting | 故障排除

### Common Issues | 常见问题

1. **Import Errors | 导入错误**: Ensure all modules are included in `hiddenimports` in the spec file | 确保所有模块都包含在规范文件的 `hiddenimports` 中
2. **Missing Resources | 缺少资源**: Verify data files are correctly specified in the spec file | 验证数据文件在规范文件中正确指定
3. **Path Issues | 路径问题**: Check that `_get_default_7z_path()` correctly detects the runtime environment | 检查 `_get_default_7z_path()` 是否正确检测运行时环境

### Debug Build | 调试构建

For debugging, you can modify the build script to create a debug build by editing the `generate_spec_content()` function:

对于调试，您可以通过编辑 `generate_spec_content()` 函数来修改构建脚本以创建调试构建：

```python
# In scripts/build.py, modify the exe section:
exe = EXE(
    # ... other parameters ... | 其他参数
    debug=True,  # Enable debug mode | 启用调试模式
    console=True,  # Keep console window | 保持控制台窗口
    # ...
)
```

## Security Considerations | 安全考虑

- The standalone executable includes all source code | 独立可执行文件包含所有源代码
- Passwords in `passwords.txt` are bundled if present | 如果存在，`passwords.txt` 中的密码会被捆绑
- Consider code obfuscation for sensitive distributions | 对于敏感分发，请考虑代码混淆
- Antivirus software may flag PyInstaller executables (false positive) | 防病毒软件可能会标记 PyInstaller 可执行文件（误报）

## Performance | 性能

- First run may be slower due to extraction to temporary directory | 首次运行可能较慢，因为需要提取到临时目录
- Subsequent operations run at normal speed | 后续操作以正常速度运行
- File size is larger than a Python script but includes all dependencies | 文件大小比 Python 脚本大，但包含所有依赖项
