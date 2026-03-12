"""Main Typer application setup."""

import typer

from llm_cli.commands import config, init, key, model, provider, team

app = typer.Typer(
    name="llm",
    help="CLI tool for managing LiteLLM Proxy Server",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Register sub-commands
app.add_typer(config.app, name="config", help="Manage configurations and environments")
app.add_typer(provider.app, name="provider", help="List supported providers and models")
app.add_typer(model.app, name="model", help="Manage models on LiteLLM Proxy")
app.add_typer(key.app, name="key", help="Manage virtual API keys")
app.add_typer(team.app, name="team", help="Manage teams and permissions")

# Direct command
app.command(name="init", help="Initialize or add new organization/environment")(init.init_command)


if __name__ == "__main__":
    app()
