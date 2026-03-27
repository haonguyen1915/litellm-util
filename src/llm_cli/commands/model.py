"""Model commands - Manage models on LiteLLM Proxy."""

from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from llm_cli.core.client import APIError, AuthenticationError, ConnectionError, LiteLLMClient
from llm_cli.core.context import ConfigurationError
from llm_cli.ui import confirm, error, fuzzy_select, success, text_input, warning
from llm_cli.ui.console import console, info, print_detail
from llm_cli.ui.tables import print_models_table, print_proxy_models_table

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
    """List all models on the proxy.

    Examples:
        llm model list
        llm model list -o PREP -e dev
    """
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"

    try:
        models = client.list_models()
        print_proxy_models_table(models, context_name)
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
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
    input_cost: Optional[float] = typer.Option(None, "--input-cost", help="Input price per 1M tokens ($)"),
    output_cost: Optional[float] = typer.Option(None, "--output-cost", help="Output price per 1M tokens ($)"),
    replace: bool = typer.Option(False, "--replace", "-r", help="Replace existing model if it already exists"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Create a new model on the proxy.

    Examples:
        llm model create                                                    # Interactive
        llm model create -p openai -m gpt-4o -a my-gpt4o -k sk-xxx
        llm model create -p openai -m gpt-4o -a my-gpt4o -k sk-xxx --input-cost 2.50 --output-cost 10.00
        llm model create -p anthropic -m claude-sonnet-4-20250514 -a claude-sonnet -k sk-ant-xxx
        llm model create -p azure -m gpt-4o -a azure-gpt4o -k xxx
        llm model create -p gemini -m gemini-2.5-pro -a gemini-pro -k AIza-xxx
        llm model create -p groq -m llama-3.3-70b-versatile -a llama70b -k gsk-xxx
        llm model create --replace -p openai -m gpt-4o -a my-gpt4o -k sk-xxx  # Replace existing
    """
    # If all required params provided, run non-interactively
    if provider_name and model_id and alias:
        _create_model_non_interactive(
            provider_name, model_id, alias, api_key, input_cost, output_cost, org, env,
            replace=replace,
        )
    else:
        create_model_interactive(
            prefill_provider=provider_name,
            prefill_model=model_id,
            prefill_alias=alias,
            prefill_api_key=api_key,
            prefill_input_cost=input_cost,
            prefill_output_cost=output_cost,
            org_override=org,
            env_override=env,
            replace=replace,
        )


def _build_model_info(
    input_cost: float | None,
    output_cost: float | None,
) -> dict | None:
    """Build model_info dict from per-1M-token prices."""
    if input_cost is None and output_cost is None:
        return None
    info: dict = {}
    if input_cost is not None:
        info["input_cost_per_token"] = input_cost / 1_000_000
    if output_cost is not None:
        info["output_cost_per_token"] = output_cost / 1_000_000
    return info


def create_model_interactive(
    prefill_provider: str | None = None,
    prefill_model: str | None = None,
    prefill_alias: str | None = None,
    prefill_api_key: str | None = None,
    prefill_input_cost: float | None = None,
    prefill_output_cost: float | None = None,
    org_override: str | None = None,
    env_override: str | None = None,
    replace: bool = False,
) -> None:
    """Interactive model creation flow."""
    client = _get_client(org_override, env_override)

    # Fetch all supported models from LiteLLM
    try:
        all_providers = client.list_supported_models()
    except Exception:
        all_providers = []

    provider_ids = [p.id for p in all_providers]

    # Select provider
    if prefill_provider:
        provider = next((p for p in all_providers if p.id == prefill_provider), None)
        if not provider:
            error(f"Provider '{prefill_provider}' not found")
            raise typer.Exit(5)
    else:
        if not provider_ids:
            error("Could not fetch provider list")
            raise typer.Exit(1)

        console.print("[dim]Type to search providers (tab to complete):[/dim]")
        selection = fuzzy_select("Provider:", provider_ids)
        if selection is None or selection not in provider_ids:
            raise typer.Exit(1)
        provider = next((p for p in all_providers if p.id == selection), None)
        if not provider:
            raise typer.Exit(1)

    # Select model - show table then fuzzy select
    if prefill_model:
        model_id = prefill_model
    else:
        model_ids = [m.id for m in provider.models]
        if not model_ids:
            model_id = text_input("Enter model ID:")
            if not model_id:
                error("Model ID is required")
                raise typer.Exit(5)
        else:
            # Show available models table
            print_models_table(provider.models, title=f"{provider.name} - Available Models")

            # Fuzzy select
            console.print("\n[dim]Type to search models (tab to complete):[/dim]")
            model_selection = fuzzy_select("Model:", model_ids)
            if model_selection is None or model_selection not in model_ids:
                raise typer.Exit(1)
            model_id = model_selection

    # Build the full model string with provider prefix
    if "/" not in model_id:
        full_model_id = f"{provider.id}/{model_id}"
    else:
        full_model_id = model_id

    # Get alias
    if prefill_alias:
        alias = prefill_alias
    else:
        default_alias = model_id.split("/")[-1].split(":")[0]
        alias = text_input("Model alias (display name):", default=default_alias)
        if not alias:
            alias = default_alias
    # Check duplicate model name on proxy
    existing_model_id: str | None = None
    try:
        existing_models = client.list_models()
        for m in existing_models:
            if m.get("model_name") == alias:
                if replace:
                    existing_model_id = m.get("model_info", {}).get("id")
                    warning(f"Model '{alias}' exists, will be replaced")
                else:
                    warning(f"Model '{alias}' already exists on the proxy")
                    if not confirm("Continue creating anyway?", default=True):
                        raise typer.Exit(1)
                break
    except (ConnectionError, AuthenticationError, APIError):
        pass  # Can't check — continue

    # Get API key with retry loop for test validation
    if prefill_api_key:
        api_key = prefill_api_key
    elif provider.requires_api_key:
        env_hint = f" (or press Enter to use {provider.env_var})" if provider.env_var else ""
        api_key = text_input(f"API Key{env_hint}:", password=True)
    else:
        api_key = None

    # Test and create with retry loop
    max_retries = 3
    for attempt in range(max_retries):
        litellm_params = {"model": full_model_id}
        if api_key:
            litellm_params["api_key"] = api_key

        # Test model before creating
        console.print("\n[dim]Testing model connection...[/dim]")
        with console.status("[bold cyan]Sending test request..."):
            test_ok, test_message = client.test_model_completion(alias, litellm_params)

        if test_ok:
            success(f"Test passed: {test_message}")
            console.print()
            break
        else:
            error(f"Test failed: {test_message}")

            if attempt < max_retries - 1:
                console.print()
                retry_choices = [
                    "Re-enter API key",
                    "Re-enter model ID",
                    "Skip test and create anyway",
                    "Cancel",
                ]
                from llm_cli.ui import select_from_list
                retry_action = select_from_list("What would you like to do?", retry_choices)

                if retry_action is None or "Cancel" in retry_action:
                    raise typer.Exit(1)
                elif "Re-enter API key" in retry_action:
                    api_key = text_input("API Key:", password=True)
                    continue
                elif "Re-enter model ID" in retry_action:
                    new_model = text_input("Model ID:", default=full_model_id)
                    if new_model:
                        full_model_id = new_model
                    continue
                elif "Skip test" in retry_action:
                    warning("Skipping test - model may not work correctly")
                    console.print()
                    break
            else:
                # Last attempt failed
                if not confirm("All test attempts failed. Create model anyway?", default=False):
                    raise typer.Exit(1)
                warning("Creating model without successful test")
                console.print()

    # Pricing — prompt if not prefilled
    input_cost = prefill_input_cost
    output_cost = prefill_output_cost
    if input_cost is None and output_cost is None:
        if confirm("Set custom pricing? (default: No)", default=False):
            ic = text_input("Input price per 1M tokens ($):")
            oc = text_input("Output price per 1M tokens ($):")
            try:
                input_cost = float(ic) if ic else None
            except ValueError:
                pass
            try:
                output_cost = float(oc) if oc else None
            except ValueError:
                pass

    model_info = _build_model_info(input_cost, output_cost)

    # Delete old model if replacing
    if replace and existing_model_id:
        try:
            client.delete_model(existing_model_id)
        except (ConnectionError, AuthenticationError, APIError) as e:
            error(f"Failed to delete existing model: {e}")
            raise typer.Exit(1)

    # Create model
    try:
        client.create_model(
            model_name=alias,
            litellm_params=litellm_params,
            model_info=model_info,
        )
        action = "replaced" if replace and existing_model_id else "created"
        success(f"Model '{alias}' {action} successfully")
        print_detail("Provider", provider.id)
        print_detail("Model", full_model_id)
        if input_cost is not None:
            print_detail("Input cost", f"${input_cost}/1M tokens")
        if output_cost is not None:
            print_detail("Output cost", f"${output_cost}/1M tokens")
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
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
    input_cost: float | None,
    output_cost: float | None,
    org: str | None,
    env: str | None,
    replace: bool = False,
) -> None:
    """Non-interactive model creation with retry for missing/bad API key."""
    from llm_cli.ui import select_from_list, text_input

    client = _get_client(org, env)

    # Check duplicate model name on proxy
    existing_model_id: str | None = None
    try:
        existing_models = client.list_models()
        for m in existing_models:
            if m.get("model_name") == alias:
                if replace:
                    existing_model_id = m.get("model_info", {}).get("id")
                    warning(f"Model '{alias}' exists, will be replaced")
                else:
                    warning(f"Model '{alias}' already exists on the proxy")
                    if not confirm("Continue creating anyway?", default=True):
                        raise typer.Exit(1)
                break
    except (ConnectionError, AuthenticationError, APIError):
        pass  # Can't check — continue

    litellm_params = {"model": model_id}
    if api_key:
        litellm_params["api_key"] = api_key
    else:
        key = text_input("API key:", password=True)
        if key:
            litellm_params["api_key"] = key

    # Test model with retry loop
    max_retries = 3
    for attempt in range(max_retries):
        console.print("[dim]Testing model connection...[/dim]")
        with console.status("[bold cyan]Sending test request..."):
            test_ok, test_message = client.test_model_completion(alias, litellm_params)

        if test_ok:
            success(f"Test passed: {test_message}")
            break
        else:
            error(f"Test failed: {test_message}")
            if attempt < max_retries - 1:
                retry_choices = [
                    "Enter API key",
                    "Skip test and create anyway",
                    "Cancel",
                ]
                retry_action = select_from_list("What would you like to do?", retry_choices)

                if retry_action and "API key" in retry_action:
                    new_key = text_input("API key:", password=True)
                    if new_key:
                        litellm_params["api_key"] = new_key
                elif retry_action and "Skip" in retry_action:
                    warning("Skipping test, creating model anyway")
                    break
                else:
                    raise typer.Exit(6)
            else:
                error("Max retries reached")
                raise typer.Exit(6)

    model_info = _build_model_info(input_cost, output_cost)

    # Delete old model if replacing
    if replace and existing_model_id:
        try:
            client.delete_model(existing_model_id)
        except (ConnectionError, AuthenticationError, APIError) as e:
            error(f"Failed to delete existing model: {e}")
            raise typer.Exit(1)

    try:
        client.create_model(
            model_name=alias,
            litellm_params=litellm_params,
            model_info=model_info,
        )
        action = "replaced" if replace and existing_model_id else "created"
        success(f"Model '{alias}' {action} successfully")
        if input_cost is not None:
            print_detail("Input cost", f"${input_cost}/1M tokens")
        if output_cost is not None:
            print_detail("Output cost", f"${output_cost}/1M tokens")
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"Failed to create model: {e.message}")
        raise typer.Exit(1)


@app.command("apply")
def apply_models(
    file: Path = typer.Option(
        ..., "--file", "-f", exists=True, readable=True, resolve_path=True,
        help="Path to models YAML file",
    ),
    env_file: Optional[Path] = typer.Option(
        None, "--env-file", exists=True, readable=True, resolve_path=True,
        help="Path to .env file (default: .env next to models file)",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate and preview without creating"),
    skip_test: bool = typer.Option(False, "--skip-test", help="Skip model connection testing"),
    replace: bool = typer.Option(False, "--replace", "-r", help="Replace existing models if they already exist"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Bulk create models from a YAML file.

    Examples:
        llm model apply -f models.yaml
        llm model apply -f models.yaml --dry-run
        llm model apply -f models.yaml --skip-test
        llm model apply -f models.yaml --replace
        llm model apply -f models.yaml --env-file prod.env
    """
    from llm_cli.core.apply import ModelApplyService

    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"

    info(f"Loading models from {file.name}")

    service = ModelApplyService(client)
    models_file, validation_errors = service.load_and_validate(file, env_file=env_file)

    if validation_errors:
        console.print()
        error(f"Validation failed with {len(validation_errors)} error(s):")
        console.print()
        for ve in validation_errors:
            console.print(f"  {ve}", style="dim")
        console.print()
        raise typer.Exit(1)

    assert models_file is not None  # guaranteed when no errors

    # Merge replace: CLI flag OR YAML defaults.replace (either one enables replace)
    if not replace and models_file.defaults:
        replace = models_file.defaults.replace

    # Show duplicate warnings (non-blocking)
    if service.duplicate_warnings:
        console.print()
        for dup_name in service.duplicate_warnings:
            warning(f"Model '{dup_name}' already exists on the proxy")

    # Preview table
    console.print()
    table = Table(
        title=f"Models to apply on {context_name}",
        show_header=True,
        header_style="bold",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Public Name", style="cyan")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Mode", style="dim")
    table.add_column("API Key", style="dim")

    for i, model in enumerate(models_file.models, 1):
        masked_key = "***" if model.api_key else "-"
        table.add_row(
            str(i),
            model.public_name,
            model.provider,
            model.provider_model,
            model.mode or "chat",
            masked_key,
        )

    console.print(table)
    console.print()
    console.print(f"Total: {len(models_file.models)} model(s)")
    console.print()

    if dry_run:
        success("Dry run completed — no models were created")
        raise typer.Exit(0)

    # Test models
    models_to_create = models_file.models
    if not skip_test:
        console.print("[dim]Testing model connections...[/dim]")
        console.print()
        test_results = service.test_models(models_file)

        passed_names: set[str] = set()
        test_passed = 0
        test_failed = 0
        for tr in test_results:
            if tr.passed:
                test_passed += 1
                passed_names.add(tr.model_name)
                success(f"{tr.model_name} -> {tr.message}")
            else:
                test_failed += 1
                error(f"{tr.model_name} -> {tr.message}")

        console.print()
        console.print(f"Test: {test_passed} passed, {test_failed} failed")
        console.print()

        if test_failed > 0:
            models_to_create = [m for m in models_file.models if m.public_name in passed_names]
            if not models_to_create:
                error("All models failed testing — nothing to create")
                raise typer.Exit(1)

    # Confirm
    if not confirm(
        f"Create {len(models_to_create)} model(s) on {context_name}?",
        default=True,
    ):
        raise typer.Exit(0)

    console.print()

    # Apply
    skipped = len(models_file.models) - len(models_to_create)
    report = service.apply(models_to_create, replace=replace)
    report.skipped = skipped

    for result in report.results:
        if result.success:
            success(f"{result.model_name} -> {result.provider_model}")
        else:
            error(f"{result.model_name} -> {result.message}")

    console.print()
    parts = []
    if report.replaced:
        parts.append(f"{report.replaced} replaced")
    if report.created:
        parts.append(f"{report.created} created")
    if not parts:
        parts.append("0 created")
    if report.failed:
        parts.append(f"{report.failed} failed")
    if report.skipped:
        parts.append(f"{report.skipped} skipped")
    summary = ", ".join(parts)

    if report.failed == 0:
        success(f"Done: {summary}")
    else:
        warning(f"Done: {summary}")
        raise typer.Exit(1)


@app.command("delete")
def delete_model(
    model_name: Optional[str] = typer.Argument(None, help="Model name to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Override environment"),
) -> None:
    """Delete a model from the proxy.

    Examples:
        llm model delete                    # Interactive selection
        llm model delete my-gpt4o           # By name
        llm model delete my-gpt4o --yes     # Skip confirmation
    """
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
        # Show deployed models table first
        context_name = f"{client.context.organization_id}/{client.context.environment}"
        print_proxy_models_table(models, context_name)

        # Fuzzy select to pick one
        model_choices = [m.get("model_name", "") for m in models if m.get("model_name")]
        console.print("\n[dim]Type to search models (tab to complete):[/dim]")
        selection = fuzzy_select("Delete model:", model_choices)
        if selection is None or selection not in model_choices:
            raise typer.Exit(1)
        model_name = selection

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
