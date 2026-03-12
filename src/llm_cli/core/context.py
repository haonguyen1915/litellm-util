"""Current organization/environment context management."""

from dataclasses import dataclass

from llm_cli.core.config import load_config
from llm_cli.models.config import Config


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


@dataclass
class CurrentContext:
    """Current active context information."""

    organization_id: str
    organization_name: str
    environment: str
    url: str
    master_key: str


def get_current_context(
    org_override: str | None = None, env_override: str | None = None
) -> CurrentContext:
    """Get the current active context.

    Args:
        org_override: Override organization from command line.
        env_override: Override environment from command line.

    Returns:
        CurrentContext with active org/env details.

    Raises:
        ConfigurationError: If no configuration or invalid context.
    """
    config = load_config()

    if not config.organizations:
        raise ConfigurationError(
            "No organizations configured. Run 'llm init' to set up."
        )

    # Determine which org to use
    org_id = org_override
    if not org_id:
        if config.default:
            org_id = config.default.organization
        else:
            raise ConfigurationError(
                "No default organization set. Run 'llm config use' to select one."
            )

    if org_id not in config.organizations:
        raise ConfigurationError(f"Organization '{org_id}' not found in configuration.")

    org = config.organizations[org_id]

    # Determine which env to use
    env_name = env_override
    if not env_name:
        if config.default:
            env_name = config.default.environment
        else:
            raise ConfigurationError(
                "No default environment set. Run 'llm config use' to select one."
            )

    if env_name not in org.environments:
        raise ConfigurationError(
            f"Environment '{env_name}' not found in organization '{org_id}'."
        )

    env = org.environments[env_name]

    return CurrentContext(
        organization_id=org_id,
        organization_name=org.name,
        environment=env_name,
        url=env.url,
        master_key=env.master_key,
    )


def set_current_context(config: Config, org_id: str, env_name: str) -> None:
    """Set the default organization and environment.

    Args:
        config: Config object to update.
        org_id: Organization ID.
        env_name: Environment name.

    Raises:
        ConfigurationError: If org or env not found.
    """
    if org_id not in config.organizations:
        raise ConfigurationError(f"Organization '{org_id}' not found.")

    if env_name not in config.organizations[org_id].environments:
        raise ConfigurationError(
            f"Environment '{env_name}' not found in organization '{org_id}'."
        )

    from llm_cli.models.config import DefaultContext

    config.default = DefaultContext(organization=org_id, environment=env_name)
