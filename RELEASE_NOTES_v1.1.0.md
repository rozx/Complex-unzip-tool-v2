# Complex Unzip Tool v2 - Release v1.1.0

**Release Date:** January 4, 2025

## 🌟 What's New in v1.1.0 | v1.1.0 新功能

---

### 🎭 Advanced Cloaked File Detection | 高级隐藏文件检测

This release introduces a powerful new rule-based detection system for identifying and uncloaking obfuscated archive files.

本版本引入了强大的新基于规则的检测系统，用于识别和解隐混淆的档案文件。

- **Rule-based detection system | 基于规则的检测系统**: New JSON configuration system (`cloaked_file_rules.json`) for flexible pattern matching | 新的 JSON 配置系统 (`cloaked_file_rules.json`) 用于灵活的模式匹配
- **Enhanced pattern recognition | 增强的模式识别**: Improved ability to detect and rename obfuscated archive files | 改进了检测和重命名混淆档案文件的能力
- **Priority-based processing | 基于优先级的处理**: Rules are processed in priority order for optimal detection accuracy | 规则按优先级顺序处理，以获得最佳检测准确性
- **Multi-format support | 多格式支持**: Enhanced support for disguised 7z, rar, and zip archives | 增强对伪装的 7z、rar 和 zip 档案的支持

**Example transformations | 转换示例:**
- `movie.7z.deleteme.001` → `movie.7z.001`
- `data.rar.hiddentext.r01` → `data.rar.r01`
- `backup.zip.xyz123.z01` → `backup.zip.z01`

---

### 📊 Improved User Experience | 改进的用户体验

Significant enhancements to the user interface and feedback systems for better interaction.

用户界面和反馈系统的重大改进，提供更好的交互体验。

- **Enhanced statistics tracking | 增强的统计跟踪**: Real-time progress monitoring with detailed metrics and counters | 具有详细指标和计数器的实时进度监控
- **Better output formatting | 更好的输出格式**: Improved visual feedback with enhanced Rich formatting | 通过增强的 Rich 格式改进视觉反馈
- **Multilingual improvements | 多语言改进**: Enhanced message handling and display for better localization | 增强的消息处理和显示，以获得更好的本地化

---

### 🛡️ Robustness Enhancements | 稳健性增强

Improved reliability and error handling for more stable operation.

改进的可靠性和错误处理，提供更稳定的操作。

- **Enhanced archive validation | 增强的档案验证**: Improved validation in ArchiveGroup with better error handling | ArchiveGroup 中改进的验证，具有更好的错误处理
- **Optimized file reading | 优化的文件读取**: Enhanced file reading logic for better performance and reliability | 增强的文件读取逻辑，以获得更好的性能和可靠性
- **Improved error recovery | 改进的错误恢复**: Better handling of edge cases and error conditions | 更好地处理边缘情况和错误条件

---

### 🔧 Technical Improvements | 技术改进

Behind-the-scenes improvements for better maintainability and performance.

幕后改进，提供更好的可维护性和性能。

- **Code organization | 代码组织**: Better separation of concerns and modular design | 更好的关注点分离和模块化设计
- **Performance optimizations | 性能优化**: Faster processing through optimized algorithms | 通过优化算法实现更快的处理
- **Configuration flexibility | 配置灵活性**: JSON-based configuration allows for easy customization | 基于 JSON 的配置允许轻松自定义

---

## 🚀 All Features | 完整功能列表

### Core Capabilities | 核心功能
- **🖱️ Drag & Drop Support | 拖拽支持**: Simply drag files or folders onto the executable for instant processing | 将文件或文件夹拖拽到可执行文件上即可立即处理
- **📋 Standalone Executable | 独立可执行文件**: No installation required, includes everything needed | 无需安装，包含所需的一切
- **🔐 Smart Password Management | 智能密码管理**: Automatically tries multiple passwords from a password book | 自动从密码本中尝试多个密码

