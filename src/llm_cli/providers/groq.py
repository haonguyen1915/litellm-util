"""Groq provider and models."""

from llm_cli.providers.base import create_model, create_provider

GROQ_MODELS = [
    create_model(
        id="groq/llama-3.3-70b-versatile",
        provider="groq",
        context_window=128_000,
        max_output=32_768,
        input_price=0.59,
        output_price=0.79,
        capabilities=["tools", "streaming", "json_mode"],
    ),
    create_model(
        id="groq/llama-3.1-70b-versatile",
        provider="groq",
        context_window=128_000,
        max_output=8_000,
        input_price=0.59,
        output_price=0.79,
        capabilities=["tools", "streaming", "json_mode"],
    ),
    create_model(
        id="groq/llama-3.1-8b-instant",
        provider="groq",
        context_window=128_000,
        max_output=8_000,
        input_price=0.05,
        output_price=0.08,
        capabilities=["tools", "streaming", "json_mode"],
    ),
    create_model(
        id="groq/mixtral-8x7b-32768",
        provider="groq",
        context_window=32_768,
        max_output=8_000,
        input_price=0.24,
        output_price=0.24,
        capabilities=["tools", "streaming"],
    ),
    create_model(
        id="groq/gemma2-9b-it",
        provider="groq",
        context_window=8_192,
        max_output=8_000,
        input_price=0.20,
        output_price=0.20,
        capabilities=["streaming"],
    ),
]

GROQ_PROVIDER = create_provider(
    id="groq",
    name="Groq",
    description="Groq (Ultra-fast inference)",
    models=GROQ_MODELS,
    env_var="GROQ_API_KEY",
)
