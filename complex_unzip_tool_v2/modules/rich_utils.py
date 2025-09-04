"""Rich-based utility functions for beautiful terminal output."""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.columns import Columns
from rich.align import Align
from rich import box
from typing import List, Dict, Any, Optional
import time
import os
from pathlib import Path

# Initialize console with better width handling
console = Console(width=120, force_terminal=True)

def print_header(title: str):
    """Print a beautiful header with title."""
    console.print(Panel(
        Text(title, style="bold bright_blue"),
        box=box.DOUBLE_EDGE,
        width=80,
        style="bright_blue",
        padding=(1, 2)
    ))

def print_step(step_num: int, title: str):
    """Print a step header with enhanced visual separation."""
    # Create gradient-like effect with emojis
    step_icons = ["🚀", "🔑", "📂", "📋", "⚙️", "🔧", "🔗", "📊", "🎯"]
    icon = step_icons[step_num - 1] if step_num <= len(step_icons) else "📌"
    
    # Add visual separation before each step
    print_major_section_break()
    
    console.print(Panel(
        f"{icon} [bold]Step {step_num}[/bold]: {title}",
        box=box.ROUNDED,
        width=78,
        style="cyan",
        padding=(0, 1)
    ))

def print_success(message: str, indent: int = 0):
    """Print a success message with checkmark."""
    indent_str = "   " * indent  # Use 3 spaces per indent level for consistency
    console.print(f"{indent_str}[bold green]✅[/bold green] [green]{message}[/green]")

def print_info(message: str, indent: int = 0):
    """Print an info message."""
    indent_str = "   " * indent  # Use 3 spaces per indent level for consistency
    console.print(f"{indent_str}[bold blue]📍[/bold blue] [bright_blue]{message}[/bright_blue]")

def print_warning(message: str, indent: int = 0):
    """Print a warning message."""
    indent_str = "   " * indent  # Use 3 spaces per indent level for consistency
    console.print(f"{indent_str}[bold yellow]⚠️[/bold yellow] [yellow]{message}[/yellow]")

def print_error(message: str, indent: int = 0):
    """Print an error message."""
    indent_str = "   " * indent  # Use 3 spaces per indent level for consistency
    console.print(f"{indent_str}[bold red]❌[/bold red] [red]{message}[/red]")

def print_file_path(path: str, indent: int = 0):
    """Print a file path with proper styling."""
    indent_str = "   " * indent  # Use 3 spaces per indent level for consistency
    console.print(f"{indent_str}[dim cyan]📂 {path}[/dim cyan]")

def print_section_divider():
    """Print a section divider."""
    console.print("─" * 70, style="dim bright_black")

def print_major_section_break():
    """Print a major section break with enhanced visual separation."""
    console.print()
    console.print("═" * 80, style="bold bright_blue")
    console.print()

def print_minor_section_break():
    """Print a minor section break for subsections."""
    console.print()
    console.print("─" * 60, style="dim cyan")
    console.print()

def print_processing_separator():
    """Print a separator for individual processing items."""
    console.print("┈" * 50, style="dim white")

