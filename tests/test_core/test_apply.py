"""Tests for core.apply — ModelApplyService, env expansion, validation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from llm_cli.core.client import LiteLLMClient

import pytest
import yaml

from llm_cli.core.apply import (
    ApplyReport,
    ApplyResult,
    ModelApplyService,
    ValidationError,
    expand_env_in_dict,
    expand_env_vars,
)
from llm_cli.models.apply import ModelDefaults, ModelEntry, ModelsFile


# ---------------------------------------------------------------------------
# Env var expansion
# ---------------------------------------------------------------------------


class TestExpandEnvVars:
    def test_simple_expansion(self, monkeypatch):
        monkeypatch.setenv("MY_KEY", "secret123")
        assert expand_env_vars("${MY_KEY}") == "secret123"

    def test_multiple_vars(self, monkeypatch):
        monkeypatch.setenv("A", "hello")
        monkeypatch.setenv("B", "world")
        assert expand_env_vars("${A}-${B}") == "hello-world"

    def test_no_vars(self):
        assert expand_env_vars("plain text") == "plain text"

    def test_missing_var_raises(self, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_VAR_XYZ", raising=False)
        with pytest.raises(ValueError, match="NONEXISTENT_VAR_XYZ"):
            expand_env_vars("${NONEXISTENT_VAR_XYZ}")

    def test_expand_in_dict(self, monkeypatch):
        monkeypatch.setenv("KEY", "val")
        data = {"a": "${KEY}", "b": [{"c": "${KEY}"}], "d": 42}
        result = expand_env_in_dict(data)
        assert result == {"a": "val", "b": [{"c": "val"}], "d": 42}


# ---------------------------------------------------------------------------
# Pydantic model tests
# ---------------------------------------------------------------------------


class TestModelEntry:
    def test_valid_entry(self):
        entry = ModelEntry(
            public_name="gpt-4o",
            provider="openai",
            provider_model="gpt-4o",
            api_key="sk-1234567890",
            mode="chat",
        )
        assert entry.public_name == "gpt-4o"

    def test_empty_public_name_fails(self):
        with pytest.raises(Exception):
            ModelEntry(
                public_name="",
                provider="openai",
                provider_model="gpt-4o",
            )

    def test_invalid_mode_fails(self):
        with pytest.raises(Exception):
            ModelEntry(
                public_name="test",
                provider="openai",
                provider_model="gpt-4o",
                mode="invalid_mode",
            )

    def test_negative_int_fails(self):
        with pytest.raises(Exception):
            ModelEntry(
                public_name="test",
                provider="openai",
                provider_model="gpt-4o",
                max_retries=-1,
            )

    def test_negative_cost_fails(self):
        with pytest.raises(Exception):
            ModelEntry(
                public_name="test",
                provider="openai",
                provider_model="gpt-4o",
                input_cost_per_token=-0.01,
            )

    def test_invalid_api_base_fails(self):
        with pytest.raises(Exception):
            ModelEntry(
                public_name="test",
                provider="openai",
                provider_model="gpt-4o",
                api_base="not-a-url",
            )

    def test_valid_api_base(self):
        entry = ModelEntry(
            public_name="test",
            provider="openai",
            provider_model="gpt-4o",
            api_base="https://api.openai.com/v1",
        )
        assert entry.api_base == "https://api.openai.com/v1"


class TestModelsFile:
    def test_duplicate_public_name_fails(self):
        with pytest.raises(Exception, match="duplicate"):
            ModelsFile(
                models=[
                    ModelEntry(public_name="gpt", provider="openai", provider_model="gpt-4o"),
                    ModelEntry(public_name="gpt", provider="openai", provider_model="gpt-4"),
                ]
            )

    def test_empty_models_fails(self):
        with pytest.raises(Exception):
            ModelsFile(models=[])

    def test_valid_file(self):
        mf = ModelsFile(
            defaults=ModelDefaults(mode="chat"),
            models=[
                ModelEntry(public_name="a", provider="openai", provider_model="gpt-4o"),
                ModelEntry(public_name="b", provider="anthropic", provider_model="claude-3"),
            ],
        )
        assert len(mf.models) == 2


# ---------------------------------------------------------------------------
# ModelApplyService
# ---------------------------------------------------------------------------


def _write_yaml(tmp_path: Path, data: dict) -> Path:
    """Helper to write a YAML file and return its path."""
    p = tmp_path / "models.yaml"
    p.write_text(yaml.dump(data, default_flow_style=False))
    return p


class TestLoadAndValidate:
    def _make_service(self) -> ModelApplyService:
        client = MagicMock(spec=["create_model", "list_models", "context"])
        client.list_models.return_value = []
        return ModelApplyService(client)

    def test_valid_file(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_KEY", "sk-abcdefghij1234567890")
        data = {
            "models": [
                {
                    "public_name": "gpt-4o",
                    "provider": "openai",
                    "provider_model": "gpt-4o",
                    "api_key": "${TEST_KEY}",
                    "api_base": "https://api.openai.com/v1",
                }
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert errors == []
        assert models_file is not None
        assert len(models_file.models) == 1
        assert models_file.models[0].api_key == "sk-abcdefghij1234567890"

    def test_invalid_yaml(self, tmp_path):
        p = tmp_path / "bad.yaml"
        p.write_text("{ invalid yaml [[[")
        service = self._make_service()
        models_file, errors = service.load_and_validate(p)
        assert models_file is None
        assert len(errors) == 1
        assert "YAML" in errors[0].field or "YAML" in errors[0].message

    def test_missing_models_key(self, tmp_path):
        data = {"defaults": {"mode": "chat"}}
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert models_file is None
        assert any("models" in e.message for e in errors)

    def test_dotenv_auto_loaded(self, tmp_path, monkeypatch):
        """`.env` next to the YAML file is loaded automatically."""
        monkeypatch.delenv("DOTENV_TEST_KEY", raising=False)
        # Write .env next to models.yaml
        (tmp_path / ".env").write_text("DOTENV_TEST_KEY=sk-from-dotenv-1234567890\n")
        data = {
            "models": [
                {
                    "public_name": "test",
                    "provider": "openai",
                    "provider_model": "gpt-4o",
                    "api_key": "${DOTENV_TEST_KEY}",
                }
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert errors == []
        assert models_file is not None
        assert models_file.models[0].api_key == "sk-from-dotenv-1234567890"

    def test_dotenv_explicit_path(self, tmp_path, monkeypatch):
        """Explicit --env-file is used over auto-detection."""
        monkeypatch.delenv("EXPLICIT_ENV_KEY", raising=False)
        env_dir = tmp_path / "envs"
        env_dir.mkdir()
        env_path = env_dir / "prod.env"
        env_path.write_text("EXPLICIT_ENV_KEY=sk-explicit-9876543210\n")
        data = {
            "models": [
                {
                    "public_name": "test",
                    "provider": "openai",
                    "provider_model": "gpt-4o",
                    "api_key": "${EXPLICIT_ENV_KEY}",
                }
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path, env_file=env_path)
        assert errors == []
        assert models_file is not None
        assert models_file.models[0].api_key == "sk-explicit-9876543210"

    def test_dotenv_does_not_override_existing(self, tmp_path, monkeypatch):
        """Existing env vars take priority over .env values."""
        monkeypatch.setenv("PRIORITY_KEY", "sk-from-shell-1234567890")
        (tmp_path / ".env").write_text("PRIORITY_KEY=sk-from-dotenv-0000000000\n")
        data = {
            "models": [
                {
                    "public_name": "test",
                    "provider": "openai",
                    "provider_model": "gpt-4o",
                    "api_key": "${PRIORITY_KEY}",
                }
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert errors == []
        assert models_file is not None
        assert models_file.models[0].api_key == "sk-from-shell-1234567890"

    def test_missing_env_var(self, tmp_path, monkeypatch):
        monkeypatch.delenv("NONEXISTENT_KEY_XYZ", raising=False)
        data = {
            "models": [
                {
                    "public_name": "test",
                    "provider": "openai",
                    "provider_model": "gpt-4o",
                    "api_key": "${NONEXISTENT_KEY_XYZ}",
                }
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert models_file is None
        assert any("NONEXISTENT_KEY_XYZ" in e.message for e in errors)

    def test_schema_errors_collected(self, tmp_path):
        data = {
            "models": [
                {
                    "public_name": "",
                    "provider": "openai",
                    "provider_model": "gpt-4o",
                },
                {
                    "public_name": "test",
                    "provider": "",
                    "provider_model": "gpt-4o",
                },
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert models_file is None
        assert len(errors) >= 2

    def test_defaults_merged(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_KEY", "sk-1234567890abcdef")
        data = {
            "defaults": {
                "api_key": "${MY_KEY}",
                "mode": "chat",
                "max_retries": 3,
            },
            "models": [
                {
                    "public_name": "m1",
                    "provider": "openai",
                    "provider_model": "gpt-4o",
                    "max_retries": 5,  # overrides default
                }
            ],
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert errors == []
        assert models_file is not None
        assert models_file.models[0].api_key == "sk-1234567890abcdef"
        assert models_file.models[0].max_retries == 5  # model wins
        assert models_file.models[0].mode == "chat"  # from defaults

    def test_semantic_api_key_too_short(self, tmp_path):
        data = {
            "models": [
                {
                    "public_name": "test",
                    "provider": "openai",
                    "provider_model": "gpt-4o",
                    "api_key": "short",
                }
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert models_file is None
        assert any("api_key" in e.field for e in errors)

    def test_duplicate_public_name(self, tmp_path):
        data = {
            "models": [
                {"public_name": "dup", "provider": "a", "provider_model": "m1"},
                {"public_name": "dup", "provider": "b", "provider_model": "m2"},
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        models_file, errors = service.load_and_validate(path)
        assert models_file is None
        assert any("duplicate" in e.message for e in errors)

    def test_duplicate_against_proxy(self, tmp_path):
        """Model name already exists on proxy → validation error."""
        data = {
            "models": [
                {"public_name": "gpt-4o", "provider": "openai", "provider_model": "gpt-4o"},
                {"public_name": "new-model", "provider": "openai", "provider_model": "gpt-4"},
            ]
        }
        path = _write_yaml(tmp_path, data)
        service = self._make_service()
        # Simulate proxy already has "gpt-4o"
        service.client.list_models.return_value = [
            {"model_name": "gpt-4o", "litellm_params": {"model": "openai/gpt-4o"}},
        ]
        models_file, errors = service.load_and_validate(path)
        assert models_file is None
        assert any("already exists" in e.message for e in errors)
        # Only gpt-4o should fail, not new-model
        dup_errors = [e for e in errors if "already exists" in e.message]
        assert len(dup_errors) == 1
        assert dup_errors[0].model_name == "gpt-4o"


class TestBuildApiPayload:
    def test_full_payload(self):
        service = ModelApplyService(MagicMock())
        model = ModelEntry(
            public_name="gpt-4o",
            provider="openai",
            provider_model="gpt-4o",
            api_key="sk-test",
            api_base="https://api.openai.com/v1",
            max_retries=3,
            timeout=60,
            mode="chat",
            input_cost_per_token=0.0025,
        )
        payload = service.build_api_payload(model)
        assert payload["model_name"] == "gpt-4o"
        assert payload["litellm_params"]["model"] == "openai/gpt-4o"
        assert payload["litellm_params"]["api_key"] == "sk-test"
        assert payload["litellm_params"]["api_base"] == "https://api.openai.com/v1"
        assert payload["litellm_params"]["max_retries"] == 3
        assert payload["litellm_params"]["timeout"] == 60
        assert payload["model_info"]["mode"] == "chat"
        assert payload["model_info"]["input_cost_per_token"] == 0.0025

    def test_minimal_payload(self):
        service = ModelApplyService(MagicMock())
        model = ModelEntry(
            public_name="test",
            provider="anthropic",
            provider_model="claude-3",
        )
        payload = service.build_api_payload(model)
        assert payload["model_name"] == "test"
        assert payload["litellm_params"]["model"] == "anthropic/claude-3"
        assert "api_key" not in payload["litellm_params"]
        assert "model_info" not in payload


class TestApply:
    def test_all_succeed(self):
        client = MagicMock()
        client.create_model.return_value = {"status": "ok"}
        service = ModelApplyService(client)

        models = [
            ModelEntry(public_name="a", provider="openai", provider_model="gpt-4o"),
            ModelEntry(public_name="b", provider="anthropic", provider_model="claude-3"),
        ]
        report = service.apply(models)
        assert report.total == 2
        assert report.created == 2
        assert report.failed == 0
        assert client.create_model.call_count == 2

    def test_partial_failure(self):
        from llm_cli.core.client import APIError

        client = MagicMock()
        client.create_model.side_effect = [
            {"status": "ok"},
            APIError("model already exists", 400),
        ]
        service = ModelApplyService(client)

        models = [
            ModelEntry(public_name="a", provider="openai", provider_model="gpt-4o"),
            ModelEntry(public_name="b", provider="anthropic", provider_model="claude-3"),
        ]
        report = service.apply(models)
        assert report.total == 2
        assert report.created == 1
        assert report.failed == 1
        assert report.results[0].success is True
        assert report.results[1].success is False

    def test_skipped_tracked(self):
        client = MagicMock()
        client.create_model.return_value = {"status": "ok"}
        service = ModelApplyService(client)

        # Only pass 1 model (the other was skipped due to test failure)
        models = [
            ModelEntry(public_name="a", provider="openai", provider_model="gpt-4o"),
        ]
        report = service.apply(models)
        report.skipped = 2  # set by command layer
        assert report.total == 1
        assert report.created == 1
        assert report.skipped == 2


class TestTestModels:
    @patch.object(LiteLLMClient, "test_model_completion", return_value=(True, "OK"))
    def test_all_pass(self, mock_test):
        service = ModelApplyService(MagicMock())
        models_file = ModelsFile(
            models=[
                ModelEntry(public_name="a", provider="openai", provider_model="gpt-4o"),
                ModelEntry(public_name="b", provider="anthropic", provider_model="claude-3"),
            ]
        )
        results = service.test_models(models_file)
        assert len(results) == 2
        assert all(r.passed for r in results)
        assert mock_test.call_count == 2

    @patch.object(
        LiteLLMClient,
        "test_model_completion",
        side_effect=[(True, "OK"), (False, "Auth failed")],
    )
    def test_partial_fail(self, mock_test):
        service = ModelApplyService(MagicMock())
        models_file = ModelsFile(
            models=[
                ModelEntry(public_name="a", provider="openai", provider_model="gpt-4o"),
                ModelEntry(public_name="b", provider="anthropic", provider_model="claude-3"),
            ]
        )
        results = service.test_models(models_file)
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[1].message == "Auth failed"


class TestValidationErrorStr:
    def test_with_name_and_index(self):
        ve = ValidationError(model_index=0, model_name="gpt-4o", field="api_key", message="too short")
        assert str(ve) == "gpt-4o (models[0]).api_key: too short"

    def test_without_name(self):
        ve = ValidationError(model_index=1, model_name=None, field="provider", message="required")
        assert str(ve) == "models[1].provider: required"

    def test_without_index(self):
        ve = ValidationError(model_index=None, model_name=None, field="file", message="bad")
        assert str(ve) == "file: bad"
