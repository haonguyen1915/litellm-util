"""Rich console setup and helper functions."""

from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red bold",
        "highlight": "cyan bold",
        "dim": "dim",
    }
)

console = Console(theme=custom_theme)


def success(message: str) -> None:
    """Print success message with checkmark."""
    console.print(f"✓ {message}", style="success")


def error(message: str) -> None:
    """Print error message with X mark."""
    console.print(f"✗ {message}", style="error")


def warning(message: str) -> None:
    """Print warning message."""
    console.print(f"⚠️  {message}", style="warning")


def info(message: str) -> None:
    """Print info message."""
    console.print(f"ℹ {message}", style="info")


def print_header(text: str) -> None:
    """Print a header line."""
    console.print(f"\n[bold]{text}[/bold]")


def print_detail(label: str, value: str) -> None:
    """Print a label-value detail line."""
    console.print(f"  {label}: [highlight]{value}[/highlight]")
