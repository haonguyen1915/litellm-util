"""Provider commands - List providers and models supported by LiteLLM."""

from enum import Enum
from typing import Optional

import typer

from llm_cli.core.client import APIError, AuthenticationError, ConnectionError, LiteLLMClient
from llm_cli.core.context import ConfigurationError
from llm_cli.models.provider import ModelInfo
from llm_cli.ui import error, fuzzy_select, select_from_list, success, warning
from llm_cli.ui.console import console
from llm_cli.ui.tables import print_model_details, print_models_table, print_providers_table
from llm_cli.utils.clipboard import copy_to_clipboard

app = typer.Typer(no_args_is_help=True)


class SortField(str, Enum):
    name = "name"
    price = "price"
    context = "context"


def _get_client(org: str | None, env: str | None) -> LiteLLMClient:
    """Get API client with error handling."""
    try:
        return LiteLLMClient(org_override=org, env_override=env)
    except ConfigurationError as e:
        error(str(e))
        raise typer.Exit(2)


def _filter_models(models: list[ModelInfo], search: str | None) -> list[ModelInfo]:
    """Filter models by search keyword (case-insensitive contains)."""
    if not search:
        return models
    keyword = search.lower()
    return [m for m in models if keyword in m.id.lower()]


def _sort_models(models: list[ModelInfo], sort: SortField) -> list[ModelInfo]:
    """Sort models by field."""
    if sort == SortField.name:
        return sorted(models, key=lambda m: m.id)
    elif sort == SortField.price:
        return sorted(models, key=lambda m: m.input_price)
    elif sort == SortField.context:
        return sorted(models, key=lambda m: m.context_window, reverse=True)
    return models


@app.command("list")
def list_providers(
    search: Optional[str] = typer.Option(
        None, "--search", "-s", help="Filter providers by keyword"
    ),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """List all providers supported by LiteLLM (from proxy /model_cost).

    Examples:
        llm provider list
        llm provider list -s openai
        llm provider list -s anthropic
    """
    client = _get_client(org, env)

    try:
        # Get all supported providers from /model_cost
        supported = client.list_supported_models()
        supported_ids = {p.id for p in supported}

        # Get deployed providers to mark status
        deployed = client.list_providers()
        deployed_map = {p.id: p for p in deployed}

        # Update descriptions to show deployment status
        for provider in supported:
            if provider.id in deployed_map:
                deployed_count = len(deployed_map[provider.id].models)
                provider.description = (
                    f"{len(provider.models)} supported, {deployed_count} deployed"
                )

        # Add deployed providers not in supported list (e.g. non-chat providers)
        for dp in deployed:
            if dp.id not in supported_ids:
                dp.description = f"{len(dp.models)} deployed (custom)"
                supported.append(dp)

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

    # Apply search filter
    if search:
        keyword = search.lower()
        supported = [p for p in supported if keyword in p.id.lower() or keyword in p.name.lower()]
        if not supported:
            error(f"No providers matching '{search}'")
            raise typer.Exit(1)

    if not supported:
        error("No providers found")
        raise typer.Exit(1)

    print_providers_table(supported)
    context_name = f"{client.context.organization_id}/{client.context.environment}"
    console.print(f"\nSource: {context_name}", style="dim")


@app.command("models")
def list_models(
    provider_name: Optional[str] = typer.Argument(None, help="Provider name"),
    search: Optional[str] = typer.Option(
        None, "--search", "-s", help="Filter models by keyword (contains)"
    ),
    sort: SortField = typer.Option(
        SortField.name, "--sort", help="Sort by: name, price, context"
    ),
    capability: Optional[str] = typer.Option(
        None, "--capability", "-c", help="Filter by capability (e.g., vision, tools)"
    ),
    no_interactive: bool = typer.Option(
        False, "--no-interactive", "-n", help="Disable interactive mode"
    ),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """List all models supported by LiteLLM for a provider.

    Examples:
        llm provider models                             # Interactive provider selection
        llm provider models openai                      # List OpenAI models
        llm provider models anthropic -s sonnet         # Search Anthropic models
        llm provider models openai --sort price         # Sort by price
        llm provider models openai -c vision -n         # Vision models, non-interactive
    """
    client = _get_client(org, env)

    try:
        supported = client.list_supported_models()
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)

    if not supported:
        error("No providers found")
        raise typer.Exit(1)

    provider_ids = [p.id for p in supported]

    # If no provider specified, show provider selection
    if not provider_name:
        if no_interactive:
            error("Provider name is required in non-interactive mode")
            console.print("\nAvailable providers:", style="dim")
            for pid in provider_ids:
                console.print(f"  - {pid}", style="dim")
            raise typer.Exit(5)

        # Use fuzzy search for provider selection (76+ providers)
        console.print("[dim]Type to search providers (tab to complete):[/dim]")
        selection = fuzzy_select("Provider:", provider_ids)
        if selection is None or selection not in provider_ids:
            raise typer.Exit(1)
        provider_name = selection

    # Find provider
    provider = next((p for p in supported if p.id == provider_name), None)
    if not provider:
        error(f"Provider '{provider_name}' not found")
        console.print("\nAvailable providers:", style="dim")
        for pid in provider_ids:
            console.print(f"  - {pid}", style="dim")
        raise typer.Exit(5)

    # Apply filters
    models = provider.models

    if capability:
        models = [m for m in models if capability.lower() in [c.lower() for c in m.capabilities]]
        if not models:
            error(f"No models found with capability '{capability}'")
            raise typer.Exit(1)

    models = _filter_models(models, search)
    if not models:
        error(f"No models matching '{search}'")
        raise typer.Exit(1)

    models = _sort_models(models, sort)

    # Build title
    title = f"{provider.name} Models ({len(models)} models)"
    if search:
        title += f" [search: {search}]"

    # Print full models table
    print_models_table(models, title=title)

    # Non-interactive mode: just print and exit
    if no_interactive:
        return

    # Interactive: type to select a model
    model_ids = [m.id for m in models]
    console.print("\n[dim]Type to search models (tab to complete, enter to select):[/dim]")
    selection = fuzzy_select("Model:", model_ids)
    if selection is None or selection not in model_ids:
        return

    # Find selected model
    selected_model = next((m for m in models if m.id == selection), None)
    if not selected_model:
        return

    # Show model details
    console.print()
    print_model_details(selected_model)

    # Show action menu
    _show_model_actions(selected_model)


def _show_model_actions(model) -> None:
    """Show action menu for a selected model."""
    console.print()

    actions = [
        "Copy model ID to clipboard",
        "Back",
    ]

    selection = select_from_list("What would you like to do?", actions)

    if selection is None or selection == "Back":
        return

    if "Copy model ID" in selection:
        if copy_to_clipboard(model.id):
            success(f"Copied '{model.id}' to clipboard")
        else:
            warning(f"Could not copy to clipboard. Model ID: {model.id}")