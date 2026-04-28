"""Main CLI interface for Complex Unzip Tool v2."""

import os
import shutil
import sys
import typer
from typing import List, Optional, Annotated
from . import __version__

from .modules import (
    file_utils,
    archive_utils,
    const,
    password_util,
)
from .modules.rename_history import RenameHistory
from .modules.rich_utils import (
    init_statistics,
    print_header,
    print_step,
    print_info,
    print_success,
    print_warning,
    print_error,
    print_archive_group_summary,
    print_remaining_groups_warning,
    print_all_processed_success,
    print_final_completion,
    print_separator,
    create_spinner,
    print_extraction_header,
    print_empty_line,
    print_version,
    print_general,
    print_file_path,
    create_extraction_progress,
    create_file_operation_progress,
    print_major_section_break,
    print_minor_section_break,
    print_processing_separator,
)

app = typer.Typer(
    help="Complex Unzip Tool v2 - Advanced Archive Extraction Utility 复杂解压工具v2 - 高级档案提取实用程序"
)


def _should_delete_original_archives(extract_result: dict) -> bool:
    """Decide whether original archive(s) can be deleted after processing.

    We never delete originals if any files were skipped due to incorrect/missing
    passwords, even if other files extracted successfully.
    """
    try:
        return not bool(extract_result.get("password_failed_archives"))
    except Exception:
        # Be conservative: if result shape is unexpected, don't delete originals.
        return False


def _reconcile_rename_history(
    history: Optional[RenameHistory],
    group_name: str,
    extract_result: Optional[dict],
) -> None:
    """Decide whether to revert or clear renames for this group, based on
    whether the originals are being preserved (revert) or deleted (clear).

    Mirrors `_should_delete_original_archives`: if originals would be kept,
    we put their names back so the user can identify the files manually.
    """
    if history is None:
        return

    if extract_result is None or not _should_delete_original_archives(extract_result):
        count, sample = history.revert_group(group_name)
        if count > 0:
            print_warning(
                f"Reverted {count} rename(s) for {group_name} "
                f"已回滚 {count} 个改名:",
                2,
            )
            for renamed_basename, original_basename in sample:
                print_file_path(f"{renamed_basename} → {original_basename}", 3)
    else:
        cleared = history.clear_group(group_name)
        if cleared > 0:
            print_info(
                f"Cleared {cleared} rename history entr(ies) for {group_name}",
                2,
            )


def _maybe_recover_pending_renames(input_root: str) -> None:
    """If a leftover rename-history file exists, ask the user whether to revert."""
    pending = RenameHistory.load_pending(input_root)
    if pending is None:
        return

    print_warning(
        f"Detected pending rename history from a previous run "
        f"检测到上次运行遗留的改名记录: {len(pending.entries)} entries"
    )
    if not pending.root_matches(input_root):
        print_warning(
            f"⚠ History was recorded for a different input root "
            f"历史文件来自另一个输入目录: {pending.input_root}",
            1,
        )

    for entry in pending.entries[:10]:
        ren_basename = os.path.basename(entry["renamed"])
        orig_basename = os.path.basename(entry["original"])
        group_label = entry.get("group") or "unbound"
        print_file_path(
            f"{ren_basename} → {orig_basename}  ({group_label})", 1
        )
    if len(pending.entries) > 10:
        print_info(f"... and {len(pending.entries) - 10} more", 1)

    try:
        choice = input(
            "Revert these renames before starting? "
            "在开始前回滚这些改名? (y/N) [default: N]: "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        choice = "n"

    if choice not in ("y", "yes"):
        print_info(
            "Skipping recovery. This run will overwrite the history file. "
            "跳过恢复，本次运行将覆盖历史记录。"
        )
        return

    total = 0
    for group_key in pending.bound_group_keys():
        count, _ = pending.revert_group(group_key)
        total += count
    unbound_count, _ = pending.revert_unbound()
    total += unbound_count
    pending.delete_file()
    print_success(
        f"✓ Reverted {total} rename(s) and removed history file "
        f"已回滚 {total} 个改名并删除历史文件"
    )


def _ask_for_user_input_and_exit() -> None:
    """Ask for random user input before exiting the application."""
    # Only ask for input in standalone builds (PyInstaller frozen executables)
    if getattr(sys, "frozen", False):
        input("Press Enter to exit... 按回车键退出...")
    sys.exit(0)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    paths: Annotated[
        Optional[List[str]],
        typer.Argument(help="Archive paths to extract 要提取的档案路径"),
    ] = None,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version information 显示版本信息"
    ),
    permanent_delete: bool = typer.Option(
        False,
        "--permanent-delete",
        "-pd",
        help="Permanently delete original files instead of moving to recycle bin 永久删除原始文件而不是移动到回收站",
    ),
) -> None:
    """Complex Unzip Tool v2 - Advanced Archive Extraction Utility 复杂解压工具v2 - 高级档案提取实用程序"""
    if version:

        print_version(__version__)
        _ask_for_user_input_and_exit()

    # If no command is provided, run the default extract command
    if ctx.invoked_subcommand is None:
        if paths:
            # Call extract_files directly instead of extract command
            extract_files(paths, use_recycle_bin=not permanent_delete)
        else:
            # Show help when no paths are provided
            print_general(ctx.get_help())
            _ask_for_user_input_and_exit()


