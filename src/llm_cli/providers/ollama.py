"""Ollama provider (local models)."""

from llm_cli.providers.base import create_model, create_provider

# Common Ollama models with default specs
# Users typically run these locally, so pricing is $0
OLLAMA_MODELS = [
    create_model(
        id="ollama/llama3.2",
        provider="ollama",
        context_window=128_000,
        max_output=4_096,
        input_price=0.00,
        output_price=0.00,
        capabilities=["tools", "streaming"],
    ),
    create_model(
        id="ollama/llama3.1",
        provider="ollama",
        context_window=128_000,
        max_output=4_096,
        input_price=0.00,
        output_price=0.00,
        capabilities=["tools", "streaming"],
    ),
    create_model(
        id="ollama/mistral",
        provider="ollama",
        context_window=32_000,
        max_output=4_096,
        input_price=0.00,
        output_price=0.00,
        capabilities=["tools", "streaming"],
    ),
    create_model(
        id="ollama/mixtral",
        provider="ollama",
        context_window=32_000,
        max_output=4_096,
        input_price=0.00,
        output_price=0.00,
        capabilities=["tools", "streaming"],
    ),
    create_model(
        id="ollama/codellama",
        provider="ollama",
        context_window=16_000,
        max_output=4_096,
        input_price=0.00,
        output_price=0.00,
        capabilities=["streaming", "fill_in_middle"],
    ),
    create_model(
        id="ollama/phi3",
        provider="ollama",
        context_window=4_096,
        max_output=4_096,
        input_price=0.00,
        output_price=0.00,
        capabilities=["streaming"],
    ),
    create_model(
        id="ollama/qwen2.5",
        provider="ollama",
        context_window=32_000,
        max_output=4_096,
        input_price=0.00,
        output_price=0.00,
        capabilities=["tools", "streaming"],
    ),
    create_model(
        id="ollama/deepseek-r1",
        provider="ollama",
        context_window=64_000,
        max_output=8_192,
        input_price=0.00,
        output_price=0.00,
        capabilities=["reasoning", "streaming"],
    ),
]

OLLAMA_PROVIDER = create_provider(
    id="ollama",
    name="Ollama",
    description="Ollama (Local models)",
    models=OLLAMA_MODELS,
    env_var=None,
    requires_api_key=False,
)
