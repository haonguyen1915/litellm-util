"""Provider commands - List supported providers and models."""

from typing import Optional

import typer

from llm_cli.providers import get_all_providers, get_provider, get_provider_ids
from llm_cli.ui import error, select_from_list
from llm_cli.ui.console import console
from llm_cli.ui.tables import print_model_details, print_models_table, print_providers_table
from llm_cli.utils.clipboard import copy_to_clipboard

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_providers() -> None:
    """List all supported LLM providers."""
    providers = get_all_providers()
    print_providers_table(providers)


@app.command("models")
def list_models(
    provider_name: Optional[str] = typer.Argument(None, help="Provider name"),
    no_interactive: bool = typer.Option(
        False, "--no-interactive", "-n", help="Disable interactive mode"
    ),
    capability: Optional[str] = typer.Option(
        None, "--capability", "-c", help="Filter by capability (e.g., vision, tools)"
    ),
) -> None:
    """List models for a provider with interactive selection."""
    # If no provider specified, show provider selection
    if not provider_name:
        if no_interactive:
            error("Provider name is required in non-interactive mode")
            raise typer.Exit(5)

        provider_ids = get_provider_ids()
        selection = select_from_list("Select provider:", provider_ids)

        if selection is None:
            raise typer.Exit(1)

        provider_name = selection

    # Get provider info
    provider = get_provider(provider_name)
    if not provider:
        error(f"Provider '{provider_name}' not found")
        console.print("\nAvailable providers:", style="dim")
        for pid in get_provider_ids():
            console.print(f"  - {pid}", style="dim")
        raise typer.Exit(5)

    # Filter models by capability if specified
    models = provider.models
    if capability:
        models = [m for m in models if capability.lower() in [c.lower() for c in m.capabilities]]
        if not models:
            error(f"No models found with capability '{capability}'")
            raise typer.Exit(1)

    # Print models table
    print_models_table(models, title=f"{provider.name} Models")

    # Non-interactive mode: just print and exit
    if no_interactive:
        return

    # Interactive mode: allow model selection
    model_ids = [m.id for m in models]
    model_ids.append("Back / Quit")

    selection = select_from_list(
        "Select model (or press Enter to skip):",
        model_ids,
    )

    if selection is None or selection == "Back / Quit":
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
        "Add to proxy (llm model create)",
        "Copy model ID to clipboard",
        "Back",
    ]

    selection = select_from_list("What would you like to do?", actions)

    if selection is None or selection == "Back":
        return

    if "Add to proxy" in selection:
        # Import here to avoid circular imports
        from llm_cli.commands.model import create_model_interactive

        create_model_interactive(prefill_provider=model.provider, prefill_model=model.id)

    elif "Copy model ID" in selection:
        if copy_to_clipboard(model.id):
            from llm_cli.ui import success

            success(f"Copied '{model.id}' to clipboard")
        else:
            from llm_cli.ui import warning

            warning(f"Could not copy to clipboard. Model ID: {model.id}")