def print_archive_group_summary(groups: List[Any]):
    """Print archive groups summary using rich tree structure and tables."""
    if not groups:
        return
    
    # Create groups tree
    tree = Tree(
        "[bold bright_blue]📂 Archive Groups Structure / 档案组结构[/bold bright_blue]",
        style="bold bright_blue"
    )
    
    for i, group in enumerate(groups, 1):
        # Determine group type and icon
        group_type = "📚 Multipart" if group.isMultiPart else "📄 Single"
        group_type_cn = "多部分" if group.isMultiPart else "单一"
        
        # Create group branch
        group_name = f"[bold white]{group.name}[/bold white]"
        group_info = f"[dim cyan]({len(group.files)} files / {len(group.files)} 个文件)[/dim cyan]"
        group_branch = tree.add(f"{group_type} {group_name} {group_info}")
        
        # Add main archive info
        if hasattr(group, 'mainArchiveFile') and group.mainArchiveFile:
            main_file = os.path.basename(group.mainArchiveFile)
            size_info = ""
            try:
                if os.path.exists(group.mainArchiveFile):
                    size_mb = os.path.getsize(group.mainArchiveFile) / (1024 * 1024)
                    size_info = f" [dim]({size_mb:.1f} MB)[/dim]"
            except:
                pass
            
            main_branch = group_branch.add(f"[green]🎯 Main Archive / 主档案:[/green] [bold]{main_file}[/bold]{size_info}")
        
        # Add files list (show first 5, then summarize)
        if hasattr(group, 'files') and group.files:
            files_branch = group_branch.add(f"[cyan]📄 Files / 文件 ({len(group.files)}):[/cyan]")
            
            # Show first 5 files
            for j, file_path in enumerate(group.files[:5], 1):
                file_name = os.path.basename(str(file_path))
                size_info = ""
                try:
                    if os.path.exists(str(file_path)):
                        size_mb = os.path.getsize(str(file_path)) / (1024 * 1024)
                        size_info = f" [dim]({size_mb:.1f} MB)[/dim]"
                except:
                    pass
                
                files_branch.add(f"[dim white]{j}. {file_name}[/dim white]{size_info}")
            
            # Show summary for remaining files
            if len(group.files) > 5:
                remaining = len(group.files) - 5
                files_branch.add(f"[dim yellow]... and {remaining} more files / 还有 {remaining} 个文件[/dim yellow]")
    
    console.print(tree)
    console.print()

def print_extraction_header(archive_name: str):
    """Print extraction header for an archive with Chinese text and enhanced separation."""
    print_minor_section_break()
    console.print(Panel(
        f"[bold bright_yellow]🎯 正在提取 Extracting: [/bold bright_yellow][white]{archive_name}[/white]",
        box=box.HEAVY,
        style="yellow",
        width=72,
        padding=(0, 1)
    ))

def print_nested_extraction_header(input_path: str, output_path: str, num_passwords: int, max_depth: int):
    """Print nested extraction process header with enhanced Chinese text."""
    console.print(Panel(
        Text("🚀 开始嵌套档案提取 Starting nested archive extraction", style="bold bright_green"),
        box=box.DOUBLE_EDGE,
        width=80,
        style="bright_green",
        padding=(1, 2)
    ))
    
    # Create an info table with proper indentation
    info_table = Table(show_header=False, box=None, padding=(0, 1), width=76)
    info_table.add_column("", style="bold bright_blue", width=25)
    info_table.add_column("", style="white", width=50)
    
    info_table.add_row("📁 输入 Input:", f"[cyan]{input_path}[/cyan]")
    info_table.add_row("📂 输出 Output:", f"[cyan]{output_path}[/cyan]")
    info_table.add_row("🔑 密码数量 Passwords:", f"[yellow]{num_passwords}[/yellow]")
    info_table.add_row("📊 最大深度 Max depth:", f"[magenta]{max_depth}[/magenta]")
    
    # Add proper indentation
    console.print(" ")
    console.print(info_table)
    console.print(" ")

def print_extraction_process_header():
    """Print extraction process section header with Chinese text."""
    console.print(Panel(
        "[bold bright_cyan]⚙️ 提取过程 Extraction Process[/bold bright_cyan]",
        box=box.HEAVY,
        style="cyan",
        width=78,
        padding=(0, 1)
    ))

def print_extracting_archive(filename: str, depth: int):
    """Print extracting archive message with Chinese text and processing separator."""
    print_processing_separator()
    depth_color = "green" if depth == 0 else "yellow" if depth < 3 else "red"
    console.print(Panel(
        f"[bold {depth_color}]📦 正在提取 Extracting (深度 depth {depth}): [/bold {depth_color}][white]{filename}[/white]",
        box=box.ROUNDED,
        style=depth_color,
        width=74,
        padding=(0, 1)
    ))

def print_password_attempt(password: str, indent: int = 0):
    """Print password attempt message with Chinese text."""
    indent_str = "   " * indent  # Use 3 spaces per indent level for consistency
    display_pwd = "[dim](空密码 empty)[/dim]" if not password else f"[bright_cyan]{password}[/bright_cyan]"
    console.print(f"{indent_str}[bright_blue]🔓[/bright_blue] [blue]尝试密码 Trying password:[/blue] {display_pwd}")

