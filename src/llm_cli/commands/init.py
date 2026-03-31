"""Init command - Initialize or add new organization/environment."""

import typer

from llm_cli.core.config import config_exists, load_config, save_config
from llm_cli.core.context import set_current_context
from llm_cli.models.config import DefaultContext, Environment, Organization
from llm_cli.ui import confirm, error, select_from_list, success, text_input
from llm_cli.ui.console import console


def init_command() -> None:
    """Initialize or add new organization/environment.

    Examples:
        llm init                # First-time setup or add new org/env
    """
    config = load_config()

    # Check if we have existing orgs
    if config.organizations:
        # Ask user to select existing org or create new
        choices = [f"{org_id} ({org.name})" for org_id, org in config.organizations.items()]
        choices.append("+ Create new organization")

        selection = select_from_list(
            "Select or create organization:",
            choices,
        )

        if selection is None:
            raise typer.Exit(1)

        if selection == "+ Create new organization":
            org_id, org = _create_new_organization()
        else:
            # Extract org_id from selection
            org_id = selection.split(" (")[0].lstrip("[0-9] ").strip()
            # Handle indexed format
            for oid in config.organizations:
                if oid in selection:
                    org_id = oid
                    break
            org = config.organizations[org_id]
    else:
        # First time setup
        console.print("\n[bold]Welcome to LiteLLM CLI![/bold]")
        console.print("Let's set up your first organization.\n")
        org_id, org = _create_new_organization()

    # Add environment to organization
    env_name, env = _create_new_environment(org_id, list(org.environments.keys()))

    # Update config
    if org_id not in config.organizations:
        config.organizations[org_id] = org

    config.organizations[org_id].environments[env_name] = env

    # Set as default if first setup or ask
    if not config.default:
        config.default = DefaultContext(organization=org_id, environment=env_name)
        save_config(config)
        success(f"Configuration saved to ~/.litellm/config.yaml")
        success(f"Set {org_id}/{env_name} as active environment")
    else:
        save_config(config)
        success(f"Added environment '{env_name}' to {org_id}")

        # Ask if user wants to switch
        if confirm(f"Switch to {org_id}/{env_name}?", default=True):
            set_current_context(config, org_id, env_name)
            save_config(config)
            success(f"Switched to {org_id}/{env_name}")


def _create_new_organization() -> tuple[str, Organization]:
    """Interactive prompts to create a new organization.

    Returns:
        Tuple of (org_id, Organization).
    """
    org_id = text_input("Organization ID (slug):")
    if not org_id:
        error("Organization ID is required")
        raise typer.Exit(1)

    # Validate org_id format (lowercase, alphanumeric, hyphens)
    org_id = org_id.lower().replace(" ", "-")

    org_name = text_input("Organization Name:", default=org_id.replace("-", " ").title())
    if not org_name:
        org_name = org_id

    return org_id, Organization(name=org_name, environments={})


def _create_new_environment(org_id: str, existing_envs: list[str]) -> tuple[str, Environment]:
    """Interactive prompts to create a new environment.

    Args:
        org_id: Organization ID for context.
        existing_envs: List of existing environment names.

    Returns:
        Tuple of (env_name, Environment).
    """
    # Suggest common environment names
    default_env = "dev"
    if "dev" in existing_envs:
        default_env = "prod" if "prod" not in existing_envs else "staging"

    env_name = text_input("Environment name:", default=default_env)
    if not env_name:
        error("Environment name is required")
        raise typer.Exit(1)

    env_name = env_name.lower().strip()

    if env_name in existing_envs:
        if not confirm(f"Environment '{env_name}' exists. Overwrite?"):
            raise typer.Exit(1)

    url = text_input("LiteLLM Proxy URL:", default="http://localhost:4000")
    if not url:
        error("URL is required")
        raise typer.Exit(1)

    # Normalize URL
    url = url.rstrip("/")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    master_key = text_input("Master Key:", password=True)
    if not master_key:
        error("Master key is required")
        raise typer.Exit(1)

    # LiteLLM proxy version
    version_choices = [
        "v2 (>= 1.80.x, recommended)",
        "v1 (<= 1.72.x)",
    ]
    version_selection = select_from_list("LiteLLM Proxy version:", version_choices)
    version = "v1" if version_selection and "v1" in version_selection else "v2"

    return env_name, Environment(url=url, master_key=master_key, version=version)
