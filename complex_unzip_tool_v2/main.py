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
from .modules.richUtils import (
    print_header, print_step, print_success, print_info, 
    print_file_path, create_spinner, print_archive_group_summary,
    print_final_completion, print_extraction_header,
    print_remaining_groups_warning, print_all_processed_success,
    print_separator
)

# Rich-based loading already imported from rich_utils

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
    
    # Header with fancy border
    print_header("🚀 Starting Complex Unzip Tool v2 启动复杂解压工具v2")

    # Step 1: Setup output folder 设置输出文件夹
    print_step(1, "📁 Setting up output folder 设置输出文件夹")
    
    if(os.path.isdir(paths[0])):
        output_folder = os.path.join(paths[0], const.OUTPUT_FOLDER)
    else:
        output_folder = os.path.join(os.path.dirname(paths[0]), const.OUTPUT_FOLDER)
    os.makedirs(output_folder, exist_ok=True)
    print_success("Output folder created 输出文件夹已创建:")
    print_file_path(f"📂 {output_folder}")

    # Step 2: Load passwords 加载密码
    print_step(2, "🔑 Loading passwords 加载密码")
    
    loader = create_spinner("Loading passwords 正在加载密码...")
    loader.start()
    passwordBook = passwordUtil.loadAllPasswords(paths)
    user_provided_passwords = []
    loader.stop()
    
    print_success(f"Loaded {len(passwordBook.getPasswords())} unique passwords 已加载 {len(passwordBook.getPasswords())} 个唯一密码")

    # Step 3: Scanning files 扫描文件
    print_step(3, "📂 Scanning files 扫描文件")
    
    print_info("Extracting files from 正在提取文件自:")
    for i, path in enumerate(paths):
        print_file_path(f"{i+1}. {path}")
    
    loader = create_spinner("Scanning directory 正在扫描目录...")
    loader.start()
    contents = fileUtils.readDir(paths)
    loader.stop()
    
    print_success(f"Found {len(contents)} files 发现 {len(contents)} 个文件")

    # Step 4: Create archive groups 创建档案组
    print_step(4, "📋 Creating archive groups 创建档案组")
    
    loader = create_spinner("Analyzing archive groups 正在分析档案组...")
    loader.start()
    groups = fileUtils.createGroupsByName(contents)
    loader.stop()
    
    print_success(f"Created {len(groups)} archive groups 已创建 {len(groups)} 个档案组")

    # Step 5: Processing archive groups 处理档案组
    print_step(5, "⚙️ Processing archive groups 处理档案组")
    # Remove this line since print_step already handles the formatting

    # Rename archive files to have the correct extensions
    print_info("🎭 Uncloaking file extensions 正在揭示文件扩展名...")
    fileUtils.uncloakFileExtensionForGroups(groups)
    typer.echo()

    # Display groups with fancy formatting
    typer.echo("   📦 Archive Groups Summary 档案组摘要:")
    print_separator()
    
    for i, group in enumerate(groups):
        typer.echo(f"   �️  Group {i+1} 组{i+1}: {group.name}")
        typer.echo(f"      📄 Files 文件 ({len(group.files)}):")
        for j, item in enumerate(group.files[:3]):  # Show first 3 files
            typer.echo(f"         {j+1}. {os.path.basename(item)}")
        if len(group.files) > 3:
            typer.echo(f"         ... and {len(group.files) - 3} more files 还有 {len(group.files) - 3} 个文件")

        if group.mainArchiveFile:
            typer.echo(f"      🎯 Main archive 主档案: {os.path.basename(group.mainArchiveFile)}")
        print_separator()
    typer.echo()

    # Step 6: Processing single archives first 首先处理单一档案
    print_step(6, "🔧 Processing single archives first 首先处理单一档案")
    
    print_info("📝 Processing single archive to extract containers 处理单一档案以提取容器...")

    for group in groups.copy():
        if not group.isMultiPart:
            print_extraction_header(f"🗂️ Extracting single archive: {group.name}")

            dir = os.path.dirname(group.mainArchiveFile)
            extractionTempPath = os.path.join(dir, f'temp.{group.name}')
            typer.echo(f"      📂 Extraction temp path 提取临时路径:")
            typer.echo(f"         {extractionTempPath}")

            try:
                # Start loading indicator for extraction
                loader = create_spinner(f"Extracting {group.name} 正在提取 {group.name}...")
                loader.start()
                
                result = archiveUtils.extractNestedArchives(
                    archive_path=group.mainArchiveFile,
                    output_path=extractionTempPath,
                    password_list=passwordBook.getPasswords(),
                    max_depth=10,
                    cleanup_archives=True,
                    loading_indicator=loader
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
                                    typer.echo(f"         📦 {os.path.basename(file_path)} → moved to group location 移动到组位置")
                                    files_to_remove.append(file_path)
                            else:
                                typer.echo(f"         ⚠️  Warning 警告: File not found 文件未找到: {os.path.basename(file_path)}")
                                files_to_remove.append(file_path)
                        
                        # Remove processed files from the list
                        for file_path in files_to_remove:
                            final_files.remove(file_path)

                        # Move remaining files to output folder
                        if final_files:
                            typer.echo(f"      📤 Moving {len(final_files)} remaining files to output folder")
                            typer.echo(f"         正在将 {len(final_files)} 个剩余文件移动到输出文件夹...")
                            moved_files = fileUtils.moveFilesPreservingStructure(
                                final_files, 
                                extractionTempPath, 
                                output_folder
                            )
                            typer.echo(f"      ✅ Moved {len(moved_files)} files successfully 成功移动 {len(moved_files)} 个文件")
                        
                        # Remove the original archive file
                        try:
                            if os.path.exists(group.mainArchiveFile):
                                os.remove(group.mainArchiveFile)
                                typer.echo(f"      🗑️  Removed original archive 已删除原始档案:")
                                typer.echo(f"         {os.path.basename(group.mainArchiveFile)}")
                        except Exception as e:
                            typer.echo(f"      ⚠️  Warning 警告: Could not remove original archive 无法删除原始档案:")
                            typer.echo(f"         {group.mainArchiveFile}: {e}")

                        # Remove the temporary extraction folder
                        try:
                            if os.path.exists(extractionTempPath):
                                shutil.rmtree(extractionTempPath)
                                typer.echo(f"      🧹 Cleaned up temporary folder 已清理临时文件夹")
                        except Exception as e:
                            typer.echo(f"      ⚠️  Warning 警告: Could not remove temp folder 无法删除临时文件夹: {e}")

                        # Remove the subfolder for group belongs, if not the current folder
                        try:
                            # Get the directory containing the archive files
                            archive_dir = os.path.dirname(group.mainArchiveFile)
                            current_working_dir = os.getcwd()
                            
                            # Only remove if it's not the current working directory and it's empty after file removal
                            if os.path.abspath(archive_dir) != os.path.abspath(current_working_dir):
                                # Check if directory is empty (or only contains hidden files/folders)
                                remaining_items = [item for item in os.listdir(archive_dir) 
                                                 if not item.startswith('.') and item != const.OUTPUT_FOLDER]
                                
                                if not remaining_items:
                                    shutil.rmtree(archive_dir)
                                    typer.echo(f"      🗑️  Removed empty archive subfolder 已删除空档案子文件夹:")
                                    typer.echo(f"         {os.path.basename(archive_dir)}")
                                else:
                                    typer.echo(f"      📁 Archive subfolder kept (contains other files) 档案子文件夹保留（包含其他文件）:")
                                    typer.echo(f"         {os.path.basename(archive_dir)}")
                            else:
                                typer.echo(f"      📁 Archive subfolder is current directory, not removed 档案子文件夹是当前目录，未删除")
                        except Exception as e:
                            typer.echo(f"      ⚠️  Warning 警告: Could not remove archive subfolder 无法删除档案子文件夹: {e}")

                        
                        # Remove the group from processing
                        groups.remove(group)
                        typer.echo("      ✅ Processing completed 处理完成")
                        
                    else:
                        typer.echo(f"      ❌ Error 错误: Expected list of files 期望文件列表")
                        typer.echo(f"         Got {type(final_files_raw)} for {group.name}")
                        groups.remove(group)
                
                else:
                    typer.echo(f"      ❌ Failed to extract 提取失败: {group.name}")
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                    groups.remove(group)
                    
            except Exception as e:
                typer.echo(f"      ❌ Error processing 处理错误: {group.name}")
                typer.echo(f"         Error details 错误详情: {e}")
                # Clean up temp folder if it exists
                try:
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                except:
                    pass
                finally:
                    groups.remove(group)
                continue
            
            print_separator()
            typer.echo()

    # add user provided passwords to password book
    passwordBook.addPasswords(user_provided_passwords)

    # Step 7: Then handle multipart archives 然后处理多部分档案
    print_step(7, "🔗 Processing multipart archives 处理多部分档案")
    
    for group in groups.copy():
        if group.isMultiPart:
            print_extraction_header(f"📚 Handling multipart archive: {group.name}")

            dir = os.path.dirname(group.mainArchiveFile)
            extractionTempPath = os.path.join(dir, f'temp.{group.name}')

            try:
                # Start loading indicator for extraction
                loader = create_spinner(f"Extracting multipart {group.name} 正在提取多部分 {group.name}...")
                loader.start()
                
                result = archiveUtils.extractNestedArchives(
                    archive_path=group.mainArchiveFile,
                    output_path=extractionTempPath,
                    password_list=passwordBook.getPasswords(),
                    max_depth=10,
                    cleanup_archives=True,
                    loading_indicator=loader
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
                            typer.echo(f"      📤 Moving {len(final_files)} files to output folder")
                            typer.echo(f"         正在将 {len(final_files)} 个文件移动到输出文件夹...")
                            moved_files = fileUtils.moveFilesPreservingStructure(
                                final_files, 
                                extractionTempPath, 
                                output_folder
                            )
                            typer.echo(f"      ✅ Moved {len(moved_files)} files successfully 成功移动 {len(moved_files)} 个文件")

                            # Remove the original archive file
                            typer.echo(f"      🗑️  Removing {len(group.files)} archive parts 正在删除 {len(group.files)} 个档案部分...")
                            try:
                                for archive_file in group.files:
                                    if os.path.exists(archive_file):
                                        os.remove(archive_file)
                                        typer.echo(f"         ✓ {os.path.basename(archive_file)}")
                            except Exception as e:
                                typer.echo(f"      ⚠️  Warning 警告: Could not remove some archive parts 无法删除某些档案部分: {e}")

                            # Remove the temporary extraction folder
                            try:
                                if os.path.exists(extractionTempPath):
                                    shutil.rmtree(extractionTempPath)
                                    typer.echo(f"      🧹 Cleaned up temporary folder 已清理临时文件夹")
                            except Exception as e:
                                typer.echo(f"      ⚠️  Warning 警告: Could not remove temp folder 无法删除临时文件夹: {e}")

                            # Remove the subfolder for group belongs, if not the current folder
                            try:
                                # Get the directory containing the archive files
                                archive_dir = os.path.dirname(group.mainArchiveFile)
                                current_working_dir = os.getcwd()
                                
                                # Only remove if it's not the current working directory and it's empty after file removal
                                if os.path.abspath(archive_dir) != os.path.abspath(current_working_dir):
                                    # Check if directory is empty (or only contains hidden files/folders)
                                    remaining_items = [item for item in os.listdir(archive_dir) 
                                                     if not item.startswith('.') and item != const.OUTPUT_FOLDER]
                                    
                                    if not remaining_items:
                                        shutil.rmtree(archive_dir)
                                        typer.echo(f"      🗑️  Removed empty archive subfolder 已删除空档案子文件夹:")
                                        typer.echo(f"         {os.path.basename(archive_dir)}")
                                    else:
                                        typer.echo(f"      📁 Archive subfolder kept (contains other files) 档案子文件夹保留（包含其他文件）:")
                                        typer.echo(f"         {os.path.basename(archive_dir)}")
                                else:
                                    typer.echo(f"      📁 Archive subfolder is current directory, not removed 档案子文件夹是当前目录，未删除")
                            except Exception as e:
                                typer.echo(f"      ⚠️  Warning 警告: Could not remove archive subfolder 无法删除档案子文件夹: {e}")

                            

                            # Remove the group from processing
                            groups.remove(group)
                            typer.echo("      ✅ Processing completed 处理完成")

                    else:
                        typer.echo(f"      ❌ Error 错误: Expected list of files 期望文件列表")
                        typer.echo(f"         Got {type(final_files_raw)} for {group.name}")
                        groups.remove(group)
                else:
                    typer.echo(f"      ❌ Failed to extract 提取失败: {group.name}")
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                    groups.remove(group)

            except Exception as e:
                typer.echo(f"      ❌ Error processing 处理错误: {group.name}")
                typer.echo(f"         Error details 错误详情: {e}")
                # Clean up temp folder if it exists
                try:
                    if os.path.exists(extractionTempPath):
                        shutil.rmtree(extractionTempPath)
                except:
                    pass
                finally:
                    groups.remove(group)
                continue
            
            print_separator()
            typer.echo()

    
    # add user provided password to password book
    passwordBook.addPasswords(user_provided_passwords)

    # Step 8: Final summary 最终摘要
    print_step(8, "📊 Final summary 最终摘要")
    
    # Show remaining unable to process files
    if groups:
        print_remaining_groups_warning(groups)
    else:
        print_all_processed_success()

    # save user provided passwords
    print_info("💾 Saving passwords 正在保存密码...")
    passwordBook.savePasswords()
    
    # Footer with fancy border
    print_final_completion(output_folder)


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

