"""Pydantic models for bulk model apply."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

VALID_MODES = frozenset(
    {"chat", "embedding", "image_generation", "audio_transcription", "text_completion"}
)


class ModelDefaults(BaseModel):
    """Defaults block — merged into each model."""

    api_key: str | None = None
    api_base: str | None = None
    max_retries: int | None = None
    timeout: int | None = None
    stream_timeout: int | None = None
    rpm: int | None = None
    tpm: int | None = None
    mode: str | None = None

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_MODES:
            raise ValueError(
                f"mode must be one of: {', '.join(sorted(VALID_MODES))}"
            )
        return v

    @field_validator("max_retries", "timeout", "stream_timeout", "rpm", "tpm")
    @classmethod
    def validate_non_negative_int(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("must be a non-negative integer")
        return v


class ModelEntry(BaseModel):
    """Single model definition."""

    # Required
    public_name: str
    provider: str
    provider_model: str

    # Optional litellm_params
    api_key: str | None = None
    api_base: str | None = None
    max_retries: int | None = None
    timeout: int | None = None
    stream_timeout: int | None = None
    rpm: int | None = None
    tpm: int | None = None

    # Optional model_info
    input_cost_per_token: float | None = None
    output_cost_per_token: float | None = None
    mode: str | None = None

    @field_validator("public_name", "provider", "provider_model")
    @classmethod
    def validate_required_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("is required and cannot be empty")
        return v.strip()

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_MODES:
            raise ValueError(
                f"mode must be one of: {', '.join(sorted(VALID_MODES))}"
            )
        return v

    @field_validator("max_retries", "timeout", "stream_timeout", "rpm", "tpm")
    @classmethod
    def validate_non_negative_int(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("must be a non-negative integer")
        return v

    @field_validator("input_cost_per_token", "output_cost_per_token")
    @classmethod
    def validate_non_negative_float(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("must be a non-negative number")
        return v

    @field_validator("api_base")
    @classmethod
    def validate_api_base_scheme(cls, v: str | None) -> str | None:
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("must start with http:// or https://")
        return v


class ModelsFile(BaseModel):
    """Root YAML schema."""

    defaults: ModelDefaults | None = None
    models: list[ModelEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_no_duplicate_public_names(self) -> ModelsFile:
        seen: dict[str, int] = {}
        duplicates: list[str] = []
        for i, model in enumerate(self.models):
            name = model.public_name
            if name in seen:
                duplicates.append(
                    f"models[{i}].public_name: duplicate public_name '{name}' "
                    f"(first defined at models[{seen[name]}])"
                )
            else:
                seen[name] = i
        if duplicates:
            raise ValueError("; ".join(duplicates))
        return self
