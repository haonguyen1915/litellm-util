"""Admin commands - Enterprise proxy administration."""

import secrets
from typing import Optional

import typer

from llm_cli.core.client import APIError, AuthenticationError, ConnectionError, LiteLLMClient
from llm_cli.core.config import load_config, save_config
from llm_cli.core.context import ConfigurationError, get_current_context
from llm_cli.ui import confirm, error, success, text_input, warning
from llm_cli.ui.console import console, print_detail
from llm_cli.utils.clipboard import copy_to_clipboard

app = typer.Typer(no_args_is_help=True)


def _get_client(org: str | None, env: str | None) -> LiteLLMClient:
    """Get API client with error handling."""
    try:
        return LiteLLMClient(org_override=org, env_override=env)
    except ConfigurationError as e:
        error(str(e))
        raise typer.Exit(2)


@app.command("rotate-key")
def rotate_key(
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Rotate the proxy master key (Enterprise feature).

    Examples:
        llm admin rotate-key
        llm admin rotate-key -o PREP -e prod
    """
    client = _get_client(org, env)
    ctx = client.context

    console.print(
        f"\nCurrent context: [highlight]{ctx.organization_id}[/highlight] / "
        f"[highlight]{ctx.environment}[/highlight] ({ctx.url})\n"
    )

    # Prompt for new key
    new_key = text_input("New master key (leave blank to auto-generate):")
    if new_key is None:
        raise typer.Exit(1)

    if not new_key:
        new_key = f"sk-{secrets.token_urlsafe(32)}"
        console.print(f"  Generated key: [highlight]{new_key}[/highlight]\n")

    if not new_key.startswith("sk-"):
        error("Master key must start with 'sk-'")
        raise typer.Exit(2)

    # Warning and confirmation
    warning(
        "This will rotate the master key and re-encrypt all model API keys in the database."
    )
    if not confirm("Are you sure?"):
        raise typer.Exit(1)

    # Call API
    console.print("\nRotating master key...")
    try:
        client.rotate_master_key(new_key)
    except AuthenticationError:
        error("Authentication failed. Current master key may be invalid.")
        raise typer.Exit(2)
    except ConnectionError as e:
        error(str(e))
        raise typer.Exit(2)
    except APIError as e:
        if e.status_code == 403 or "enterprise" in e.message.lower():
            error("This is an Enterprise feature. Check your LiteLLM license.")
        else:
            error(f"API error: {e.message}")
        raise typer.Exit(2)

    success("Master key rotated successfully")
    console.print(f"  New key: [highlight]{new_key}[/highlight]\n")

    # Offer to update local config
    if not confirm("Update local config with new key?", default=True):
        raise typer.Exit(0)

    config = load_config()
    org_config = config.organizations.get(ctx.organization_id)
    if org_config:
        env_config = org_config.environments.get(ctx.environment)
        if env_config:
            env_config.master_key = new_key
            save_config(config)
            success("Config updated")

            if copy_to_clipboard(new_key):
                console.print("  (New key copied to clipboard)", style="dim")
            return

    error("Could not find current environment in config to update.")
    raise typer.Exit(2)
