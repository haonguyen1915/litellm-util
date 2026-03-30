"""Main Typer application setup."""

import sys

import typer

from llm_cli.commands import admin, config, history, init, key, model, provider, team, usage
from llm_cli.core.history import record_command

app = typer.Typer(
    name="llm",
    help="CLI tool for managing LiteLLM Proxy Server",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context) -> None:
    """Record every CLI invocation to history."""
    args = sys.argv[1:]
    if not args:
        return

    # Skip recording the "history" command itself
    if args[0] == "history":
        return

    # Commands with interactive flows record themselves with resolved args
    _SELF_RECORDING = {
        ("model", "create"),
        ("model", "delete"),
        ("provider", "models"),
    }
    cmd_tuple = tuple(args[:2]) if len(args) >= 2 else ()
    if cmd_tuple in _SELF_RECORDING:
        return

    try:
        record_command(args)
    except Exception:
        # Never let history recording break the CLI
        pass


# Register sub-commands
app.add_typer(admin.app, name="admin", help="Enterprise proxy administration")
app.add_typer(config.app, name="config", help="Manage configurations and environments")
app.add_typer(provider.app, name="provider", help="List supported providers and models")
app.add_typer(model.app, name="model", help="Manage models on LiteLLM Proxy")
app.add_typer(key.app, name="key", help="Manage virtual API keys")
app.add_typer(team.app, name="team", help="Manage teams and permissions")
app.add_typer(usage.app, name="usage", help="View spend and usage statistics")

# Direct commands
app.command(name="init", help="Initialize or add new organization/environment")(init.init_command)
app.command(name="history", help="Show command history")(history.history_command)


def main() -> None:
    """CLI entry point with Ctrl+C handling."""
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
