"""Core service for bulk model apply."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
from pydantic import ValidationError as PydanticValidationError

from llm_cli.core.client import APIError, AuthenticationError, ConnectionError, LiteLLMClient
from llm_cli.models.apply import ModelDefaults, ModelEntry, ModelsFile
from llm_cli.utils.validators import validate_api_key, validate_url


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ValidationError:
    model_index: int | None
    model_name: str | None
    field: str
    message: str

    def __str__(self) -> str:
        if self.model_name and self.model_index is not None:
            prefix = f"{self.model_name} (models[{self.model_index}])"
        elif self.model_index is not None:
            prefix = f"models[{self.model_index}]"
        elif self.model_name:
            prefix = self.model_name
        else:
            return f"{self.field}: {self.message}"
        return f"{prefix}.{self.field}: {self.message}"


@dataclass
class ApplyResult:
    model_name: str
    provider_model: str
    success: bool
    message: str


@dataclass
class TestResult:
    model_name: str
    provider_model: str
    passed: bool
    message: str


@dataclass
class ApplyReport:
    total: int = 0
    created: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[ApplyResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Env var expansion
# ---------------------------------------------------------------------------

_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def expand_env_vars(value: str) -> str:
    """Expand ``${VAR}`` references in *value*.

    Raises ``ValueError`` if a referenced env var is not set.
    """

    def _replace(match: re.Match) -> str:
        var_name = match.group(1)
        env_val = os.environ.get(var_name)
        if env_val is None:
            raise ValueError(f"environment variable ${{{var_name}}} is not set")
        return env_val

    return _ENV_VAR_RE.sub(_replace, value)


def expand_env_in_dict(data: Any) -> Any:
    """Recursively expand ``${VAR}`` in all string values."""
    if isinstance(data, str):
        return expand_env_vars(data)
    if isinstance(data, dict):
        return {k: expand_env_in_dict(v) for k, v in data.items()}
    if isinstance(data, list):
        return [expand_env_in_dict(item) for item in data]
    return data


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ModelApplyService:
    """Orchestrates loading, validation and applying of models."""

    def __init__(self, client: LiteLLMClient) -> None:
        self.client = client

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_and_validate(
        self, file_path: Path, env_file: Path | None = None,
    ) -> tuple[ModelsFile | None, list[ValidationError]]:
        """Phases 1-3: load YAML, expand env vars, validate schema, validate semantics.

        Args:
            file_path: Path to the models YAML file.
            env_file: Explicit ``.env`` file path. When *None* the service
                looks for a ``.env`` in the same directory as *file_path*.
        """
        errors: list[ValidationError] = []

        # Load .env into os.environ (existing vars are NOT overridden) ---
        self._load_dotenv(file_path, env_file)

        # Phase 1: parse YAML -------------------------------------------
        raw = self._load_yaml(file_path, errors)
        if errors:
            return None, errors

        if not isinstance(raw, dict):
            errors.append(
                ValidationError(
                    model_index=None,
                    model_name=None,
                    field="file",
                    message="YAML root must be a mapping",
                )
            )
            return None, errors

        if "models" not in raw:
            errors.append(
                ValidationError(
                    model_index=None,
                    model_name=None,
                    field="file",
                    message="missing required key 'models'",
                )
            )
            return None, errors

        # Expand env vars ------------------------------------------------
        try:
            raw = expand_env_in_dict(raw)
        except ValueError as exc:
            errors.append(
                ValidationError(
                    model_index=None,
                    model_name=None,
                    field="env",
                    message=str(exc),
                )
            )
            return None, errors

        # Merge defaults into each model ---------------------------------
        raw = self._merge_defaults_raw(raw)

        # Phase 2: Pydantic validation -----------------------------------
        try:
            models_file = ModelsFile.model_validate(raw)
        except PydanticValidationError as exc:
            for err in exc.errors():
                loc_parts = [str(p) for p in err["loc"]]
                # Try to extract model index and field
                model_index: int | None = None
                model_name: str | None = None
                field_name = ".".join(loc_parts)

                if len(loc_parts) >= 2 and loc_parts[0] == "models":
                    try:
                        model_index = int(loc_parts[1])
                        field_name = ".".join(loc_parts[2:]) or "unknown"
                        # Try to get public_name from raw data
                        models_raw = raw.get("models", [])
                        if model_index < len(models_raw) and isinstance(
                            models_raw[model_index], dict
                        ):
                            model_name = models_raw[model_index].get("public_name")
                    except (ValueError, IndexError):
                        pass

                errors.append(
                    ValidationError(
                        model_index=model_index,
                        model_name=model_name,
                        field=field_name,
                        message=err["msg"],
                    )
                )
            return None, errors

        # Phase 3: semantic validation -----------------------------------
        self._validate_semantic(models_file, errors)
        if errors:
            return None, errors

        return models_file, []

    def build_api_payload(self, model: ModelEntry) -> dict[str, Any]:
        """Convert ``ModelEntry`` to ``/model/new`` API payload."""
        litellm_params: dict[str, Any] = {
            "model": f"{model.provider}/{model.provider_model}",
        }
        for key in ("api_key", "api_base", "max_retries", "timeout", "stream_timeout", "rpm", "tpm"):
            val = getattr(model, key, None)
            if val is not None:
                litellm_params[key] = val

        model_info: dict[str, Any] = {}
        for key in ("input_cost_per_token", "output_cost_per_token", "mode"):
            val = getattr(model, key, None)
            if val is not None:
                model_info[key] = val

        payload: dict[str, Any] = {
            "model_name": model.public_name,
            "litellm_params": litellm_params,
        }
        if model_info:
            payload["model_info"] = model_info

        return payload

    def test_models(self, models_file: ModelsFile) -> list[TestResult]:
        """Test each model by calling the provider API directly via litellm SDK."""
        results: list[TestResult] = []
        for model in models_file.models:
            payload = self.build_api_payload(model)
            provider_model = f"{model.provider}/{model.provider_model}"
            passed, message = LiteLLMClient.test_model_completion(
                model.public_name, payload["litellm_params"],
            )
            results.append(
                TestResult(
                    model_name=model.public_name,
                    provider_model=provider_model,
                    passed=passed,
                    message=message,
                )
            )
        return results

    def apply(self, models: list[ModelEntry]) -> ApplyReport:
        """Create models on the proxy (continue-on-error)."""
        report = ApplyReport(total=len(models))

        for model in models:
            provider_model = f"{model.provider}/{model.provider_model}"
            try:
                payload = self.build_api_payload(model)
                self.client.create_model(
                    model_name=payload["model_name"],
                    litellm_params=payload["litellm_params"],
                    model_info=payload.get("model_info"),
                )
                report.created += 1
                report.results.append(
                    ApplyResult(
                        model_name=model.public_name,
                        provider_model=provider_model,
                        success=True,
                        message="created",
                    )
                )
            except (APIError, AuthenticationError, ConnectionError) as exc:
                report.failed += 1
                report.results.append(
                    ApplyResult(
                        model_name=model.public_name,
                        provider_model=provider_model,
                        success=False,
                        message=str(exc),
                    )
                )

        return report

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _load_dotenv(file_path: Path, env_file: Path | None) -> Path | None:
        """Load a ``.env`` file into ``os.environ``.

        Resolution order:
        1. Explicit *env_file* if provided.
        2. ``.env`` in the same directory as *file_path*.
        3. ``.env`` in the current working directory.

        Existing environment variables are **not** overridden.
        Returns the path that was loaded, or *None*.
        """
        if env_file is not None:
            candidates = [env_file]
        else:
            candidates = [
                file_path.parent / ".env",
                Path.cwd() / ".env",
            ]

        for candidate in candidates:
            if candidate.is_file():
                values = dotenv_values(candidate)
                for key, value in values.items():
                    if value is not None:
                        os.environ.setdefault(key, value)
                return candidate

        return None

    @staticmethod
    def _load_yaml(
        file_path: Path, errors: list[ValidationError]
    ) -> dict[str, Any] | None:
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)
            return data
        except yaml.YAMLError as exc:
            errors.append(
                ValidationError(
                    model_index=None,
                    model_name=None,
                    field="file",
                    message=f"invalid YAML syntax: {exc}",
                )
            )
            return None

    @staticmethod
    def _merge_defaults_raw(raw: dict[str, Any]) -> dict[str, Any]:
        """Merge ``defaults`` into each model entry (model values win)."""
        defaults = raw.get("defaults")
        if not defaults or not isinstance(defaults, dict):
            return raw

        merged_models = []
        for model in raw.get("models", []):
            if not isinstance(model, dict):
                merged_models.append(model)
                continue
            merged = {**defaults, **{k: v for k, v in model.items() if v is not None}}
            merged_models.append(merged)

        return {**raw, "models": merged_models}

    def _validate_semantic(
        self, models_file: ModelsFile, errors: list[ValidationError]
    ) -> None:
        """Phase 3: semantic checks using existing validators."""
        # Check duplicates against proxy
        try:
            existing_models = self.client.list_models()
            existing_names = {m.get("model_name", "") for m in existing_models}
        except (APIError, AuthenticationError, ConnectionError):
            existing_names = set()

        for i, model in enumerate(models_file.models):
            # Check duplicate against proxy
            if model.public_name in existing_names:
                errors.append(
                    ValidationError(
                        model_index=i,
                        model_name=model.public_name,
                        field="public_name",
                        message=f"model '{model.public_name}' already exists on the proxy",
                    )
                )

            # Validate api_key
            if model.api_key is not None:
                result = validate_api_key(model.api_key)
                if result is not True:
                    errors.append(
                        ValidationError(
                            model_index=i,
                            model_name=model.public_name,
                            field="api_key",
                            message=str(result),
                        )
                    )

            # Validate api_base
            if model.api_base is not None:
                result = validate_url(model.api_base)
                if result is not True:
                    errors.append(
                        ValidationError(
                            model_index=i,
                            model_name=model.public_name,
                            field="api_base",
                            message=str(result),
                        )
                    )
