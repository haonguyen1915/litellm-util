"""Key commands - Manage virtual API keys."""

from typing import Optional

import typer

from llm_cli.core.client import APIError, AuthenticationError, ConnectionError, LiteLLMClient
from llm_cli.core.context import ConfigurationError
from llm_cli.ui import confirm, error, fuzzy_select, select_from_list, success, text_input
from llm_cli.ui.console import console, print_detail, warning
from llm_cli.ui.tables import print_keys_table, print_proxy_models_table, print_teams_table
from llm_cli.utils.clipboard import copy_to_clipboard

app = typer.Typer(no_args_is_help=True)


def _get_client(org: str | None, env: str | None) -> LiteLLMClient:
    """Get API client with error handling."""
    try:
        return LiteLLMClient(org_override=org, env_override=env)
    except ConfigurationError as e:
        error(str(e))
        raise typer.Exit(2)


@app.command("list")
def list_keys(
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """List all virtual keys."""
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"

    try:
        keys = client.list_keys()
        print_keys_table(keys, context_name)
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        console.print(f"  URL: {client.base_url}", style="dim")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)


@app.command("create")
def create_key(
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Key alias/name"),
    team: Optional[str] = typer.Option(None, "--team", "-t", help="Team ID to assign"),
    budget: Optional[float] = typer.Option(None, "--budget", "-b", help="Monthly budget"),
    models: Optional[str] = typer.Option(
        None, "--models", "-m", help="Comma-separated list of allowed models"
    ),
    expires: Optional[str] = typer.Option(None, "--expires", help="Expiration date (YYYY-MM-DD)"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Create a new virtual key."""
    client = _get_client(org, env)

    # If alias not provided, prompt for it
    if not alias:
        alias = text_input("Key alias:")

    # Interactive team selection if not provided
    team_id = team
    if not team_id:
        if confirm("Assign to team? (default: Yes)", default=True):
            try:
                teams = client.list_teams()
                if teams:
                    # Show teams table first
                    context_name = f"{client.context.organization_id}/{client.context.environment}"
                    print_teams_table(teams, context_name)

                    # Fuzzy select team
                    team_map = {
                        f"{t.team_alias or t.team_id} ({t.team_id})": t.team_id
                        for t in teams
                    }
                    console.print("\n[dim]Type to search teams (tab to complete):[/dim]")
                    selection = fuzzy_select("Team:", list(team_map.keys()))
                    if selection and selection in team_map:
                        team_id = team_map[selection]
            except Exception:
                pass  # Continue without team

    # Interactive budget
    max_budget = budget
    budget_duration = None
    if max_budget is None:
        if confirm("Set budget limit? (default: Unlimited)", default=False):
            budget_str = text_input("Monthly budget ($):")
            if budget_str:
                try:
                    max_budget = float(budget_str)
                    budget_duration = "monthly"
                except ValueError:
                    warning("Invalid budget value, skipping")

    # Interactive model selection
    model_list = None
    if models:
        model_list = [m.strip() for m in models.split(",")]
    else:
        try:
            proxy_models = client.list_models()
            if proxy_models:
                model_names = [m.get("model_name", "") for m in proxy_models if m.get("model_name")]
                if model_names:
                    # Show deployed models table
                    context_name = f"{client.context.organization_id}/{client.context.environment}"
                    print_proxy_models_table(proxy_models, context_name)

                    # Fuzzy search loop for multi-select
                    selected_models: list[str] = []

                    while True:
                        remaining = [m for m in model_names if m not in selected_models]
                        if not remaining:
                            break

                        if not selected_models:
                            console.print(
                                "\n[dim]Enter = All Team Models | Type to search & restrict:[/dim]"
                            )
                        else:
                            console.print(
                                f"\n[dim]Selected: {', '.join(selected_models)}[/dim]"
                            )
                            console.print("[dim]Enter = Done | Type to add more:[/dim]")

                        pick = fuzzy_select("Model access:", remaining)

                        if not pick:
                            break

                        # Exact match
                        if pick in remaining:
                            selected_models.append(pick)
                            continue

                        # Partial match (typed text + Enter without Tab)
                        matches = [m for m in remaining if pick.lower() in m.lower()]
                        if len(matches) == 1:
                            selected_models.append(matches[0])
                            continue

                        break

                    if selected_models:
                        model_list = selected_models
        except Exception:
            pass  # Continue without model restriction

    # Interactive expiration
    expires_date = expires
    if not expires_date:
        if confirm("Set expiration? (default: Never)", default=False):
            expires_date = text_input("Expiration date (YYYY-MM-DD):")

    # Show summary and confirm before creating
    console.print("\n[bold]Key Summary:[/bold]")
    print_detail("Alias", alias or "(none)")
    print_detail("Team", team_id or "None")
    print_detail("Budget", f"${max_budget}/{budget_duration or 'month'}" if max_budget else "Unlimited")
    print_detail("Models", ", ".join(model_list) if model_list else "All models")
    print_detail("Expires", expires_date or "Never")
    console.print()

    if not confirm("Create this key?", default=True):
        raise typer.Exit(1)

    # Create the key
    try:
        result = client.create_key(
            key_alias=alias if alias else None,
            team_id=team_id,
            models=model_list,
            max_budget=max_budget,
            budget_duration=budget_duration,
            expires=expires_date,
        )

        key = result.get("key", result.get("token", ""))

        console.print()
        success("Virtual key created:")
        if alias:
            print_detail("Alias", alias)
        print_detail("Key", key)

        console.print()
        warning("Save this key! It won't be shown again.")

        # Try to copy to clipboard
        if copy_to_clipboard(key):
            console.print("  (Copied to clipboard)", style="dim")

    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"Failed to create key: {e.message}")
        raise typer.Exit(1)


@app.command("update")
def update_key(
    key_alias: Optional[str] = typer.Argument(None, help="Key alias to update"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New key alias/name"),
    team: Optional[str] = typer.Option(None, "--team", "-t", help="New team ID"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Update a virtual key (name, team)."""
    client = _get_client(org, env)

    try:
        keys = client.list_keys()
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)

    if not keys:
        error("No keys found")
        raise typer.Exit(1)

    # Select key if not provided
    selected_key = None
    if not key_alias:
        context_name = f"{client.context.organization_id}/{client.context.environment}"
        print_keys_table(keys, context_name)

        key_choices = [
            f"{k.key_alias or k.key_name or '-'} ({k.masked_key})" for k in keys
        ]
        console.print("\n[dim]Type to search keys (tab to complete):[/dim]")
        selection = fuzzy_select("Update key:", key_choices)
        if selection is None or selection not in key_choices:
            raise typer.Exit(1)

        for k in keys:
            if k.masked_key in selection:
                selected_key = k
                break
    else:
        for k in keys:
            if (k.key_alias and k.key_alias.lower() == key_alias.lower()) or (
                k.key_name and k.key_name.lower() == key_alias.lower()
            ):
                selected_key = k
                break

        if not selected_key:
            error(f"Key '{key_alias}' not found")
            raise typer.Exit(5)

    if not selected_key:
        error("Key not found")
        raise typer.Exit(5)

    display_name = selected_key.key_alias or selected_key.key_name or selected_key.masked_key

    # Show current info
    console.print("\nCurrent key info:")
    print_detail("Alias", selected_key.key_alias or selected_key.key_name or "-")
    print_detail("Key", selected_key.masked_key)
    print_detail("Team", selected_key.team_id or "-")
    console.print()

    # Interactive if no flags provided
    if not any([name, team]):
        update_choices = ["Update name", "Update team"]
        selection = select_from_list("What would you like to update?", update_choices)

        if selection is None:
            raise typer.Exit(1)

        if "name" in selection:
            name = text_input("New alias:", default=selected_key.key_alias or "")

        elif "team" in selection:
            try:
                teams = client.list_teams()
                if teams:
                    context_name = f"{client.context.organization_id}/{client.context.environment}"
                    print_teams_table(teams, context_name)

                    team_map = {
                        f"{t.team_alias or t.team_id} ({t.team_id})": t.team_id
                        for t in teams
                    }
                    console.print("\n[dim]Type to search teams (tab to complete):[/dim]")
                    pick = fuzzy_select("Team:", list(team_map.keys()))
                    if pick and pick in team_map:
                        team = team_map[pick]
            except Exception:
                team = text_input("Team ID:")

    if not name and not team:
        warning("Nothing to update")
        raise typer.Exit(1)

    # Confirm
    console.print("\n[bold]Update Summary:[/bold]")
    print_detail("Key", display_name)
    if name:
        print_detail("New Name", name)
    if team:
        print_detail("New Team", team)
    console.print()

    if not confirm("Apply update?", default=True):
        raise typer.Exit(1)

    try:
        client.update_key(
            key=selected_key.token,
            key_alias=name,
            team_id=team,
        )
        success(f"Key '{display_name}' updated")
        if name:
            print_detail("Name", name)
        if team:
            print_detail("Team", team)
    except APIError as e:
        error(f"Failed to update key: {e.message}")
        raise typer.Exit(1)


@app.command("delete")
def delete_key(
    key_alias: Optional[str] = typer.Argument(None, help="Key alias to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Delete a virtual key."""
    client = _get_client(org, env)

    try:
        keys = client.list_keys()
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)

    if not keys:
        error("No keys found")
        raise typer.Exit(1)

    # Select key if not provided
    selected_key = None
    if not key_alias:
        # Show keys table first
        context_name = f"{client.context.organization_id}/{client.context.environment}"
        print_keys_table(keys, context_name)

        # Fuzzy select key
        key_choices = [
            f"{k.key_alias or k.key_name or '-'} ({k.masked_key})" for k in keys
        ]
        console.print("\n[dim]Type to search keys (tab to complete):[/dim]")
        selection = fuzzy_select("Delete key:", key_choices)
        if selection is None or selection not in key_choices:
            raise typer.Exit(1)

        for k in keys:
            if k.masked_key in selection:
                selected_key = k
                break
    else:
        # Find key by alias
        for k in keys:
            if (k.key_alias and k.key_alias.lower() == key_alias.lower()) or (k.key_name and k.key_name.lower() == key_alias.lower()):
                selected_key = k
                break

        if not selected_key:
            error(f"Key '{key_alias}' not found")
            raise typer.Exit(5)

    if not selected_key:
        error("Key not found")
        raise typer.Exit(5)

    # Confirm deletion
    display_name = selected_key.key_alias or selected_key.key_name or selected_key.masked_key
    if not yes:
        if not confirm(f"Are you sure you want to delete '{display_name}'?"):
            raise typer.Exit(1)

    try:
        client.delete_key(selected_key.token)
        success(f"Key '{display_name}' deleted")
    except APIError as e:
        error(f"Failed to delete key: {e.message}")
        raise typer.Exit(1)