def print_password_failed(password: str, indent: int = 0):
    """Print password failed message with Chinese text."""
    indent_str = "   " * indent  # Use 3 spaces per indent level for consistency
    display_pwd = "[dim](空密码 empty)[/dim]" if not password else f"[red]{password}[/red]"
    console.print(f"{indent_str}[bold red]❌[/bold red] [red]密码错误 Wrong password:[/red] {display_pwd}")

def print_password_success(password: str, indent: int = 0):
    """Print password success message with Chinese text."""
    indent_str = "   " * indent  # Use 3 spaces per indent level for consistency
    display_pwd = "[dim](空密码 empty)[/dim]" if not password else f"[bright_green]{password}[/bright_green]"
    console.print(f"{indent_str}[bold green]✅[/bold green] [green]密码成功 Extraction successful with password:[/green] {display_pwd}")

def print_extraction_summary(status: str, archives_extracted: int, final_files: int, errors: int):
    """Print final extraction summary with Chinese text and colors."""
    # Create status styling and Chinese text
    if status == "SUCCESS":
        status_style = "bold bright_green"
        status_text = "成功 SUCCESS"
        status_icon = "✅"
    else:
        status_style = "bold bright_red"
        status_text = "失败 FAILED"
        status_icon = "❌"
    
    # Create summary table
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column("", style="bold", width=25)
    summary_table.add_column("", style="")
    
    summary_table.add_row(
        f"[{status_style}]{status_icon} 状态 Status:[/{status_style}]", 
        f"[{status_style}]{status_text}[/{status_style}]"
    )
    summary_table.add_row(
        "[bright_blue]📦 提取档案 Archives:[/bright_blue]", 
        f"[bright_blue]{archives_extracted}[/bright_blue]"
    )
    summary_table.add_row(
        "[bright_green]📄 最终文件 Final files:[/bright_green]", 
        f"[bright_green]{final_files}[/bright_green]"
    )
    summary_table.add_row(
        "[bright_red]⚠️ 错误 Errors:[/bright_red]", 
        f"[bright_red]{errors}[/bright_red]"
    )
    
    console.print(Panel(
        summary_table,
        title="[bold bright_white]📋 提取摘要 Extraction Summary[/bold bright_white]",
        box=box.DOUBLE_EDGE,
        width=80,
        style=status_style.split()[-1],  # Get just the color
        padding=(1, 2)
    ))

def print_final_completion(output_location: str):
    """Print enhanced final completion message with statistics."""
    console.print()
    
    # Create completion statistics
    stats_text = f"""
[bold bright_green]🎉 Extraction Process Completed! / 提取过程完成！[/bold bright_green]

[bold bright_blue]📊 Summary / 摘要:[/bold bright_blue]
• All archives have been processed / 所有档案都已处理
• Files extracted to output directory / 文件已提取到输出目录
• Temporary files cleaned up / 临时文件已清理
• Original archives removed / 原始档案已删除

[bold bright_cyan]📂 Output Location / 输出位置:[/bold bright_cyan]
[bright_cyan]{output_location}[/bright_cyan]
    """
    
    console.print(Panel(
        stats_text.strip(),
        title="[bold bright_yellow]🏆 Mission Accomplished / 任务完成[/bold bright_yellow]",
        title_align="center",
        box=box.DOUBLE_EDGE,
        width=100,
        style="bright_green",
        padding=(1, 3)
    ))
    
    # Add a final celebratory message
    celebration_text = Text("✨ Thank you for using Complex Unzip Tool v2! / 感谢使用复杂解压工具v2！ by Rozx✨", style="bold bright_magenta")
    console.print(Align.center(celebration_text))
    console.print()

# Simple global variable to track active progress display
_active_progress_display = None

def set_active_progress(progress_instance):
    """Set the currently active progress display, stopping any previous one."""
    global _active_progress_display
    if _active_progress_display and hasattr(_active_progress_display, 'progress') and _active_progress_display.progress:
        try:
            _active_progress_display.progress.stop()
        except:
            pass
    _active_progress_display = progress_instance

