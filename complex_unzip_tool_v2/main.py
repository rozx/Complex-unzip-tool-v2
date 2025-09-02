"""Main CLI interface for Complex Unzip Tool v2."""

from ctypes import cast
import os
import shutil
import sys
import time
import threading
import typer
from pathlib import Path
from typing import List, Optional, Annotated

from .modules import passwordUtil
from .modules import fileUtils
from .modules import archiveExtensionUtils
from .modules import archiveUtils
from .modules import const

# Loading indicator class
class LoadingIndicator:
    def __init__(self, message: str):
        self.message = message
        self.is_running = False
        self.thread = None
        
    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join()
        # Clear the line
        print('\r' + ' ' * (len(self.message) + 10), end='\r')
        
    def _animate(self):
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        while self.is_running:
            print(f'\r{spinner[i % len(spinner)]} {self.message}', end='', flush=True)
            time.sleep(0.1)
            i += 1

app = typer.Typer(help="Complex Unzip Tool v2 - Advanced Archive Extraction Utility 复杂解压工具v2 - 高级档案提取实用程序")

@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    paths: Annotated[Optional[List[str]], typer.Argument(help="Archive paths to extract 要提取的档案路径")] = None,
    version: bool = typer.Option(False, "--version", "-v", help="Show version information 显示版本信息")
) -> None:
    """Complex Unzip Tool v2 - Advanced Archive Extraction Utility 复杂解压工具v2 - 高级档案提取实用程序"""
    if version:
        from . import __version__
        typer.echo(f"📦 Complex Unzip Tool v2 {__version__} 复杂解压工具v2")
        raise typer.Exit()
    
    # If no command is provided, run the default extract command
    if ctx.invoked_subcommand is None:
        if paths:
            # Call extract_files directly instead of extract command
            extract_files(paths)
        else:
            # Show help when no paths are provided
            typer.echo(ctx.get_help())
            raise typer.Exit(0)

@app.command()
def version() -> None:
    """Show version information 显示版本信息"""
    from . import __version__
    typer.echo(f"📦 Complex Unzip Tool v2 {__version__} 复杂解压工具v2")

def extract(paths: Annotated[List[str], typer.Argument(help="Paths to the archives to extract 要提取的档案路径")]) -> None:
    """Extract files from an archive 从档案中提取文件"""
    extract_files(paths)

