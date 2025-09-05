"""Rich-based utility functions for clean terminal output."""

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
from pathlib import Path

# Initialize console with better width handling and proper encoding support
console = Console(width=120, force_terminal=True)

# Global variables for tracking statistics
_start_time = None
_stats = {
    'total_archives': 0,
    'successful_extractions': 0,
    'failed_extractions': 0,
    'total_files_processed': 0,
    'errors': []
}

def init_statistics():
    """Initialize statistics tracking."""
    global _start_time, _stats
    _start_time = time.time()
    _stats = {
        'total_archives': 0,
        'successful_extractions': 0,
        'failed_extractions': 0,
        'total_files_processed': 0,
        'errors': []
    }

def update_stats(archives: int = 0, successful: int = 0, failed: int = 0, files: int = 0, error: str = None):
    """Update extraction statistics."""
    global _stats
    _stats['total_archives'] += archives
    _stats['successful_extractions'] += successful
    _stats['failed_extractions'] += failed
    _stats['total_files_processed'] += files
    if error:
        _stats['errors'].append(error)

def print_header(title: str):
    """Print a clean header with title."""
    console.print()
    console.print(f"[bold cyan]🚀 {title}[/bold cyan]")
    console.print("=" * 80, style="cyan")
    console.print()

def print_step(step_num: int, title: str):
    """Print a clean step header."""
    console.print()
    console.print(f"[bold cyan]Step {step_num}: {title}[/bold cyan]")
    console.print("-" * 60, style="cyan")

def print_success(message: str, indent: int = 0):
    """Print a success message with checkmark."""
    indent_str = "  " * indent
    console.print(f"{indent_str}[green]✓ {message}[/green]")

def print_info(message: str, indent: int = 0):
    """Print an info message."""
    indent_str = "  " * indent
    console.print(f"{indent_str}[blue]• {message}[/blue]")

def print_warning(message: str, indent: int = 0):
    """Print a warning message."""
    indent_str = "  " * indent
    console.print(f"{indent_str}[yellow]⚠ {message}[/yellow]")

def print_error(message: str, indent: int = 0):
    """Print an error message."""
    indent_str = "  " * indent
    console.print(f"{indent_str}[red]✗ {message}[/red]")
    update_stats(error=message)

def print_file_path(path: str, indent: int = 0):
    """Print a file path with proper styling."""
    indent_str = "  " * indent
    console.print(f"{indent_str}[dim cyan] {path}[/dim cyan]")

def print_section_divider():
    """Print a section divider."""
    console.print("─" * 60, style="dim")

def print_major_section_break():
    """Print a major section break."""
    console.print()

def print_minor_section_break():
    """Print a minor section break."""
    console.print()

def print_processing_separator():
    """Print a separator for processing items."""
    pass  # Simplified - no separator needed

def print_archive_group_summary(groups: List[Any]):
    """Print archive groups summary in a clean format."""
    if not groups:
        return
    
    console.print(f"[cyan]📋 Found {len(groups)} archive groups 找到 {len(groups)} 个档案组:[/cyan]")
    
    for i, group in enumerate(groups, 1):
        if group.isMultiPart:
            icon = "📚"
            group_type = "multipart 多部分"
        else:
            icon = "📄"
            group_type = "single 单一"
        file_count = len(group.files) if hasattr(group, 'files') else 0
        console.print(f"  {icon} [white]{i}.[/white] [bold]{group.name}[/bold] ({group_type}, {file_count} files 文件)")

def print_extraction_header(archive_name: str):
    """Print extraction header for an archive."""
    console.print(f"[yellow]🔧 Extracting 正在提取:[/yellow] [bold]{archive_name}[/bold]")

def print_nested_extraction_header(input_path: str, output_path: str, num_passwords: int, max_depth: int):
    """Print nested extraction process header."""
    console.print(f"[blue]📥 Input 输入:[/blue] [cyan]{input_path}[/cyan]")
    console.print(f"[blue]📤 Output 输出:[/blue] [cyan]{output_path}[/cyan]")
    console.print(f"[blue]🔑 Passwords available 可用密码:[/blue] [yellow]{num_passwords}[/yellow]")
    console.print(f"[blue]🔍 Max depth 最大深度:[/blue] [magenta]{max_depth}[/magenta]")

def print_extraction_process_header():
    """Print extraction process section header."""
    pass  # Simplified

def print_extracting_archive(filename: str, depth: int):
    """Print extracting archive message."""
    depth_indicator = "  " * depth
    console.print(f"    {depth_indicator}[cyan]📦 {filename} (depth {depth} 深度 {depth})[/cyan]")

