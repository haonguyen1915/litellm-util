"""Anthropic provider and models."""

from llm_cli.providers.base import create_model, create_provider

ANTHROPIC_MODELS = [
    create_model(
        id="claude-opus-4-20250514",
        provider="anthropic",
        context_window=200_000,
        max_output=32_000,
        input_price=15.00,
        output_price=75.00,
        capabilities=["vision", "tools", "streaming", "computer_use"],
        training_cutoff="January 2025",
    ),
    create_model(
        id="claude-sonnet-4-20250514",
        provider="anthropic",
        context_window=200_000,
        max_output=64_000,
        input_price=3.00,
        output_price=15.00,
        capabilities=["vision", "tools", "streaming", "computer_use"],
        training_cutoff="January 2025",
    ),
    create_model(
        id="claude-3-5-sonnet-20241022",
        provider="anthropic",
        context_window=200_000,
        max_output=8_192,
        input_price=3.00,
        output_price=15.00,
        capabilities=["vision", "tools", "streaming", "computer_use"],
        training_cutoff="April 2024",
    ),
    create_model(
        id="claude-3-5-haiku-20241022",
        provider="anthropic",
        context_window=200_000,
        max_output=8_192,
        input_price=1.00,
        output_price=5.00,
        capabilities=["vision", "tools", "streaming"],
        training_cutoff="July 2024",
    ),
    create_model(
        id="claude-3-opus-20240229",
        provider="anthropic",
        context_window=200_000,
        max_output=4_096,
        input_price=15.00,
        output_price=75.00,
        capabilities=["vision", "tools", "streaming"],
        training_cutoff="August 2023",
    ),
    create_model(
        id="claude-3-sonnet-20240229",
        provider="anthropic",
        context_window=200_000,
        max_output=4_096,
        input_price=3.00,
        output_price=15.00,
        capabilities=["vision", "tools", "streaming"],
        training_cutoff="August 2023",
    ),
    create_model(
        id="claude-3-haiku-20240307",
        provider="anthropic",
        context_window=200_000,
        max_output=4_096,
        input_price=0.25,
        output_price=1.25,
        capabilities=["vision", "tools", "streaming"],
        training_cutoff="August 2023",
    ),
]

ANTHROPIC_PROVIDER = create_provider(
    id="anthropic",
    name="Anthropic",
    description="Anthropic (Claude 4, Claude 3.5, Claude 3)",
    models=ANTHROPIC_MODELS,
    env_var="ANTHROPIC_API_KEY",
)