def extract_files(paths: List[str]) -> None:
    """Shared extraction logic 共享提取逻辑"""
    
    typer.echo("🚀 Starting Complex Unzip Tool v2 启动复杂解压工具v2")
    typer.echo("=" * 60)

    # Step 1: Setup output folder 设置输出文件夹
    typer.echo("📁 Step 1: Setting up output folder 步骤1：设置输出文件夹")
    if(os.path.isdir(paths[0])):
        output_folder = os.path.join(paths[0], const.OUTPUT_FOLDER)
    else:
        output_folder = os.path.join(os.path.dirname(paths[0]), const.OUTPUT_FOLDER)
    os.makedirs(output_folder, exist_ok=True)
    typer.echo(f"   ✅ Output folder created 输出文件夹已创建: {output_folder}")

    # Step 2: Load passwords 加载密码
    typer.echo("\n🔑 Step 2: Loading passwords 步骤2：加载密码")
    loader = LoadingIndicator("Loading passwords 正在加载密码...")
    loader.start()
    passwordBook = passwordUtil.loadAllPasswords(paths)
    user_provided_passwords = []
    loader.stop()
    typer.echo(f"   ✅ Loaded {len(passwordBook.getPasswords())} unique passwords 已加载 {len(passwordBook.getPasswords())} 个唯一密码")

    # Step 3: Scanning files 扫描文件
    typer.echo(f"\n📂 Step 3: Scanning files 步骤3：扫描文件")
    typer.echo(f"   📍 Extracting files from 正在提取文件自: {paths}")
    
    loader = LoadingIndicator("Scanning directory 正在扫描目录...")
    loader.start()
    contents = fileUtils.readDir(paths)
    loader.stop()
    typer.echo(f"   ✅ Found {len(contents)} files 发现 {len(contents)} 个文件")

    # Step 4: Create archive groups 创建档案组
    typer.echo(f"\n📋 Step 4: Creating archive groups 步骤4：创建档案组")
    loader = LoadingIndicator("Analyzing archive groups 正在分析档案组...")
    loader.start()
    groups = fileUtils.createGroupsByName(contents)
    loader.stop()
    typer.echo(f"   ✅ Created {len(groups)} archive groups 已创建 {len(groups)} 个档案组")

    # Step 5: Processing archive groups 处理档案组
    typer.echo(f"\n⚙️  Step 5: Processing archive groups 步骤5：处理档案组")

    # Rename archive files to have the correct extensions
    typer.echo("   🎭 Uncloaking file extensions 正在揭示文件扩展名...")
    fileUtils.uncloakFileExtensionForGroups(groups)

    for group in groups:
        typer.echo(f"   📦 Group 组: {group.name}")
        for item in group.files:
            typer.echo(f"      📄 {item}")

        if group.mainArchiveFile:
            typer.echo(f"      🎯 Main archive 主档案: {group.mainArchiveFile}")

    # Step 6: Processing single archives first 首先处理单一档案
    typer.echo(f"\n🔧 Step 6: Processing single archives first 步骤6：首先处理单一档案")
    typer.echo("   📝 Processing single archive to extract containers 处理单一档案以提取容器...")

    for group in groups.copy():
        if not group.isMultiPart:
            typer.echo(f"\n   🗂️  Extracting single archive 正在提取单一档案: {group.name}")

            dir = os.path.dirname(group.mainArchiveFile)
            extractionTempPath = os.path.join(dir, f'temp.{group.name}')
            typer.echo(f"      📂 Extraction temp path 提取临时路径: {extractionTempPath}")

            try:
                # Start loading indicator for extraction
                loader = LoadingIndicator(f"Extracting {group.name} 正在提取 {group.name}...")
                loader.start()
                
                result = archiveUtils.extractNestedArchives(
                    archive_path=group.mainArchiveFile,
                    output_path=extractionTempPath,
                    password_list=passwordBook.getPasswords(),
                    max_depth=10,
                    cleanup_archives=True
                )
                
                loader.stop()

                # Check if extraction was successful and result contains expected data
                if result and result.get("success", False):

                    # add user provided passwords
                    user_provided_passwords.extend(result.get("user_provided_passwords", []))

                    # Successfully extracted nested archives
                    final_files_raw = result.get("final_files", [])
                    
                    # Type guard to ensure we have a list
                    if isinstance(final_files_raw, list):
                        final_files = final_files_raw.copy()  # Make a copy to safely modify
                        
                        typer.echo(f"      ✅ Successfully extracted 成功提取: {group.name}")
                        typer.echo("      🔍 Checking extracted files 正在检查提取的文件...")

                        # Process each extracted file
                        files_to_remove = []
                        for file_path in final_files:
                            if os.path.exists(file_path):
                                if fileUtils.addFileToGroups(file_path, groups):
                                    typer.echo(f"         📦 {os.path.basename(file_path)} is part of multi-part archive, moved to the location of group 是多部分档案的一部分，已移动到组位置")
                                    files_to_remove.append(file_path)
                            else:
                                typer.echo(f"         ⚠️  Warning 警告: File not found 文件未找到: {file_path}")
                                files_to_remove.append(file_path)
                        
                        # Remove processed files from the list
                        for file_path in files_to_remove:
                            final_files.remove(file_path)

                        # Move remaining files to output folder
                        if final_files:
                            typer.echo(f"      📤 Moving {len(final_files)} remaining files to output folder 正在将 {len(final_files)} 个剩余文件移动到输出文件夹...")
                            moved_files = fileUtils.moveFilesPreservingStructure(
                                final_files, 
                                extractionTempPath, 
                                output_folder
                            )
                            typer.echo(f"      ✅ Moved {len(moved_files)} remaining files to 已移动 {len(moved_files)} 个剩余文件到: {output_folder}")
                        
                        # Remove the original archive file
                        try:
                            if os.path.exists(group.mainArchiveFile):
                                os.remove(group.mainArchiveFile)
                                typer.echo(f"      🗑️  Removed original archive 已删除原始档案: {os.path.basename(group.mainArchiveFile)}")
                        except Exception as e:
                            typer.echo(f"      ⚠️  Warning 警告: Could not remove original archive 无法删除原始档案 {group.mainArchiveFile}: {e}")

                        # Remove the temporary extraction folder
                        try:
                            if os.path.exists(extractionTempPath):
                                shutil.rmtree(extractionTempPath)
                                typer.echo(f"      🧹 Cleaned up temporary folder 已清理临时文件夹: {extractionTempPath}")
                        except Exception as e:
                            typer.echo(f"      ⚠️  Warning 警告: Could not remove temp folder 无法删除临时文件夹 {extractionTempPath}: {e}")

                        # Remove the group from processing
                        groups.remove(group)
                        
                    else:
                        typer.echo(f"      ❌ Error 错误: Expected list of files for {group.name}, got {type(final_files_raw)} 期望文件列表，得到 {type(final_files_raw)}")
                        groups.remove(group)
                
                else:
                    typer.echo(f"      ❌ Failed to extract 提取失败: {group.name}")
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                    groups.remove(group)
                    
            except Exception as e:
                typer.echo(f"      ❌ Error processing 处理错误 {group.name}: {e}")
                # Clean up temp folder if it exists
                try:
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                except:
                    pass
                finally:
                    groups.remove(group)
                continue

    # add user provided passwords to password book
    passwordBook.addPasswords(user_provided_passwords)

    # Step 7: Then handle multipart archives 然后处理多部分档案
    typer.echo(f"\n🔗 Step 7: Processing multipart archives 步骤7：处理多部分档案")
    
    for group in groups.copy():
        if group.isMultiPart:
            typer.echo(f"\n   📚 Handling multipart archive 正在处理多部分档案: {group.name}")

            dir = os.path.dirname(group.mainArchiveFile)
            extractionTempPath = os.path.join(dir, f'temp.{group.name}')

            try:
                # Start loading indicator for extraction
                loader = LoadingIndicator(f"Extracting multipart {group.name} 正在提取多部分 {group.name}...")
                loader.start()
                
                result = archiveUtils.extractNestedArchives(
                    archive_path=group.mainArchiveFile,
                    output_path=extractionTempPath,
                    password_list=passwordBook.getPasswords(),
                    max_depth=10,
                    cleanup_archives=True
                )
                
                loader.stop()

                if result and result.get("success", False):

                    # add user provided passwords
                    user_provided_passwords.extend(result.get("user_provided_passwords", []))

                    # Successfully extracted nested archives
                    final_files_raw = result.get("final_files", [])

                    # Type guard to ensure we have a list
                    if isinstance(final_files_raw, list):
                        typer.echo(f"      ✅ Successfully extracted 成功提取: {group.name}")

                        final_files = final_files_raw.copy()  # Make a copy to safely modify

                        # Move files to output folder
                        if final_files:
                            typer.echo(f"      📤 Moving {len(final_files)} files to output folder 正在将 {len(final_files)} 个文件移动到输出文件夹...")
                            moved_files = fileUtils.moveFilesPreservingStructure(
                                final_files, 
                                extractionTempPath, 
                                output_folder
                            )
                            typer.echo(f"      ✅ Moved {len(moved_files)} files to 已移动 {len(moved_files)} 个文件到: {output_folder}")

                            # Remove the original archive file
                            try:
                                for archive_file in group.files:
                                    if os.path.exists(archive_file):
                                        os.remove(archive_file)
                                        typer.echo(f"      🗑️  Removed original archive 已删除原始档案: {os.path.basename(archive_file)}")
                            except Exception as e:
                                typer.echo(f"      ⚠️  Warning 警告: Could not remove original archive 无法删除原始档案 {group.mainArchiveFile}: {e}")

                            # Remove the temporary extraction folder
                            try:
                                if os.path.exists(extractionTempPath):
                                    shutil.rmtree(extractionTempPath)
                                    typer.echo(f"      🧹 Cleaned up temporary folder 已清理临时文件夹: {extractionTempPath}")
                            except Exception as e:
                                typer.echo(f"      ⚠️  Warning 警告: Could not remove temp folder 无法删除临时文件夹 {extractionTempPath}: {e}")

                            # Remove the group from processing
                            groups.remove(group)

                    else:
                        typer.echo(f"      ❌ Error 错误: Expected list of files for {group.name}, got {type(final_files_raw)} 期望文件列表，得到 {type(final_files_raw)}")
                        groups.remove(group)
                else:
                    typer.echo(f"      ❌ Failed to extract 提取失败: {group.name}")
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                    groups.remove(group)


            except Exception as e:
                typer.echo(f"      ❌ Error processing 处理错误 {group.name}: {e}")
                # Clean up temp folder if it exists
                try:
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                except:
                    pass
                finally:
                    groups.remove(group)
                continue

    
    # add user provided password to password book
    passwordBook.addPasswords(user_provided_passwords)

    # Step 8: Final summary 最终摘要
    typer.echo(f"\n📊 Step 8: Final summary 步骤8：最终摘要")
    
    # Show remaining unable to process files
    if groups:
        typer.echo("⚠️  Remaining groups unable to process 剩余无法处理的组:")
        for group in groups:
            typer.echo(f"   ❌ {group.name}")
    else:
        typer.echo("✅ All archives processed successfully 所有档案处理成功!")

    # save user provided passwords
    typer.echo("💾 Saving passwords 正在保存密码...")
    passwordBook.savePasswords()
    
    typer.echo("\n🎉 Extraction completed! 提取完成!")
    typer.echo("=" * 60)


def cli() -> None:
    """Command line interface entry point 命令行界面入口点"""
    app()


def main() -> None:
    """Entry point for the application 应用程序入口点"""
    try:
        cli()
    except KeyboardInterrupt:
        typer.echo("\n❌ Operation cancelled by user 操作被用户取消", err=True)
        sys.exit(1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error 意外错误: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