### Advanced Archive Handling | 高级档案处理
- **📦 Multipart Archive Support | 多部分档案支持**: Handles split archives (.001/.002, .part1/.part2, .rar/.r01) | 处理分割档案 (.001/.002, .part1/.part2, .rar/.r01)
- **🔍 Missing Part Detection | 缺失部分检测**: Automatically finds and reconstructs incomplete multipart archives | 自动查找并重建不完整的多部分档案
- **🏗️ Nested Archive Extraction | 嵌套档案提取**: Recursively extracts archives within archives | 递归提取档案中的档案
- **🎯 Intelligent Grouping | 智能分组**: Enhanced archive grouping with improved validation and cross-reference detection | 增强的档案分组，具有改进的验证和交叉引用检测

### User Interface & Experience | 用户界面与体验
- **📊 Rich Progress Display | 丰富的进度显示**: Beautiful command-line interface with enhanced progress tracking | 美观的命令行界面，具有增强的进度跟踪
- **🌐 Enhanced Multilingual Support | 增强的多语言支持**: Improved message handling and display for better user experience | 改进的消息处理和显示，以获得更好的用户体验
- **🗂️ Safe File Deletion | 安全文件删除**: Original archives are moved to Recycle Bin by default instead of permanent deletion | 原始档案默认移动到回收站而非永久删除

### Performance & Reliability | 性能与可靠性
- **⚡ High Performance | 高性能**: Optimized file reading and processing logic for faster extraction | 优化的文件读取和处理逻辑，提供更快的提取速度
- **🛡️ Robust Error Recovery | 强大的错误恢复**: Enhanced error handling mechanisms with better validation | 增强的错误处理机制，具有更好的验证
- **🔧 Batch Processing | 批量处理**: Handle multiple files and folders in one operation | 在一次操作中处理多个文件和文件夹

---

## 📊 Performance Improvements | 性能提升

- ⚡ **Faster cloaked file detection** with optimized pattern matching
- 🛡️ **Enhanced error handling** and recovery mechanisms
- 💾 **Improved memory efficiency** in file processing
- 🔄 **Better parallel processing** for multipart archives

- ⚡ **更快的隐藏文件检测**，采用优化的模式匹配
- 🛡️ **增强的错误处理**和恢复机制
- 💾 **改进的内存效率**在文件处理中
- 🔄 **更好的并行处理**用于多部分档案

---

## 🛠️ Bug Fixes & Improvements | 错误修复与改进

### Issues Resolved | 已解决问题

- ✅ **Cloaked file detection** - New rule-based system for better accuracy
- ✅ **Archive validation** - Enhanced validation logic with better error messages  
- ✅ **File reading optimization** - Improved performance and reliability
- ✅ **Progress tracking** - More detailed and accurate progress reporting
- ✅ **Error handling** - Better recovery from edge cases and error conditions
- ✅ **Code organization** - Improved modular design and maintainability

- ✅ **隐藏文件检测** - 新的基于规则的系统，提供更高准确性
- ✅ **档案验证** - 增强的验证逻辑，提供更好的错误消息
- ✅ **文件读取优化** - 改进的性能和可靠性
- ✅ **进度跟踪** - 更详细和准确的进度报告
- ✅ **错误处理** - 更好地从边缘情况和错误条件中恢复
- ✅ **代码组织** - 改进的模块化设计和可维护性

---

## 🔧 System Requirements | 系统要求

### For Standalone Executable | 独立可执行文件
- Windows OS (64-bit recommended) | Windows 操作系统（推荐 64 位）
- No additional dependencies required | 无需额外依赖

### For Development | 开发环境
- Python 3.11+ | Python 3.11 或更高版本
- Windows OS (includes 7z.exe) | Windows 操作系统（包含 7z.exe）
- Poetry for dependency management | Poetry 用于依赖管理

---

## 🙏 Acknowledgments | 致谢

Special thanks to the open-source community and the developers of the libraries that make this project possible:

特别感谢开源社区以及使本项目成为可能的库开发者：

- **7-Zip** - Archive extraction engine
- **Typer** - Modern CLI framework  
- **Rich** - Beautiful terminal formatting
- **Poetry** - Dependency management
- **PyInstaller** - Executable packaging

---

> *Complex Unzip Tool v2 v1.1.0 - Making archive extraction simple, intelligent, and robust.*
> 
> *复杂解压工具 v2 v1.1.0 - 让档案提取变得简单、智能且稳定。*

**Full Changelog**: https://github.com/rozx/Complex-unzip-tool-v2/compare/v1.0.1...v1.1.0