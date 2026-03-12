"""Config commands - Manage configurations and environments."""

from typing import Optional

import typer

from llm_cli.core.config import config_exists, load_config, save_config
from llm_cli.core.context import ConfigurationError, get_current_context, set_current_context
from llm_cli.ui import error, select_from_list, success
from llm_cli.ui.console import console, print_detail
from llm_cli.ui.tables import print_config_table

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_configs() -> None:
    """List all organizations and environments."""
    config = load_config()

    if not config.organizations:
        error("No configurations found. Run 'llm init' to set up.")
        raise typer.Exit(2)

    print_config_table(config.organizations)

    if config.default:
        console.print(
            f"\nCurrent: [highlight]{config.default.organization}[/highlight] / "
            f"[highlight]{config.default.environment}[/highlight]"
        )


@app.command("use")
def use_config(
    org: Optional[str] = typer.Argument(None, help="Organization ID"),
    env: Optional[str] = typer.Argument(None, help="Environment name"),
) -> None:
    """Switch to a different organization/environment."""
    config = load_config()

    if not config.organizations:
        error("No configurations found. Run 'llm init' to set up.")
        raise typer.Exit(2)

    # If both provided, use directly
    if org and env:
        try:
            set_current_context(config, org, env)
            save_config(config)
            success(f"Switched to {org} / {env}")
            return
        except ConfigurationError as e:
            error(str(e))
            raise typer.Exit(2)

    # Interactive selection
    org_choices = [f"{oid} ({o.name})" for oid, o in config.organizations.items()]

    org_selection = select_from_list("Select organization:", org_choices)
    if org_selection is None:
        raise typer.Exit(1)

    # Extract org_id
    selected_org_id = None
    for oid in config.organizations:
        if oid in org_selection:
            selected_org_id = oid
            break

    if not selected_org_id:
        error("Invalid selection")
        raise typer.Exit(1)

    selected_org = config.organizations[selected_org_id]

    # Select environment
    env_choices = [
        f"{name} ({env.url})" for name, env in selected_org.environments.items()
    ]

    env_selection = select_from_list("Select environment:", env_choices)
    if env_selection is None:
        raise typer.Exit(1)

    # Extract env name
    selected_env = None
    for name in selected_org.environments:
        if name in env_selection:
            selected_env = name
            break

    if not selected_env:
        error("Invalid selection")
        raise typer.Exit(1)

    set_current_context(config, selected_org_id, selected_env)
    save_config(config)
    success(f"Switched to {selected_org_id} / {selected_env}")


@app.command("current")
def current_config() -> None:
    """Show current active configuration."""
    try:
        ctx = get_current_context()
        console.print()
        print_detail("Organization", f"{ctx.organization_id} ({ctx.organization_name})")
        print_detail("Environment", ctx.environment)
        print_detail("URL", ctx.url)
        console.print()
    except ConfigurationError as e:
        error(str(e))
        raise typer.Exit(2)
