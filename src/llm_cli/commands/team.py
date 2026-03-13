"""Team commands - Manage teams and permissions."""

from typing import Optional

import typer

from llm_cli.core.client import APIError, AuthenticationError, ConnectionError, LiteLLMClient
from llm_cli.core.context import ConfigurationError
from llm_cli.ui import confirm, error, fuzzy_select, select_from_list, select_multiple, success, text_input
from llm_cli.ui.console import console, print_detail, warning
from llm_cli.ui.tables import print_proxy_models_table, print_teams_table

app = typer.Typer(no_args_is_help=True)


def _get_client(org: str | None, env: str | None) -> LiteLLMClient:
    """Get API client with error handling."""
    try:
        return LiteLLMClient(org_override=org, env_override=env)
    except ConfigurationError as e:
        error(str(e))
        raise typer.Exit(2)


@app.command("list")
def list_teams(
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """List all teams."""
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"

    try:
        teams = client.list_teams()
        print_teams_table(teams, context_name)
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
def create_team(
    team_id: Optional[str] = typer.Option(None, "--id", help="Team ID (slug)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Team name"),
    models: Optional[str] = typer.Option(
        None, "--models", "-m", help="Comma-separated list of allowed models"
    ),
    budget: Optional[float] = typer.Option(None, "--budget", "-b", help="Monthly budget"),
    reset_monthly: bool = typer.Option(
        False, "--reset-monthly", help="Auto-reset budget monthly"
    ),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Create a new team."""
    client = _get_client(org, env)

    # Interactive prompts for missing values
    if not team_id:
        team_id = text_input("Team ID (slug):")
        if not team_id:
            error("Team ID is required")
            raise typer.Exit(5)

    team_id = team_id.lower().replace(" ", "-")

    if not name:
        name = text_input("Team Name:", default=team_id.replace("-", " ").title())

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

                    console.print("\nSelect models for team (or skip for all models):")
                    model_names_with_all = ["All models"] + model_names
                    selected = select_multiple("Choose models:", model_names_with_all)
                    if selected and "All models" not in selected:
                        model_list = selected
        except Exception:
            pass  # Continue without model restriction

    # Interactive budget
    max_budget = budget
    budget_duration = None
    if max_budget is None:
        if confirm("Set monthly budget?", default=False):
            budget_str = text_input("Monthly budget ($):")
            if budget_str:
                try:
                    max_budget = float(budget_str)
                except ValueError:
                    warning("Invalid budget value, skipping")

    if max_budget and (reset_monthly or confirm("Enable auto-reset monthly?", default=True)):
        budget_duration = "monthly"

    # Create the team
    try:
        result = client.create_team(
            team_alias=name,
            team_id=team_id,
            models=model_list,
            max_budget=max_budget,
            budget_duration=budget_duration,
        )

        success("Team created:")
        print_detail("ID", team_id)
        print_detail("Name", name)
        if model_list:
            print_detail("Models", ", ".join(model_list))
        else:
            print_detail("Models", "All models")
        if max_budget:
            print_detail("Budget", f"${max_budget}/{budget_duration or 'month'} (auto-reset)")

    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"Failed to create team: {e.message}")
        raise typer.Exit(1)


@app.command("update")
def update_team(
    team_id: Optional[str] = typer.Argument(None, help="Team ID to update"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New team name"),
    add_models: Optional[str] = typer.Option(
        None, "--add-models", help="Comma-separated models to add"
    ),
    remove_models: Optional[str] = typer.Option(
        None, "--remove-models", help="Comma-separated models to remove"
    ),
    budget: Optional[float] = typer.Option(None, "--budget", "-b", help="New monthly budget"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Update an existing team."""
    client = _get_client(org, env)

    # Get teams list for selection
    try:
        teams = client.list_teams()
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)

    if not teams:
        error("No teams found")
        raise typer.Exit(1)

    # Select team if not provided
    selected_team = None
    if not team_id:
        # Show teams table first
        context_name = f"{client.context.organization_id}/{client.context.environment}"
        print_teams_table(teams, context_name)

        # Fuzzy select team
        team_choices = [t.team_id for t in teams]
        console.print("\n[dim]Type to search teams (tab to complete):[/dim]")
        selection = fuzzy_select("Update team:", team_choices)
        if selection is None or selection not in team_choices:
            raise typer.Exit(1)

        for t in teams:
            if t.team_id == selection:
                selected_team = t
                team_id = t.team_id
                break
    else:
        for t in teams:
            if t.team_id == team_id:
                selected_team = t
                break

        if not selected_team:
            error(f"Team '{team_id}' not found")
            raise typer.Exit(5)

    # Show current info
    if selected_team:
        console.print("\nCurrent team info:")
        print_detail("Name", selected_team.team_alias or "-")
        print_detail("Models", ", ".join(selected_team.models) if selected_team.models else "All models")
        if selected_team.max_budget:
            print_detail("Budget", f"${selected_team.max_budget}/{selected_team.budget_duration or 'month'}")
        console.print()

    # Interactive update if no flags provided
    if not any([name, add_models, remove_models, budget is not None]):
        update_choices = [
            "Update name",
            "Add models",
            "Remove models",
            "Update budget",
        ]
        selection = select_from_list("What would you like to update?", update_choices)

        if selection is None:
            raise typer.Exit(1)

        if "name" in selection:
            name = text_input("New name:", default=selected_team.team_alias or "")

        elif "Add models" in selection:
            try:
                proxy_models = client.list_models()
                current_models = set(selected_team.models) if selected_team.models else set()
                available = [
                    m.get("model_name", "")
                    for m in proxy_models
                    if m.get("model_name") and m.get("model_name") not in current_models
                ]
                if available:
                    # Show available models table
                    available_proxy = [
                        m for m in proxy_models
                        if m.get("model_name") and m.get("model_name") not in current_models
                    ]
                    if available_proxy:
                        print_proxy_models_table(available_proxy, "Available to add")

                    selected = select_multiple("Select models to add:", available)
                    if selected:
                        add_models = ",".join(selected)
                else:
                    warning("No additional models available")
            except Exception:
                add_models = text_input("Models to add (comma-separated):")

        elif "Remove models" in selection:
            if selected_team.models:
                selected = select_multiple("Select models to remove:", selected_team.models)
                if selected:
                    remove_models = ",".join(selected)
            else:
                warning("Team has access to all models, nothing to remove")

        elif "budget" in selection:
            budget_str = text_input("New monthly budget ($):")
            if budget_str:
                try:
                    budget = float(budget_str)
                except ValueError:
                    warning("Invalid budget value")

    # Build update data
    new_models = None
    if add_models or remove_models:
        current_models = set(selected_team.models) if selected_team.models else set()

        if add_models:
            for m in add_models.split(","):
                current_models.add(m.strip())

        if remove_models:
            for m in remove_models.split(","):
                current_models.discard(m.strip())

        new_models = list(current_models) if current_models else None

    # Update team
    try:
        client.update_team(
            team_id=team_id,
            team_alias=name,
            models=new_models,
            max_budget=budget,
            budget_duration="monthly" if budget else None,
        )
        success(f"Team '{team_id}' updated")

        if name:
            print_detail("Name", name)
        if new_models:
            print_detail("Models", ", ".join(new_models))
        if budget:
            print_detail("Budget", f"${budget}/monthly")

    except APIError as e:
        error(f"Failed to update team: {e.message}")
        raise typer.Exit(1)


@app.command("delete")
def delete_team(
    team_id: Optional[str] = typer.Argument(None, help="Team ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Delete a team."""
    client = _get_client(org, env)

    try:
        teams = client.list_teams()
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)

    if not teams:
        error("No teams found")
        raise typer.Exit(1)

    # Select team if not provided
    selected_team = None
    if not team_id:
        # Show teams table first
        context_name = f"{client.context.organization_id}/{client.context.environment}"
        print_teams_table(teams, context_name)

        # Fuzzy select team
        team_choices = [t.team_id for t in teams]
        console.print("\n[dim]Type to search teams (tab to complete):[/dim]")
        selection = fuzzy_select("Delete team:", team_choices)
        if selection is None or selection not in team_choices:
            raise typer.Exit(1)

        for t in teams:
            if t.team_id == selection:
                selected_team = t
                team_id = t.team_id
                break
    else:
        for t in teams:
            if t.team_id == team_id:
                selected_team = t
                break

        if not selected_team:
            error(f"Team '{team_id}' not found")
            raise typer.Exit(5)

    # Confirm deletion
    if not yes:
        warning("This will also revoke all keys assigned to this team!")
        console.print()
        if not confirm(f"Are you sure you want to delete '{team_id}'?"):
            raise typer.Exit(1)

    try:
        client.delete_team(team_id)
        success(f"Team '{team_id}' deleted")
    except APIError as e:
        error(f"Failed to delete team: {e.message}")
        raise typer.Exit(1)