def print_password_attempt(password: str, indent: int = 0):
    """Print password attempt message."""
    indent_str = "  " * indent
    display_pwd = "(empty 空)" if not password else password
    console.print(f"{indent_str}[blue]🔐 Trying password 尝试密码:[/blue] {display_pwd}")

def print_password_failed(password: str, indent: int = 0):
    """Print password failed message."""
    indent_str = "  " * indent
    display_pwd = "(empty 空)" if not password else password
    console.print(f"{indent_str}[red]❌ Wrong password 密码错误:[/red] {display_pwd}")

def print_password_success(password: str, indent: int = 0):
    """Print password success message."""
    indent_str = "  " * indent
    display_pwd = "(empty 空)" if not password else password
    console.print(f"{indent_str}[green]✅ Success with password 密码成功:[/green] {display_pwd}")

def print_extraction_summary(status: str, archives_extracted: int, final_files: int, errors: int):
    """Print extraction summary."""
    if status == "SUCCESS":
        status_color = "green"
        status_icon = "✅"
        status_text = "SUCCESS 成功"
    else:
        status_color = "red"
        status_icon = "❌"
        status_text = "FAILED 失败"
    
    console.print(f"[{status_color}]{status_icon} Status 状态:[/{status_color}] [{status_color}]{status_text}[/{status_color}]")
    console.print(f"[blue]📦 Archives extracted 提取档案:[/blue] {archives_extracted}")
    console.print(f"[green]📄 Final files 最终文件:[/green] {final_files}")
    if errors > 0:
        console.print(f"[red]⚠ Errors 错误:[/red] {errors}")