def clear_active_progress():
    """Clear the currently active progress display."""
    global _active_progress_display
    _active_progress_display = None


class RichSpinner:
    """A rich-based spinner for long operations with Chinese text."""
    
    def __init__(self, message: str):
        self.message = message
        self.progress = None
        self.task = None
    
    def start(self):
        """Start the spinner with colorful display."""
        self.progress = Progress(
            SpinnerColumn(style="bright_cyan"),
            TextColumn("[bold bright_blue]{task.description}[/bold bright_blue]"),
            console=console,
            transient=True
        )
        set_active_progress(self)
        self.progress.start()
        self.task = self.progress.add_task(self.message, total=None)
    
    def stop(self):
        """Stop the spinner."""
        if self.progress:
            self.progress.stop()
            clear_active_progress()


class ExtractionProgress:
    """Advanced progress tracker for extraction operations."""
    
    def __init__(self, title: str = "Extraction Progress / 提取进度"):
        self.title = title
        self.progress = None
        self.overall_task = None
        self.current_task = None
        self.total_groups = 0
        self.completed_groups = 0
        
    def start(self, total_groups: int):
        """Start the progress tracker."""
        self.total_groups = total_groups
        self.progress = Progress(
            SpinnerColumn(style="bright_green"),
            TextColumn("[bold bright_blue]{task.description}[/bold bright_blue]"),
            BarColumn(bar_width=None, style="bright_green", complete_style="green"),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            expand=True
        )
        set_active_progress(self)
        self.progress.start()
        self.overall_task = self.progress.add_task(
            f"[bold]{self.title}[/bold]", 
            total=total_groups
        )
    
    def start_group(self, group_name: str, file_count: int = 0):
        """Start processing a new group."""
        task_desc = f"Processing / 正在处理: [cyan]{group_name}[/cyan]"
        if file_count > 0:
            task_desc += f" ([yellow]{file_count} files[/yellow])"
        
        if self.current_task is not None:
            self.progress.remove_task(self.current_task)
        
        self.current_task = self.progress.add_task(
            task_desc,
            total=None
        )
    
    def complete_group(self):
        """Mark current group as completed."""
        if self.current_task is not None:
            self.progress.remove_task(self.current_task)
            self.current_task = None
        
        self.completed_groups += 1
        if self.overall_task is not None:
            self.progress.update(self.overall_task, completed=self.completed_groups)
    
    def stop(self):
        """Stop the progress tracker."""
        if self.progress:
            self.progress.stop()
            clear_active_progress()


class FileOperationProgress:
    """Progress tracker for file operations like moving, copying."""
    
    def __init__(self, operation: str = "File Operation"):
        self.operation = operation
        self.progress = None
        self.task = None
        
    def start(self, total_files: int):
        """Start file operation progress."""
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}[/bold blue]"),
            BarColumn(bar_width=None, style="bright_blue", complete_style="blue"),
            MofNCompleteColumn(),
            TextColumn("files"),
            TimeElapsedColumn(),
            console=console,
            expand=True
        )
        set_active_progress(self)
        self.progress.start()
        self.task = self.progress.add_task(
            f"[bold]{self.operation} / 文件操作[/bold]",
            total=total_files
        )
    
    def update(self, advance: int = 1, description: Optional[str] = None):
        """Update progress."""
        if self.task is not None:
            self.progress.update(self.task, advance=advance)
            if description:
                self.progress.update(self.task, description=description)
    
    def stop(self):
        """Stop the progress tracker."""
        if self.progress:
            self.progress.stop()
            clear_active_progress()


def create_extraction_progress(title: str = "Extraction Progress / 提取进度") -> ExtractionProgress:
    """Create a new extraction progress tracker."""
    return ExtractionProgress(title)


def create_file_operation_progress(operation: str = "Processing Files") -> FileOperationProgress:
    """Create a new file operation progress tracker."""
    return FileOperationProgress(operation)

def create_spinner(message: str) -> RichSpinner:
    """Create a new colorful spinner with the given message."""
    return RichSpinner(message)

