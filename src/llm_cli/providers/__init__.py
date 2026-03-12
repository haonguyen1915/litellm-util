"""Provider definitions and registry."""

from llm_cli.models.provider import ProviderInfo
from llm_cli.providers.anthropic import ANTHROPIC_PROVIDER
from llm_cli.providers.azure import AZURE_PROVIDER
from llm_cli.providers.bedrock import BEDROCK_PROVIDER
from llm_cli.providers.cohere import COHERE_PROVIDER
from llm_cli.providers.deepseek import DEEPSEEK_PROVIDER
from llm_cli.providers.groq import GROQ_PROVIDER
from llm_cli.providers.mistral import MISTRAL_PROVIDER
from llm_cli.providers.ollama import OLLAMA_PROVIDER
from llm_cli.providers.openai import OPENAI_PROVIDER
from llm_cli.providers.vertex import VERTEX_PROVIDER

# Provider registry
_PROVIDERS: dict[str, ProviderInfo] = {
    "openai": OPENAI_PROVIDER,
    "anthropic": ANTHROPIC_PROVIDER,
    "azure": AZURE_PROVIDER,
    "vertex_ai": VERTEX_PROVIDER,
    "bedrock": BEDROCK_PROVIDER,
    "groq": GROQ_PROVIDER,
    "mistral": MISTRAL_PROVIDER,
    "deepseek": DEEPSEEK_PROVIDER,
    "cohere": COHERE_PROVIDER,
    "ollama": OLLAMA_PROVIDER,
}


def get_all_providers() -> list[ProviderInfo]:
    """Get all registered providers.

    Returns:
        List of all provider info objects.
    """
    return list(_PROVIDERS.values())


def get_provider(provider_id: str) -> ProviderInfo | None:
    """Get provider by ID.

    Args:
        provider_id: Provider identifier (e.g., 'openai', 'anthropic').

    Returns:
        ProviderInfo if found, None otherwise.
    """
    return _PROVIDERS.get(provider_id)


def get_provider_ids() -> list[str]:
    """Get list of all provider IDs.

    Returns:
        List of provider ID strings.
    """
    return list(_PROVIDERS.keys())