@app.command()
def version() -> None:
    """Show version information 显示版本信息"""

    print_version(__version__)
    _ask_for_user_input_and_exit()


def extract(
    paths: Annotated[
        List[str],
        typer.Argument(help="Paths to the archives to extract 要提取的档案路径"),
    ],
    permanent_delete: bool = typer.Option(
        False,
        "--permanent-delete",
        "-pd",
        help="Permanently delete original files instead of moving to recycle bin 永久删除原始文件而不是移动到回收站",
    ),
) -> None:
    """Extract files from an archive 从档案中提取文件"""
    extract_files(paths, use_recycle_bin=not permanent_delete)


def extract_files(paths: List[str], use_recycle_bin: bool = True) -> None:
    """Shared extraction logic 共享提取逻辑"""

    # Initialize statistics tracking
    init_statistics()

    # Header with fancy border
    print_header(
        f"🚀 Starting Complex Unzip Tool v2 启动复杂解压工具v2 v{__version__} By Rozx"
    )

    # Derive input root for the rename-history persistence file
    input_root = (
        paths[0] if os.path.isdir(paths[0]) else os.path.dirname(paths[0])
    )

    # Recovery: prompt to revert any leftover renames from a crashed run
    _maybe_recover_pending_renames(input_root)

    # Per-run rename history (records every cloaked-file uncloak rename)
    rename_history = RenameHistory(input_root)

    # Step 1: Setup output folder 设置输出文件夹
    print_step(1, "📁 Setting up output folder 设置输出文件夹")

    if os.path.isdir(paths[0]):
        output_folder = os.path.join(paths[0], const.OUTPUT_FOLDER)
    else:
        output_folder = os.path.join(os.path.dirname(paths[0]), const.OUTPUT_FOLDER)

    os.makedirs(output_folder, exist_ok=True)
    print_success("Output folder created 输出文件夹已创建:")
    print_file_path(f"📂 {output_folder}")
    print_minor_section_break()

    # Step 2: Load passwords 加载密码
    print_step(2, "🔑 Loading passwords 加载密码")

    loader = create_spinner("Loading passwords 正在加载密码...")
    loader.start()
    passwordBook = password_util.load_all_passwords(paths)
    user_provided_passwords = []
    loader.stop()

    print_success(
        f"Loaded {len(passwordBook.get_passwords())} unique passwords 已加载 {len(passwordBook.get_passwords())} 个唯一密码"
    )
    print_minor_section_break()

    # Step 3: Scanning files 扫描文件
    print_step(3, "📂 Scanning files 扫描文件")

    print_info("Extracting files from 正在提取文件自:")
    for i, path in enumerate(paths):
        print_file_path(f"{i+1}. {path}")

    loader = create_spinner("Scanning directory 正在扫描目录...")
    loader.start()
    contents = file_utils.read_dir(paths)
    loader.stop()

    print_success("Scan completed! 扫描完成！")
    print_minor_section_break()

    # Step 4: Uncloak file extensions 揭示文件扩展名
    print_step(4, "🎭 Uncloaking file extensions 揭示文件扩展名")

    loader = create_spinner("Uncloaking file extensions 正在揭示文件扩展名...")
    loader.start()
    contents = file_utils.uncloak_file_extensions(contents, history=rename_history)
    loader.stop()

    print_success("File extensions uncloaked 文件扩展名已揭示")
    print_minor_section_break()

    # Step 5: Create archive groups 创建档案组
    print_step(5, "📋 Creating archive groups 创建档案组")

    loader = create_spinner("Analyzing archive groups 正在分析档案组...")
    loader.start()
    groups = file_utils.create_groups_by_name(contents)
    loader.stop()

    print_success(f"Created {len(groups)} archive groups 已创建 {len(groups)} 个档案组")

    # Bind rename history entries to their owning ArchiveGroup so per-group
    # success/failure can revert or clear the right entries later.
    for group in groups:
        for file_path in group.files:
            rename_history.bind(file_path, group.name)

    print_minor_section_break()

    # Step 6: Processing archive groups 处理档案组
    print_step(6, "⚙️ Processing archive groups 处理档案组")

    # Display groups with fancy formatting - use rich function instead
    print_archive_group_summary(groups)
    print_minor_section_break()

    # Step 7: Processing single archives first 首先处理单一档案
    print_step(7, "🔧 Processing single archives first 首先处理单一档案")

    print_info(
        "📝 Processing single archive to extract containers 处理单一档案以提取容器..."
    )

    # Get single archives for progress tracking
    single_archives = [group for group in groups if not group.isMultiPart]

    if single_archives:
        # Start extraction progress
        extraction_progress = create_extraction_progress("Single Archives")
        extraction_progress.start(len(single_archives))

        for group in single_archives.copy():
            extraction_progress.start_group(group.name, len(group.files))

            print_extraction_header(f"🗂️ Extracting single archive: {group.name}")

            # Check if the main archive file exists
            if not os.path.exists(group.mainArchiveFile):
                print_error(
                    f"Main archive file not found 主档案文件未找到: {os.path.basename(group.mainArchiveFile)}",
                    2,
                )

                # Try to find an alternative main archive in the group
                if group.try_set_alternative_main_archive():
                    print_info(
                        f"Using alternative main archive 使用备用主档案: {os.path.basename(group.mainArchiveFile)}",
                        2,
                    )
                else:
                    print_error(
                        f"No valid archive files found in group 组中未找到有效档案文件: {group.name}",
                        2,
                    )
                    _reconcile_rename_history(rename_history, group.name, None)
                    groups.remove(group)
                    extraction_progress.complete_group(success=False)
                    print_minor_section_break()
                    continue

            dir = os.path.dirname(group.mainArchiveFile)
            extraction_temp_path = os.path.join(dir, f"temp.{group.name}")
            print_info("📂 Extraction temp path 提取临时路径:", 2)
            print_file_path(extraction_temp_path, 3)

            try:
                # Start loading indicator for extraction
                loader = create_spinner(
                    f"Extracting {group.name} 正在提取 {group.name}..."
                )
                loader.start()

                result = archive_utils.extract_nested_archives(
                    archive_path=group.mainArchiveFile,
                    output_path=extraction_temp_path,
                    password_list=passwordBook.get_passwords(),
                    max_depth=10,
                    cleanup_archives=True,
                    loading_indicator=loader,
                    active_progress_bars=[extraction_progress],
                    use_recycle_bin=False,
                    group_relocator=lambda p: bool(
                        file_utils.add_file_to_groups(p, groups)
                    ),
                )

                loader.stop()

                # Check if extraction was successful and result contains expected data
                if result and result.get("success", False):
                    # add user provided passwords
                    user_provided_passwords.extend(
                        result.get("user_provided_passwords", [])
                    )

                    # Successfully extracted nested archives
                    final_files_raw = result.get("final_files", [])

                    # Type guard to ensure we have a list
                    if isinstance(final_files_raw, list):
                        final_files = (
                            final_files_raw.copy()
                        )  # Make a copy to safely modify

                        print_success(
                            f"Successfully extracted 成功提取: {group.name}", 2
                        )

                        # Move files to output folder (relocation to groups happens after this step)
                        if final_files:
                            print_processing_separator()
                            print_info(
                                f"Moving {len(final_files)} files to output folder",
                                2,
                            )
                            print_info(
                                f"正在将 {len(final_files)} 个剩余文件移动到输出文件夹...",
                                3,
                            )

                            # Create file operation progress
                            file_progress = create_file_operation_progress(
                                "Moving Files"
                            )
                            file_progress.start(len(final_files))

                            moved_files = file_utils.move_files_preserving_structure(
                                final_files,
                                extraction_temp_path,
                                output_folder,
                                progress_callback=lambda: file_progress.update(1),
                            )

                            file_progress.stop()
                            print_success(
                                f"Moved {len(moved_files)} files successfully 成功移动 {len(moved_files)} 个文件",
                                2,
                            )

                            # If nested extraction preserved a contained multipart set into the output folder,
                            # create a corresponding multipart group so Step 8 can extract it in the same run.
                            try:
                                moved_abs = [
                                    os.path.join(output_folder, rel)
                                    for rel in moved_files
                                ]
                                created = file_utils.ensure_contained_multipart_groups(
                                    moved_abs, groups
                                )
                                if created:
                                    print_info(
                                        f"Discovered {created} new multipart set(s) from containers 从容器发现 {created} 个新的分卷集合",
                                        2,
                                    )
                            except Exception:
                                # Best-effort only; failure here should not break extraction.
                                pass

                        print_processing_separator()
                        # Remove the original archive file (only when no password skips happened)
                        if not _should_delete_original_archives(result):
                            skipped = result.get("password_failed_archives", [])
                            print_warning(
                                "Skipped deleting original archive because some files were skipped due to password failure "
                                "由于部分文件密码错误/缺失被跳过，未删除原始档案",
                                2,
                            )
                            if skipped:
                                print_info(
                                    f"Password-failed archives (kept) 密码失败档案（已保留）: {len(skipped)}",
                                    3,
                                )
                        else:
                            try:
                                if os.path.exists(group.mainArchiveFile):
                                    success = file_utils.safe_remove(
                                        group.mainArchiveFile,
                                        use_recycle_bin=use_recycle_bin,
                                        error_callback=print_error,
                                    )
                                    if success:
                                        if use_recycle_bin:
                                            print_success(
                                                "Moved original archive to recycle bin 已将原始档案移至回收站:",
                                                2,
                                            )
                                        else:
                                            print_success(
                                                "Removed original archive 已删除原始档案:",
                                                2,
                                            )
                                        print_file_path(
                                            os.path.basename(group.mainArchiveFile), 3
                                        )
                            except Exception as e:
                                print_warning(
                                    "Could not remove original archive 无法删除原始档案:",
                                    2,
                                )
                                print_error(f"{group.mainArchiveFile}: {e}", 3)

                        # Remove the temporary extraction folder
                        try:
                            if os.path.exists(extraction_temp_path):
                                shutil.rmtree(extraction_temp_path)
                                print_success(
                                    "Cleaned up temporary folder 已清理临时文件夹", 2
                                )
                        except Exception as e:
                            print_warning(
                                f"Could not remove temp folder 无法删除临时文件夹: {e}",
                                2,
                            )

                        # Remove the subfolder for group belongs, if not related to output folder
                        try:
                            # Get the directory containing the archive files
                            archive_dir = os.path.dirname(group.mainArchiveFile)

                            # Only remove if it's not the output folder and doesn't contain the output folder
                            if os.path.abspath(archive_dir) != os.path.abspath(
                                output_folder
                            ) and not os.path.abspath(output_folder).startswith(
                                os.path.abspath(archive_dir) + os.sep
                            ):
                                # Check if directory is empty (or only contains hidden files/folders)
                                remaining_items = [
                                    item
                                    for item in os.listdir(archive_dir)
                                    if not item.startswith(".")
                                    and item != const.OUTPUT_FOLDER
                                ]

                                if not remaining_items:
                                    shutil.rmtree(archive_dir)
                                    print_success(
                                        "Removed empty archive subfolder 已删除空档案子文件夹:",
                                        2,
                                    )
                                    print_file_path(os.path.basename(archive_dir), 3)
                                else:
                                    print_info(
                                        "Archive subfolder kept (contains other files) 档案子文件夹保留（包含其他文件）:",
                                        2,
                                    )
                                    print_file_path(os.path.basename(archive_dir), 3)
                            else:
                                print_info(
                                    "Archive subfolder contains output folder, not removed 档案子文件夹包含输出文件夹，未删除",
                                    2,
                                )
                        except Exception as e:
                            print_warning(
                                f"Could not remove archive subfolder 无法删除档案子文件夹: {e}",
                                2,
                            )

                        # Remove the group from processing
                        _reconcile_rename_history(rename_history, group.name, result)
                        groups.remove(group)
                        extraction_progress.complete_group(success=True)
                        print_success("Processing completed 处理完成", 2)
                        print_minor_section_break()

                    else:
                        print_error("Expected list of files 期望文件列表", 2)
                        print_error(f"Got {type(final_files_raw)} for {group.name}", 3)
                        _reconcile_rename_history(rename_history, group.name, None)
                        groups.remove(group)
                        extraction_progress.complete_group(success=False)

                else:
                    print_error(f"Failed to extract 提取失败: {group.name}", 2)
                    if os.path.exists(extraction_temp_path):
                        shutil.rmtree(extraction_temp_path)
                    _reconcile_rename_history(rename_history, group.name, None)
                    groups.remove(group)
                    extraction_progress.complete_group(success=False)
                    print_minor_section_break()

            except Exception as e:
                print_error(f"Error processing 处理错误: {group.name}", 2)
                print_error(f"Error details 错误详情: {e}", 3)

                # Try alternative main archives if available
                if group.try_set_alternative_main_archive():
                    print_info(
                        f"Trying alternative main archive 尝试备用主档案: {os.path.basename(group.mainArchiveFile)}",
                        2,
                    )

                    # Update the extraction temp path for the new main archive
                    new_dir = os.path.dirname(group.mainArchiveFile)
                    new_extraction_temp_path = os.path.join(
                        new_dir, f"temp.{group.name}"
                    )

                    # Clean up the old temp folder if it exists
                    try:
                        if os.path.exists(extraction_temp_path):
                            shutil.rmtree(extraction_temp_path)
                    except Exception:
                        pass

                    try:
                        # Start loading indicator for extraction
                        retry_loader = create_spinner(
                            f"Retrying extraction with alternative archive 使用备用档案重新提取 {group.name}..."
                        )
                        retry_loader.start()

                        retry_result = archive_utils.extract_nested_archives(
                            archive_path=group.mainArchiveFile,
                            output_path=new_extraction_temp_path,
                            password_list=passwordBook.get_passwords(),
                            max_depth=10,
                            cleanup_archives=True,
                            loading_indicator=retry_loader,
                            active_progress_bars=[extraction_progress],
                            use_recycle_bin=False,
                            group_relocator=lambda p: bool(
                                file_utils.add_file_to_groups(p, groups)
                            ),
                        )

                        retry_loader.stop()

                        # Check if retry extraction was successful
                        if retry_result and retry_result.get("success", False):
                            # add user provided passwords from retry
                            user_provided_passwords.extend(
                                retry_result.get("user_provided_passwords", [])
                            )

                            # Process files from retry result
                            retry_final_files = retry_result.get("final_files", [])
                            if retry_final_files:
                                print_processing_separator()
                                print_info(
                                    f"Moving {len(retry_final_files)} files from retry to output folder",
                                    2,
                                )
                                file_progress = create_file_operation_progress(
                                    "Moving Files"
                                )
                                file_progress.start(len(retry_final_files))

                                moved_files = (
                                    file_utils.move_files_preserving_structure(
                                        retry_final_files,
                                        new_extraction_temp_path,
                                        output_folder,
                                        progress_callback=lambda: file_progress.update(
                                            1
                                        ),
                                    )
                                )
                                file_progress.stop()
                                print_success(
                                    f"Moved {len(moved_files)} files successfully 成功移动 {len(moved_files)} 个文件",
                                    2,
                                )

                            # Check for password failures in retry - if any, don't delete original
                            if not _should_delete_original_archives(retry_result):
                                skipped = retry_result.get(
                                    "password_failed_archives", []
                                )
                                print_warning(
                                    "Skipped deleting original archive because retry had password failures "
                                    "由于重试时部分文件密码错误/缺失被跳过，未删除原始档案",
                                    2,
                                )
                                if skipped:
                                    print_info(
                                        f"Password-failed archives (kept) 密码失败档案（已保留）: {len(skipped)}",
                                        3,
                                    )
                            else:
                                # No password failures in retry, safe to delete original
                                try:
                                    if os.path.exists(group.mainArchiveFile):
                                        success = file_utils.safe_remove(
                                            group.mainArchiveFile,
                                            use_recycle_bin=use_recycle_bin,
                                            error_callback=print_error,
                                        )
                                        if success:
                                            if use_recycle_bin:
                                                print_success(
                                                    "Moved original archive to recycle bin 已将原始档案移至回收站:",
                                                    2,
                                                )
                                            else:
                                                print_success(
                                                    "Removed original archive 已删除原始档案:",
                                                    2,
                                                )
                                            print_file_path(
                                                os.path.basename(group.mainArchiveFile),
                                                3,
                                            )
                                except Exception as e:
                                    print_warning(
                                        "Could not remove original archive 无法删除原始档案:",
                                        2,
                                    )
                                    print_error(f"{group.mainArchiveFile}: {e}", 3)

                            # Clean up retry temp folder
                            try:
                                if os.path.exists(new_extraction_temp_path):
                                    shutil.rmtree(new_extraction_temp_path)
                                    print_success(
                                        "Cleaned up temporary folder 已清理临时文件夹",
                                        2,
                                    )
                            except Exception as e:
                                print_warning(
                                    f"Could not remove temp folder 无法删除临时文件夹: {e}",
                                    2,
                                )

                            print_success(
                                f"Alternative archive extraction succeeded 备用档案提取成功: {group.name}",
                                2,
                            )
                            _reconcile_rename_history(
                                rename_history, group.name, retry_result
                            )
                            extraction_progress.complete_group(success=True)
                            print_minor_section_break()
                            continue  # Skip the removal and continue with next group
                        else:
                            print_error(
                                f"Alternative archive extraction also failed 备用档案提取也失败: {group.name}",
                                2,
                            )
                            # Clean up temp folder if it exists
                            if os.path.exists(new_extraction_temp_path):
                                shutil.rmtree(new_extraction_temp_path)

                    except Exception as retry_e:
                        print_error(f"Error during retry 重试时出错: {retry_e}", 3)
                        # Clean up temp folder if it exists
                        if os.path.exists(new_extraction_temp_path):
                            try:
                                shutil.rmtree(new_extraction_temp_path)
                            except Exception:
                                pass
                else:
                    print_warning(
                        f"No alternative archives available for group 组中没有备用档案: {group.name}",
                        2,
                    )

                # Clean up original temp folder if it still exists
                try:
                    if os.path.exists(extraction_temp_path):
                        shutil.rmtree(extraction_temp_path)
                except Exception:
                    pass
                finally:
                    _reconcile_rename_history(rename_history, group.name, None)
                    groups.remove(group)
                    extraction_progress.complete_group(success=False)
                    print_minor_section_break()
                continue

            print_separator()
            print_empty_line()

        extraction_progress.stop()
    else:
        print_info("No single archives found 未找到单一档案")
        print_minor_section_break()

    # After extracting single archives, reconcile any multipart parts that were
    # extracted into the output folder so multipart sets are complete before extraction
    print_info("🔄 Reconciling parts from extracted containers 对齐从容器提取的分卷...")
    moved_parts = file_utils.relocate_multipart_parts_from_directory(
        output_folder, groups
    )
    if moved_parts:
        print_success(
            f"Relocated {moved_parts} multipart parts to their groups 已移动 {moved_parts} 个分卷到对应组"
        )
    else:
        print_info("No multipart parts to relocate 无需移动的分卷")
    print_minor_section_break()

    # add user provided passwords to password book
    if user_provided_passwords:
        passwordBook.add_passwords(user_provided_passwords)

    # Step 8: Then handle multipart archives 然后处理多部分档案
    print_step(8, "🔗 Processing multipart archives 处理多部分档案")

    # Get multipart archives for progress tracking
    multipart_archives = [group for group in groups if group.isMultiPart]

    if multipart_archives:
        # Start extraction progress for multipart archives
        multipart_progress = create_extraction_progress("Multipart Archives")
        multipart_progress.start(len(multipart_archives))

        for group in multipart_archives.copy():
            multipart_progress.start_group(group.name, len(group.files))

            print_extraction_header(f"📚 Handling multipart archive: {group.name}")

            # Check if the main archive file exists
            if not os.path.exists(group.mainArchiveFile):
                print_error(
                    f"Main multipart archive file not found 主多部分档案文件未找到: {os.path.basename(group.mainArchiveFile)}",
                    2,
                )

                # Try to find an alternative main archive in the group
                if group.try_set_alternative_main_archive():
                    print_info(
                        f"Using alternative main multipart archive 使用备用主多部分档案: {os.path.basename(group.mainArchiveFile)}",
                        2,
                    )
                else:
                    print_error(
                        f"No valid multipart archive files found in group 组中未找到有效多部分档案文件: {group.name}",
                        2,
                    )
                    _reconcile_rename_history(rename_history, group.name, None)
                    groups.remove(group)
                    multipart_progress.complete_group(success=False)
                    print_minor_section_break()
                    continue

            dir = os.path.dirname(group.mainArchiveFile)
            extraction_temp_path = os.path.join(dir, f"temp.{group.name}")

            try:
                # Start loading indicator for extraction
                loader = create_spinner(
                    f"Extracting multipart {group.name} 正在提取多部分 {group.name}..."
                )
                loader.start()

                result = archive_utils.extract_nested_archives(
                    archive_path=group.mainArchiveFile,
                    output_path=extraction_temp_path,
                    password_list=passwordBook.get_passwords(),
                    max_depth=10,
                    cleanup_archives=True,
                    loading_indicator=loader,
                    active_progress_bars=[multipart_progress],
                    use_recycle_bin=False,
                    group_relocator=lambda p: bool(
                        file_utils.add_file_to_groups(p, groups)
                    ),
                )

                loader.stop()

                if result and result.get("success", False):
                    # add user provided passwords
                    user_provided_passwords.extend(
                        result.get("user_provided_passwords", [])
                    )

                    # Successfully extracted nested archives
                    final_files_raw = result.get("final_files", [])

                    # Type guard to ensure we have a list
                    if isinstance(final_files_raw, list):
                        print_success(
                            f"Successfully extracted 成功提取: {group.name}", 2
                        )
                        print_processing_separator()

                        final_files = (
                            final_files_raw.copy()
                        )  # Make a copy to safely modify

                        # Move files to output folder
                        if final_files:
                            print_info(
                                f"Moving {len(final_files)} files to output folder", 2
                            )
                            print_info(
                                f"正在将 {len(final_files)} 个文件移动到输出文件夹...",
                                3,
                            )

                            # Create file operation progress
                            file_progress = create_file_operation_progress(
                                "Moving Files"
                            )
                            file_progress.start(len(final_files))

                            moved_files = file_utils.move_files_preserving_structure(
                                final_files,
                                extraction_temp_path,
                                output_folder,
                                progress_callback=lambda: file_progress.update(1),
                            )

                            file_progress.stop()
                            print_success(
                                f"Moved {len(moved_files)} files successfully 成功移动 {len(moved_files)} 个文件",
                                2,
                            )

                            print_processing_separator()
                            # Remove the original archive parts (only when no password skips happened)
                            if not _should_delete_original_archives(result):
                                skipped = result.get("password_failed_archives", [])
                                print_warning(
                                    "Skipped deleting original archive parts because some files were skipped due to password failure "
                                    "由于部分文件密码错误/缺失被跳过，未删除原始分卷档案",
                                    2,
                                )
                                if skipped:
                                    print_info(
                                        f"Password-failed archives (kept) 密码失败档案（已保留）: {len(skipped)}",
                                        3,
                                    )
                            else:
                                if use_recycle_bin:
                                    print_info(
                                        f"Moving {len(group.files)} archive parts to recycle bin 正在将 {len(group.files)} 个档案部分移至回收站...",
                                        2,
                                    )
                                else:
                                    print_info(
                                        f"Removing {len(group.files)} archive parts 正在删除 {len(group.files)} 个档案部分...",
                                        2,
                                    )
                                try:
                                    for archive_file in group.files:
                                        if os.path.exists(archive_file):
                                            success = file_utils.safe_remove(
                                                archive_file,
                                                use_recycle_bin=use_recycle_bin,
                                                error_callback=print_error,
                                            )
                                            if success:
                                                print_success(
                                                    f"✓ {os.path.basename(archive_file)}",
                                                    3,
                                                )
                                except Exception as e:
                                    print_warning(
                                        f"Could not remove some archive parts 无法删除某些档案部分: {e}",
                                        2,
                                    )

                            # Remove the temporary extraction folder
                            try:
                                if os.path.exists(extraction_temp_path):
                                    shutil.rmtree(extraction_temp_path)
                                    print_success(
                                        "Cleaned up temporary folder 已清理临时文件夹",
                                        2,
                                    )
                            except Exception as e:
                                print_warning(
                                    f"Could not remove temp folder 无法删除临时文件夹: {e}",
                                    2,
                                )

                            # Remove the subfolder for group belongs, if not related to output folder
                            try:
                                # Get the directory containing the archive files
                                archive_dir = os.path.dirname(group.mainArchiveFile)

                                # Only remove if it's not the output folder and doesn't contain the output folder
                                if os.path.abspath(archive_dir) != os.path.abspath(
                                    output_folder
                                ) and not os.path.abspath(output_folder).startswith(
                                    os.path.abspath(archive_dir) + os.sep
                                ):
                                    # Check if directory is empty (or only contains hidden files/folders)
                                    remaining_items = [
                                        item
                                        for item in os.listdir(archive_dir)
                                        if not item.startswith(".")
                                        and item != const.OUTPUT_FOLDER
                                    ]

                                    if not remaining_items:
                                        shutil.rmtree(archive_dir)
                                        print_success(
                                            "Removed empty archive subfolder 已删除空档案子文件夹:",
                                            2,
                                        )
                                        print_file_path(
                                            os.path.basename(archive_dir), 3
                                        )
                                    else:
                                        print_info(
                                            "Archive subfolder kept (contains other files) 档案子文件夹保留（包含其他文件）:",
                                            2,
                                        )
                                        print_file_path(
                                            os.path.basename(archive_dir), 3
                                        )
                                else:
                                    print_info(
                                        "Archive subfolder contains output folder, not removed 档案子文件夹包含输出文件夹，未删除",
                                        2,
                                    )
                            except Exception as e:
                                print_warning(
                                    f"Could not remove archive subfolder 无法删除档案子文件夹: {e}",
                                    2,
                                )

                            # Remove the group from processing
                            _reconcile_rename_history(
                                rename_history, group.name, result
                            )
                            groups.remove(group)
                            multipart_progress.complete_group(success=True)
                            print_success("Processing completed 处理完成", 2)
                            print_minor_section_break()

                    else:
                        print_error("Expected list of files 期望文件列表", 2)
                        print_error(f"Got {type(final_files_raw)} for {group.name}", 3)
                        _reconcile_rename_history(rename_history, group.name, None)
                        groups.remove(group)
                        multipart_progress.complete_group(success=False)
                        print_minor_section_break()
                else:
                    print_error(f"Failed to extract 提取失败: {group.name}", 2)
                    if os.path.exists(extraction_temp_path):
                        shutil.rmtree(extraction_temp_path)
                        print_info(
                            "Retained source multipart parts due to extraction failure 提取失败，保留源分卷",
                            2,
                        )
                    _reconcile_rename_history(rename_history, group.name, None)
                    groups.remove(group)
                    multipart_progress.complete_group(success=False)
                    print_minor_section_break()

            except Exception as e:
                print_error(f"Error processing 处理错误: {group.name}", 2)
                print_error(f"Error details 错误详情: {e}", 3)

                # Try alternative main archives if available
                if group.try_set_alternative_main_archive():
                    print_info(
                        f"Trying alternative main archive 尝试备用主档案: {os.path.basename(group.mainArchiveFile)}",
                        2,
                    )

                    # Update the extraction temp path for the new main archive
                    new_dir = os.path.dirname(group.mainArchiveFile)
                    new_extraction_temp_path = os.path.join(
                        new_dir, f"temp.{group.name}"
                    )

                    # Clean up the old temp folder if it exists
                    try:
                        if os.path.exists(extraction_temp_path):
                            shutil.rmtree(extraction_temp_path)
                    except Exception:
                        pass

                    try:
                        # Start loading indicator for extraction
                        retry_loader = create_spinner(
                            f"Retrying multipart extraction 重新尝试多部分提取 {group.name}..."
                        )
                        retry_loader.start()

                        retry_result = archive_utils.extract_nested_archives(
                            archive_path=group.mainArchiveFile,
                            output_path=new_extraction_temp_path,
                            password_list=passwordBook.get_passwords(),
                            max_depth=10,
                            cleanup_archives=True,
                            loading_indicator=retry_loader,
                            active_progress_bars=[multipart_progress],
                            use_recycle_bin=False,
                            group_relocator=lambda p: bool(
                                file_utils.add_file_to_groups(p, groups)
                            ),
                        )

                        retry_loader.stop()

                        # Check if retry extraction was successful
                        if retry_result and retry_result.get("success", False):
                            # add user provided passwords from retry
                            user_provided_passwords.extend(
                                retry_result.get("user_provided_passwords", [])
                            )

                            # Process files from retry result
                            retry_final_files = retry_result.get("final_files", [])
                            if retry_final_files:
                                print_processing_separator()
                                print_info(
                                    f"Moving {len(retry_final_files)} files from retry to output folder",
                                    2,
                                )
                                file_progress = create_file_operation_progress(
                                    "Moving Files"
                                )
                                file_progress.start(len(retry_final_files))

                                moved_files = (
                                    file_utils.move_files_preserving_structure(
                                        retry_final_files,
                                        new_extraction_temp_path,
                                        output_folder,
                                        progress_callback=lambda: file_progress.update(
                                            1
                                        ),
                                    )
                                )
                                file_progress.stop()
                                print_success(
                                    f"Moved {len(moved_files)} files successfully 成功移动 {len(moved_files)} 个文件",
                                    2,
                                )

                            # Check for password failures in retry - if any, don't delete original
                            if not _should_delete_original_archives(retry_result):
                                skipped = retry_result.get(
                                    "password_failed_archives", []
                                )
                                print_warning(
                                    "Skipped deleting original archive parts because retry had password failures "
                                    "由于重试时部分文件密码错误/缺失被跳过，未删除原始分卷档案",
                                    2,
                                )
                                if skipped:
                                    print_info(
                                        f"Password-failed archives (kept) 密码失败档案（已保留）: {len(skipped)}",
                                        3,
                                    )
                            else:
                                # No password failures in retry, safe to delete original parts
                                print_processing_separator()
                                if use_recycle_bin:
                                    print_info(
                                        f"Moving {len(group.files)} archive parts to recycle bin 正在将 {len(group.files)} 个档案部分移至回收站...",
                                        2,
                                    )
                                else:
                                    print_info(
                                        f"Removing {len(group.files)} archive parts 正在删除 {len(group.files)} 个档案部分...",
                                        2,
                                    )
                                try:
                                    for archive_file in group.files:
                                        if os.path.exists(archive_file):
                                            success = file_utils.safe_remove(
                                                archive_file,
                                                use_recycle_bin=use_recycle_bin,
                                                error_callback=print_error,
                                            )
                                            if success:
                                                print_success(
                                                    f"✓ {os.path.basename(archive_file)}",
                                                    3,
                                                )
                                except Exception as e:
                                    print_warning(
                                        f"Could not remove some archive parts 无法删除某些档案部分: {e}",
                                        2,
                                    )

                            # Clean up retry temp folder
                            try:
                                if os.path.exists(new_extraction_temp_path):
                                    shutil.rmtree(new_extraction_temp_path)
                                    print_success(
                                        "Cleaned up temporary folder 已清理临时文件夹",
                                        2,
                                    )
                            except Exception as e:
                                print_warning(
                                    f"Could not remove temp folder 无法删除临时文件夹: {e}",
                                    2,
                                )

                            print_success(
                                f"Alternative multipart archive extraction succeeded 备用多部分档案提取成功: {group.name}",
                                2,
                            )
                            _reconcile_rename_history(
                                rename_history, group.name, retry_result
                            )
                            multipart_progress.complete_group(success=True)
                            print_minor_section_break()
                            continue  # Skip the removal and continue with next group
                        else:
                            print_error(
                                f"Alternative multipart archive extraction also failed 备用多部分档案提取也失败: {group.name}",
                                2,
                            )
                            # Clean up temp folder if it exists
                            if os.path.exists(new_extraction_temp_path):
                                shutil.rmtree(new_extraction_temp_path)
                                print_info(
                                    "Retained source multipart parts due to extraction failure 提取失败，保留源分卷",
                                    2,
                                )

                    except Exception as retry_e:
                        print_error(
                            f"Error during multipart retry 多部分重试时出错: {retry_e}",
                            3,
                        )
                        # Clean up temp folder if it exists
                        if os.path.exists(new_extraction_temp_path):
                            try:
                                shutil.rmtree(new_extraction_temp_path)
                            except Exception:
                                pass
                else:
                    print_warning(
                        f"No alternative multipart archives available for group 组中没有备用多部分档案: {group.name}",
                        2,
                    )

                # Clean up original temp folder if it still exists
                try:
                    if os.path.exists(extraction_temp_path):
                        shutil.rmtree(extraction_temp_path)
                except Exception:
                    pass
                finally:
                    print_info(
                        "Retained source multipart parts due to extraction failure 提取失败，保留源分卷",
                        2,
                    )
                    _reconcile_rename_history(rename_history, group.name, None)
                    groups.remove(group)
                    multipart_progress.complete_group(success=False)
                    print_minor_section_break()
                continue

            print_separator()
            print_empty_line()

        multipart_progress.stop()
    else:
        print_info("No multipart archives found 未找到多部分档案")
        print_minor_section_break()

    # add user provided password to password book
    if user_provided_passwords:
        passwordBook.add_passwords(user_provided_passwords)

    # Step 9: Final summary 最终摘要
    print_step(9, "📊 Final summary 最终摘要")

    # Show remaining unable to process files
    if groups:
        print_remaining_groups_warning(groups)
    else:
        print_all_processed_success()

    print_minor_section_break()
    # save user provided passwords only if there are changes
    if passwordBook.has_unsaved_changes():
        print_info("💾 Saving passwords 正在保存密码...")
        passwordBook.save_passwords()
    else:
        print_info("📝 No new passwords to save 没有新密码需要保存")

    # Revert any rename history entries that never bound to a group (their
    # renamed file likely vanished before grouping completed).
    unbound_count, unbound_sample = rename_history.revert_unbound()
    if unbound_count > 0:
        print_warning(
            f"Reverted {unbound_count} unbound rename(s) "
            f"已回滚 {unbound_count} 个未绑定改名:",
            1,
        )
        for renamed_basename, original_basename in unbound_sample:
            print_file_path(f"{renamed_basename} → {original_basename}", 2)

    # Delete the on-disk history file when no entries remain (clean run).
    rename_history.finalize()

    print_major_section_break()
    # Footer with fancy border
    print_final_completion(output_folder)

    # Ask for random user input before exit
    _ask_for_user_input_and_exit()


def cli() -> None:
    """Command line interface entry point 命令行界面入口点"""
    app()


def main() -> None:
    """Entry point for the application 应用程序入口点"""
    try:
        cli()
    except KeyboardInterrupt:
        print_error("\nOperation cancelled by user 操作被用户取消")
        _ask_for_user_input_and_exit()
    except Exception as e:
        print_error(f"Unexpected error 意外错误: {e}")
        _ask_for_user_input_and_exit()


if __name__ == "__main__":
    main()