def print_remaining_groups_warning(groups: List[Any]):
    """Print warning about remaining unprocessed groups with enhanced table."""
    console.print()
    console.print(Panel(
        "[bold bright_yellow]⚠️ Unprocessed Groups / 未处理的组[/bold bright_yellow]",
        box=box.HEAVY,
        style="yellow",
        title="[bold red]Issues Found[/bold red]",
        title_align="center",
        width=100,
        padding=(1, 2)
    ))
    
    # Create a detailed warning table
    warning_table = Table(show_header=True, box=box.ROUNDED, width=90)
    warning_table.add_column("#", style="bold red", width=5, justify="center")
    warning_table.add_column("Group Name / 组名", style="bold white", width=30)
    warning_table.add_column("Type / 类型", style="cyan", width=15, justify="center")
    warning_table.add_column("Files / 文件数", style="yellow", width=12, justify="center")
    warning_table.add_column("Status / 状态", style="bold red", width=15, justify="center")
    warning_table.add_column("Main Archive / 主档案", style="dim", width=25)
    
    for i, group in enumerate(groups, 1):
        group_name = group.name if hasattr(group, 'name') else str(group)
        group_type = "Multipart / 多部分" if getattr(group, 'isMultiPart', False) else "Single / 单一"
        file_count = len(getattr(group, 'files', []))
        main_archive = ""
        
        if hasattr(group, 'mainArchiveFile') and group.mainArchiveFile:
            main_archive = os.path.basename(group.mainArchiveFile)
        
        warning_table.add_row(
            f"{i}",
            f"{group_name}",
            f"{group_type}",
            f"{file_count}",
            "❌ Failed / 失败",
            f"[dim]{main_archive}[/dim]"
        )
    
    console.print(Align.center(warning_table))
    
    # Add suggestions panel
    suggestions_text = """
[bold bright_yellow]💡 Suggestions / 建议:[/bold bright_yellow]
• Check if archives are corrupted / 检查档案是否损坏
• Verify passwords in passwords.txt / 验证 passwords.txt 中的密码
• Ensure all parts are present for multipart archives / 确保多部分档案的所有部分都存在
• Check file permissions / 检查文件权限
    """
    
    console.print(Panel(
        suggestions_text.strip(),
        box=box.ROUNDED,
        style="bright_yellow",
        title="[bold]Troubleshooting / 故障排除[/bold]",
        title_align="left",
        width=100,
        padding=(1, 2)
    ))
    console.print()

def print_all_processed_success():
    """Print success message when all archives are processed with Chinese celebration."""
    console.print(Panel(
        "[bold bright_green]🎊 所有档案处理成功! All archives processed successfully! 🎊[/bold bright_green]",
        box=box.DOUBLE_EDGE,
        style="bright_green",
        width=76,
        padding=(1, 2)
    ))

def print_separator():
    """Print a beautiful separator line 打印美丽的分隔线"""
    console.print("   " + "─" * 70, style="bright_blue")

def print_empty_line():
    """Print an empty line 打印空行"""
    console.print()

def print_version(version: str):
    """Print version information with rich formatting 打印版本信息"""
    console.print(f"[bold bright_cyan]📦 Complex Unzip Tool v2 {version} 复杂解压工具v2[/bold bright_cyan]")

def print_general(message: str, indent: int = 0):
    """Print a general message with optional indentation 打印一般消息"""
    indent_str = " " * indent
    console.print(f"{indent_str}{message}")

def print_error_summary(errors: List[str]):
    """Print a beautiful error summary panel with Chinese text."""
    if not errors:
        return
    
    console.print()
    console.print(Panel(
        "[bold red]❌ 遇到的错误 Errors Encountered[/bold red]",
        box=box.HEAVY,
        style="red",
        width=80,
        padding=(0, 1)
    ))
    
    # Create error table
    error_table = Table(show_header=False, box=None, width=76)
    error_table.add_column("#", style="bold red", width=4)
    error_table.add_column("Error", style="red")
    
    for i, error in enumerate(errors, 1):
        # Truncate long error messages but keep them readable
        display_error = error if len(error) <= 70 else error[:67] + "..."
        error_table.add_row(f"{i}.", display_error)
    
    console.print(error_table)
    console.print()
