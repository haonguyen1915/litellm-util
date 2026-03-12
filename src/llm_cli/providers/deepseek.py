"""DeepSeek provider and models."""

from llm_cli.providers.base import create_model, create_provider

DEEPSEEK_MODELS = [
    create_model(
        id="deepseek/deepseek-chat",
        provider="deepseek",
        context_window=64_000,
        max_output=8_192,
        input_price=0.14,
        output_price=0.28,
        capabilities=["tools", "streaming", "json_mode"],
        training_cutoff="December 2024",
    ),
    create_model(
        id="deepseek/deepseek-reasoner",
        provider="deepseek",
        context_window=64_000,
        max_output=8_192,
        input_price=0.55,
        output_price=2.19,
        capabilities=["reasoning", "streaming"],
        training_cutoff="December 2024",
    ),
    create_model(
        id="deepseek/deepseek-coder",
        provider="deepseek",
        context_window=64_000,
        max_output=8_192,
        input_price=0.14,
        output_price=0.28,
        capabilities=["tools", "streaming", "fill_in_middle"],
        training_cutoff="December 2024",
    ),
]

DEEPSEEK_PROVIDER = create_provider(
    id="deepseek",
    name="DeepSeek",
    description="DeepSeek (Chat, Reasoner, Coder)",
    models=DEEPSEEK_MODELS,
    env_var="DEEPSEEK_API_KEY",
)