def print_final_completion(output_location: str):
    """Print final completion message with comprehensive statistics."""
    global _start_time, _stats
    
    if _start_time is None:
        elapsed_time = 0
    else:
        elapsed_time = time.time() - _start_time
    
    console.print()
    console.print("=" * 80, style="green")
    console.print("[bold green]🎉 EXTRACTION COMPLETED 提取完成[/bold green]")
    console.print("=" * 80, style="green")
    console.print()
    
    # Create summary table
    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Value", style="white", width=15)
    table.add_column("Details", style="dim", width=35)
    
    # Format time
    if elapsed_time >= 60:
        time_str = f"{elapsed_time // 60:.0f}m {elapsed_time % 60:.1f}s"
    else:
        time_str = f"{elapsed_time:.1f}s"
    
    table.add_row("⏱️  Time Elapsed 用时", time_str, "Total processing time 总处理时间")
    table.add_row("📦 Archives Processed 档案处理", str(_stats['total_archives']), f"{_stats['successful_extractions']} successful 成功, {_stats['failed_extractions']} failed 失败")
    table.add_row("📄 Files Extracted 提取文件", str(_stats['total_files_processed']), "Total files moved to output 移至输出的总文件")
    
    if _stats['errors']:
        table.add_row("❌ Errors 错误", str(len(_stats['errors'])), "Issues encountered 遇到的问题")
    
    table.add_row("📂 Output Location 输出位置", "", "")
    
    console.print(table)
    console.print(f"    [cyan]{output_location}[/cyan]")
    
    # Show errors if any
    if _stats['errors']:
        console.print()
        console.print("[red]Errors encountered 遇到的错误:[/red]")
        for i, error in enumerate(_stats['errors'][:5], 1):  # Show first 5 errors
            console.print(f"  {i}. [red]{error}[/red]")
        if len(_stats['errors']) > 5:
            console.print(f"  ... and {len(_stats['errors']) - 5} more errors 更多错误")
    
    console.print()
    console.print("[dim]Thank you for using Complex Unzip Tool v2! 感谢使用复杂解压工具v2![/dim]")

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
    """A simple spinner for long operations."""
    
    def __init__(self, message: str):
        self.message = message
        self.progress = None
        self.task = None
    
    def start(self):
        """Start the spinner."""
        self.progress = Progress(
            SpinnerColumn(style="cyan"),
            TextColumn("[blue]{task.description}[/blue]"),
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
    """Progress tracker for extraction operations."""
    
    def __init__(self, title: str = "Processing Archives"):
        self.title = title
        self.progress = None
        self.overall_task = None
        self.current_task = None
        self.total_groups = 0
        self.completed_groups = 0
        
    def start(self, total_groups: int):
        """Start the progress tracker."""
        self.total_groups = total_groups
        update_stats(archives=total_groups)
        
        self.progress = Progress(
            TextColumn("[cyan]{task.description}[/cyan]"),
            BarColumn(bar_width=40, style="green", complete_style="green"),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            expand=False
        )
        set_active_progress(self)
        self.progress.start()
        self.overall_task = self.progress.add_task(
            f"{self.title} ({total_groups} total)", 
            total=total_groups
        )
    
    def start_group(self, group_name: str, file_count: int = 0):
        """Start processing a new group."""
        task_desc = f"→ {group_name}"
        if file_count > 0:
            task_desc += f" ({file_count} files)"
        
        if self.current_task is not None:
            self.progress.remove_task(self.current_task)
        
        self.current_task = self.progress.add_task(task_desc, total=None)
    
    def complete_group(self, success: bool = True):
        """Mark current group as completed."""
        if self.current_task is not None:
            self.progress.remove_task(self.current_task)
            self.current_task = None
        
        self.completed_groups += 1
        if success:
            update_stats(successful=1)
        else:
            update_stats(failed=1)
            
        if self.overall_task is not None:
            self.progress.update(self.overall_task, completed=self.completed_groups)
    
    def stop(self):
        """Stop the progress tracker."""
        if self.progress:
            self.progress.stop()
            clear_active_progress()


class FileOperationProgress:
    """Progress tracker for file operations."""
    
    def __init__(self, operation: str = "Moving Files"):
        self.operation = operation
        self.progress = None
        self.task = None
        
    def start(self, total_files: int):
        """Start file operation progress."""
        update_stats(files=total_files)
        
        self.progress = Progress(
            TextColumn("[blue]{task.description}[/blue]"),
            BarColumn(bar_width=40, style="blue", complete_style="blue"),
            MofNCompleteColumn(),
            TextColumn("files"),
            console=console,
            expand=False
        )
        set_active_progress(self)
        self.progress.start()
        self.task = self.progress.add_task(self.operation, total=total_files)
    
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


def create_extraction_progress(title: str = "Processing Archives") -> ExtractionProgress:
    """Create a new extraction progress tracker."""
    return ExtractionProgress(title)


def create_file_operation_progress(operation: str = "Moving Files") -> FileOperationProgress:
    """Create a new file operation progress tracker."""
    return FileOperationProgress(operation)

def create_spinner(message: str) -> RichSpinner:
    """Create a new spinner with the given message."""
    return RichSpinner(message)

def print_remaining_groups_warning(groups: List[Any]):
    """Print warning about remaining unprocessed groups."""
    console.print()
    console.print("[yellow]⚠ Some archives could not be processed 某些档案无法处理:[/yellow]")
    
    for i, group in enumerate(groups, 1):
        group_name = group.name if hasattr(group, 'name') else str(group)
        group_type = "multipart 多部分" if getattr(group, 'isMultiPart', False) else "single 单一"
        file_count = len(getattr(group, 'files', []))
        
        console.print(f"  {i}. [red]{group_name}[/red] ({group_type}, {file_count} files 文件)")
    
    console.print()
    console.print("[yellow]Possible reasons 可能原因:[/yellow]")
    console.print("  • Corrupted archives 档案损坏")
    console.print("  • Missing passwords 缺少密码")
    console.print("  • Incomplete multipart archives 多部分档案不完整")
    console.print("  • Unsupported archive format 不支持的档案格式")

def print_all_processed_success():
    """Print success message when all archives are processed."""
    console.print("[green]✓ All archives processed successfully! 所有档案处理成功![/green]")

def print_separator():
    """Print a separator line."""
    console.print("─" * 60, style="dim")

def print_empty_line():
    """Print an empty line."""
    console.print()

def print_version(version: str):
    """Print version information."""
    console.print(f"[bold cyan]🚀 Complex Unzip Tool v2 {version} 复杂解压工具v2[/bold cyan]")

def print_general(message: str, indent: int = 0):
    """Print a general message."""
    indent_str = " " * indent
    console.print(f"{indent_str}{message}")

def print_error_summary(errors: List[str]):
    """Print error summary."""
    if not errors:
        return
    
    console.print()
    console.print("[red]❌ Errors encountered 遇到的错误:[/red]")
    for i, error in enumerate(errors[:10], 1):  # Show first 10 errors
        console.print(f"  {i}. [red]⚠ {error}[/red]")
    if len(errors) > 10:
        console.print(f"  ... and {len(errors) - 10} more errors 更多错误")
    console.print()
