"""Google Vertex AI provider and models."""

from llm_cli.providers.base import create_model, create_provider

VERTEX_MODELS = [
    create_model(
        id="vertex_ai/gemini-2.0-flash",
        provider="vertex_ai",
        context_window=1_000_000,
        max_output=8_192,
        input_price=0.075,
        output_price=0.30,
        capabilities=["vision", "tools", "streaming", "audio"],
        training_cutoff="August 2024",
    ),
    create_model(
        id="vertex_ai/gemini-1.5-pro",
        provider="vertex_ai",
        context_window=2_000_000,
        max_output=8_192,
        input_price=1.25,
        output_price=5.00,
        capabilities=["vision", "tools", "streaming", "audio", "video"],
        training_cutoff="April 2024",
    ),
    create_model(
        id="vertex_ai/gemini-1.5-flash",
        provider="vertex_ai",
        context_window=1_000_000,
        max_output=8_192,
        input_price=0.075,
        output_price=0.30,
        capabilities=["vision", "tools", "streaming", "audio", "video"],
        training_cutoff="April 2024",
    ),
    create_model(
        id="vertex_ai/gemini-1.0-pro",
        provider="vertex_ai",
        context_window=32_000,
        max_output=8_192,
        input_price=0.50,
        output_price=1.50,
        capabilities=["tools", "streaming"],
        training_cutoff="November 2023",
    ),
]

VERTEX_PROVIDER = create_provider(
    id="vertex_ai",
    name="Google Vertex AI",
    description="Google Vertex AI (Gemini)",
    models=VERTEX_MODELS,
    env_var="GOOGLE_APPLICATION_CREDENTIALS",
)
