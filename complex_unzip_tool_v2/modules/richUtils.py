"""Rich-based utility functions for beautiful terminal output."""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich import box
from typing import List, Dict, Any
import time

# Initialize console
console = Console()

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
    """Print a step header."""
    # Create gradient-like effect with emojis
    step_icons = ["🚀", "🔑", "📂", "📋", "⚙️", "🔧", "🔗", "📊", "🎯"]
    icon = step_icons[step_num - 1] if step_num <= len(step_icons) else "📌"
    
    console.print(Panel(
        f"{icon} [bold]Step {step_num}[/bold]: {title}",
        box=box.ROUNDED,
        width=78,
        style="cyan",
        padding=(0, 1)
    ))

def print_success(message: str, indent: int = 3):
    """Print a success message with checkmark."""
    indent_str = " " * indent
    console.print(f"{indent_str}[bold green]✅[/bold green] [green]{message}[/green]")

def print_info(message: str, indent: int = 3):
    """Print an info message."""
    indent_str = " " * indent
    console.print(f"{indent_str}[bold blue]📍[/bold blue] [bright_blue]{message}[/bright_blue]")

def print_warning(message: str, indent: int = 3):
    """Print a warning message."""
    indent_str = " " * indent
    console.print(f"{indent_str}[bold yellow]⚠️[/bold yellow] [yellow]{message}[/yellow]")

def print_error(message: str, indent: int = 3):
    """Print an error message."""
    indent_str = " " * indent
    console.print(f"{indent_str}[bold red]❌[/bold red] [red]{message}[/red]")

def print_file_path(path: str, indent: int = 6):
    """Print a file path with proper styling."""
    indent_str = " " * indent
    console.print(f"{indent_str}[dim cyan]📂 {path}[/dim cyan]")

def print_section_divider():
    """Print a section divider."""
    console.print("─" * 70, style="dim bright_black")

def print_archive_group_summary(groups: List[Any]):
    """Print archive groups summary in a nice table format with Chinese text."""
    if not groups:
        return
    
    console.print()
    console.print(Panel(
        "[bold bright_cyan]📦 Archive Groups Summary 档案组摘要[/bold bright_cyan]",
        box=box.ROUNDED,
        style="cyan",
        width=76
    ))
    
    for i, group in enumerate(groups, 1):
        # Create a table for each group
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("", style="bold blue", width=8)
        table.add_column("", style="white")
        
        # Group header
        table.add_row(
            f"[bold bright_blue]🗂️ 组{i}[/bold bright_blue]:", 
            f"[bold white]{group.name}[/bold white]"
        )
        
        # Files count
        table.add_row(
            "[cyan]📄 文件:[/cyan]", 
            f"[yellow]{len(group.files)} files[/yellow]"
        )
        
        # Show files (limit to 3)
        files_to_show = group.files[:3] if hasattr(group, 'files') else []
        for j, file_path in enumerate(files_to_show, 1):
            file_name = file_path.name if hasattr(file_path, 'name') else str(file_path).split('/')[-1].split('\\')[-1]
            table.add_row(
                f"   {j}.", 
                f"[dim white]{file_name}[/dim white]"
            )
        
        if len(group.files) > 3:
            remaining = len(group.files) - 3
            table.add_row(
                "   ...", 
                f"[dim yellow]还有 {remaining} 个文件 (and {remaining} more files)[/dim yellow]"
            )
        
        # Main archive
        if hasattr(group, 'mainArchiveFile') and group.mainArchiveFile:
            main_file = group.mainArchiveFile.split('/')[-1].split('\\')[-1]
            table.add_row(
                "[green]🎯 主档案:[/green]", 
                f"[bold green]{main_file}[/bold green]"
            )
        
        console.print(table)
        
        if i < len(groups):
            console.print("[dim]" + "─" * 70 + "[/dim]")
    
    console.print()

