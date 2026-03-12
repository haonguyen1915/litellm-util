"""Cohere provider and models."""

from llm_cli.providers.base import create_model, create_provider

COHERE_MODELS = [
    create_model(
        id="cohere/command-r-plus",
        provider="cohere",
        context_window=128_000,
        max_output=4_096,
        input_price=2.50,
        output_price=10.00,
        capabilities=["tools", "streaming", "rag"],
    ),
    create_model(
        id="cohere/command-r",
        provider="cohere",
        context_window=128_000,
        max_output=4_096,
        input_price=0.15,
        output_price=0.60,
        capabilities=["tools", "streaming", "rag"],
    ),
    create_model(
        id="cohere/command-light",
        provider="cohere",
        context_window=4_096,
        max_output=4_096,
        input_price=0.30,
        output_price=0.60,
        capabilities=["streaming"],
    ),
    create_model(
        id="cohere/command",
        provider="cohere",
        context_window=4_096,
        max_output=4_096,
        input_price=1.00,
        output_price=2.00,
        capabilities=["streaming"],
    ),
]

COHERE_PROVIDER = create_provider(
    id="cohere",
    name="Cohere",
    description="Cohere (Command R, Command)",
    models=COHERE_MODELS,
    env_var="COHERE_API_KEY",
)
