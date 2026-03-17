"""History command — display CLI invocation history."""

from typing import Optional

import typer

from llm_cli.core.history import clear_history, load_history
from llm_cli.ui import info, success, warning
from llm_cli.ui.tables import print_history_table


def history_command(
    limit: int = typer.Option(50, "--limit", "-n", help="Max entries to show"),
    clear: bool = typer.Option(False, "--clear", help="Delete all history"),
) -> None:
    """Show command history.

    Examples:
        llm history
        llm history -n 10              # Last 10 entries
        llm history --clear            # Clear all history
    """
    if clear:
        if clear_history():
            success("History cleared")
        else:
            info("No history to clear")
        return

    entries = load_history(limit=limit)
    if not entries:
        info("No command history yet. Run some commands first!")
        return

    print_history_table(entries)