def print_extraction_header(archive_name: str):
    """Print extraction header for an archive with Chinese text."""
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
    
    # Create an info table
    info_table = Table(show_header=False, box=None, padding=(0, 1))
    info_table.add_column("", style="bold bright_blue", width=20)
    info_table.add_column("", style="white")
    
    info_table.add_row("📁 输入 Input:", f"[cyan]{input_path}[/cyan]")
    info_table.add_row("📂 输出 Output:", f"[cyan]{output_path}[/cyan]")
    info_table.add_row("🔑 密码数量 Passwords:", f"[yellow]{num_passwords}[/yellow]")
    info_table.add_row("📊 最大深度 Max depth:", f"[magenta]{max_depth}[/magenta]")
    
    console.print(info_table)

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
    """Print extracting archive message with Chinese text."""
    depth_color = "green" if depth == 0 else "yellow" if depth < 3 else "red"
    console.print(Panel(
        f"[bold {depth_color}]📦 正在提取 Extracting (深度 depth {depth}): [/bold {depth_color}][white]{filename}[/white]",
        box=box.ROUNDED,
        style=depth_color,
        width=74,
        padding=(0, 1)
    ))

def print_password_attempt(password: str, indent: int = 2):
    """Print password attempt message with Chinese text."""
    indent_str = " " * indent
    display_pwd = "[dim](空密码 empty)[/dim]" if not password else f"[bright_cyan]{password}[/bright_cyan]"
    console.print(f"{indent_str}[bright_blue]🔓[/bright_blue] [blue]尝试密码 Trying password:[/blue] {display_pwd}")

def print_password_failed(password: str, indent: int = 2):
    """Print password failed message with Chinese text."""
    indent_str = " " * indent
    display_pwd = "[dim](空密码 empty)[/dim]" if not password else f"[red]{password}[/red]"
    console.print(f"{indent_str}[bold red]❌[/bold red] [red]密码错误 Wrong password:[/red] {display_pwd}")

def print_password_success(password: str, indent: int = 2):
    """Print password success message with Chinese text."""
    indent_str = " " * indent
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
    """Print final completion message with Chinese text and celebration."""
    # Create a celebration table
    completion_table = Table(show_header=False, box=None, padding=(0, 2))
    completion_table.add_column("", style="bold", width=25)
    completion_table.add_column("", style="")
    
    completion_table.add_row(
        "[bold bright_green]🎉 状态 Status:[/bold bright_green]", 
        "[bold bright_green]提取完成! Extraction completed![/bold bright_green]"
    )
    completion_table.add_row(
        "[bright_blue]📂 输出位置 Output:[/bright_blue]", 
        f"[bright_cyan]{output_location}[/bright_cyan]"
    )
    
    console.print(Panel(
        completion_table,
        title="[bold bright_yellow]🏆 任务完成 Mission Accomplished[/bold bright_yellow]",
        box=box.DOUBLE_EDGE,
        width=80,
        style="bright_green",
        padding=(1, 2)
    ))

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
        self.progress.start()
        self.task = self.progress.add_task(self.message, total=None)
    
    def stop(self):
        """Stop the spinner."""
        if self.progress:
            self.progress.stop()

def create_spinner(message: str) -> RichSpinner:
    """Create a new colorful spinner with the given message."""
    return RichSpinner(message)

def print_remaining_groups_warning(groups: List[Any]):
    """Print warning about remaining unprocessed groups with Chinese text."""
    console.print(Panel(
        "[bold bright_yellow]⚠️ 剩余未处理组 Remaining unprocessed groups[/bold bright_yellow]",
        box=box.HEAVY,
        style="yellow",
        width=76,
        padding=(0, 1)
    ))
    
    # Create a warning table
    warning_table = Table(show_header=False, box=box.SIMPLE, width=70)
    warning_table.add_column("#", style="dim", width=5)
    warning_table.add_column("Group Name", style="red")
    warning_table.add_column("Status", style="bold red", width=10)
    
    for i, group in enumerate(groups, 1):
        group_name = group.name if hasattr(group, 'name') else str(group)
        warning_table.add_row(
            f"{i}.", 
            f"{group_name}", 
            "❌ 失败"
        )
    
    console.print(warning_table)

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
