"""Model commands - Manage models on LiteLLM Proxy."""

from typing import Optional

import typer

from llm_cli.core.client import APIError, AuthenticationError, ConnectionError, LiteLLMClient
from llm_cli.core.context import ConfigurationError
from llm_cli.providers import get_all_providers, get_provider, get_provider_ids
from llm_cli.ui import confirm, error, select_from_list, success, text_input
from llm_cli.ui.console import console, print_detail
from llm_cli.ui.tables import print_proxy_models_table

app = typer.Typer(no_args_is_help=True)


def _get_client(org: str | None, env: str | None) -> LiteLLMClient:
    """Get API client with error handling."""
    try:
        return LiteLLMClient(org_override=org, env_override=env)
    except ConfigurationError as e:
        error(str(e))
        raise typer.Exit(2)


@app.command("list")
def list_models(
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """List all models on the proxy."""
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"

    try:
        models = client.list_models()
        print_proxy_models_table(models, context_name)
    except ConnectionError as e:
        error(f"Cannot connect to LiteLLM Proxy")
        console.print(f"  URL: {client.base_url}", style="dim")
        console.print("\n  Please check:", style="dim")
        console.print("  - Is the proxy server running?", style="dim")
        console.print("  - Is the URL correct?", style="dim")
        console.print("\n  Run 'llm config current' to see current configuration", style="dim")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        console.print("  Master key may be invalid or expired", style="dim")
        console.print("\n  Run 'llm init' to update credentials", style="dim")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)


@app.command("create")
def create_model(
    provider_name: Optional[str] = typer.Option(None, "--provider", "-p", help="Provider name"),
    model_id: Optional[str] = typer.Option(None, "--model", "-m", help="Model ID"),
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="Model alias/display name"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API key"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Create a new model on the proxy."""
    # If all required params provided, run non-interactively
    if provider_name and model_id and alias:
        _create_model_non_interactive(provider_name, model_id, alias, api_key, org, env)
    else:
        create_model_interactive(
            prefill_provider=provider_name,
            prefill_model=model_id,
            prefill_alias=alias,
            prefill_api_key=api_key,
            org_override=org,
            env_override=env,
        )


def create_model_interactive(
    prefill_provider: str | None = None,
    prefill_model: str | None = None,
    prefill_alias: str | None = None,
    prefill_api_key: str | None = None,
    org_override: str | None = None,
    env_override: str | None = None,
) -> None:
    """Interactive model creation flow."""
    client = _get_client(org_override, env_override)

    # Select provider
    if prefill_provider:
        provider = get_provider(prefill_provider)
        if not provider:
            error(f"Provider '{prefill_provider}' not found")
            raise typer.Exit(5)
    else:
        provider_ids = get_provider_ids()
        selection = select_from_list("Select provider:", provider_ids)
        if selection is None:
            raise typer.Exit(1)
        provider = get_provider(selection)
        if not provider:
            raise typer.Exit(1)

    # Select model
    if prefill_model:
        model_id = prefill_model
    else:
        model_ids = [m.id for m in provider.models]
        if not model_ids:
            # Custom model input for providers without predefined models
            model_id = text_input("Enter model ID:")
            if not model_id:
                error("Model ID is required")
                raise typer.Exit(5)
        else:
            model_selection = select_from_list("Select model:", model_ids)
            if model_selection is None:
                raise typer.Exit(1)
            model_id = model_selection

    # Get alias
    if prefill_alias:
        alias = prefill_alias
    else:
        # Suggest a default alias based on model ID
        default_alias = model_id.split("/")[-1].split(":")[0]
        alias = text_input("Model alias (display name):", default=default_alias)
        if not alias:
            alias = default_alias

    # Get API key
    if prefill_api_key:
        api_key = prefill_api_key
    elif provider.requires_api_key:
        env_hint = f" (or press Enter to use {provider.env_var})" if provider.env_var else ""
        api_key = text_input(f"API Key{env_hint}:", password=True)
    else:
        api_key = None

    # Build litellm_params
    litellm_params = {"model": model_id}
    if api_key:
        litellm_params["api_key"] = api_key

    # Create model
    try:
        result = client.create_model(
            model_name=alias,
            litellm_params=litellm_params,
        )
        success(f"Model '{alias}' created successfully")
        print_detail("Provider", provider.id)
        print_detail("Model", model_id)
    except ConnectionError as e:
        error(f"Cannot connect to LiteLLM Proxy: {e}")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"Failed to create model: {e.message}")
        raise typer.Exit(1)


def _create_model_non_interactive(
    provider_name: str,
    model_id: str,
    alias: str,
    api_key: str | None,
    org: str | None,
    env: str | None,
) -> None:
    """Non-interactive model creation."""
    client = _get_client(org, env)

    provider = get_provider(provider_name)
    if not provider:
        error(f"Provider '{provider_name}' not found")
        raise typer.Exit(5)

    litellm_params = {"model": model_id}
    if api_key:
        litellm_params["api_key"] = api_key

    try:
        client.create_model(
            model_name=alias,
            litellm_params=litellm_params,
        )
        success(f"Model '{alias}' created successfully")
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"Failed to create model: {e.message}")
        raise typer.Exit(1)


@app.command("delete")
def delete_model(
    model_name: Optional[str] = typer.Argument(None, help="Model name to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Delete a model from the proxy."""
    client = _get_client(org, env)

    try:
        models = client.list_models()
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)

    if not models:
        error("No models found on proxy")
        raise typer.Exit(1)

    # Select model if not provided
    if not model_name:
        model_choices = [
            f"{m.get('model_name', '')} ({m.get('litellm_params', {}).get('model', '')})"
            for m in models
        ]
        selection = select_from_list("Select model to delete:", model_choices)
        if selection is None:
            raise typer.Exit(1)

        # Find the model
        for m in models:
            if m.get("model_name", "") in selection:
                model_name = m.get("model_name")
                model_id = m.get("model_info", {}).get("id")
                break
    else:
        # Find model by name
        model_id = None
        for m in models:
            if m.get("model_name") == model_name:
                model_id = m.get("model_info", {}).get("id")
                break

        if not model_id:
            error(f"Model '{model_name}' not found")
            raise typer.Exit(5)

    # Confirm deletion
    if not yes:
        if not confirm(f"Are you sure you want to delete '{model_name}'?"):
            raise typer.Exit(1)

    try:
        client.delete_model(model_id)
        success(f"Model '{model_name}' deleted")
    except APIError as e:
        error(f"Failed to delete model: {e.message}")
        raise typer.Exit(1)
