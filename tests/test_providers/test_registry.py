"""Tests for provider registry."""

import pytest

from llm_cli.providers import get_all_providers, get_provider, get_provider_ids


def test_get_all_providers():
    """Test getting all providers."""
    providers = get_all_providers()

    assert len(providers) > 0
    assert all(p.id for p in providers)
    assert all(p.name for p in providers)


def test_get_provider_ids():
    """Test getting provider IDs."""
    ids = get_provider_ids()

    assert "openai" in ids
    assert "anthropic" in ids
    assert "azure" in ids


def test_get_provider_valid():
    """Test getting a valid provider."""
    provider = get_provider("openai")

    assert provider is not None
    assert provider.id == "openai"
    assert provider.name == "OpenAI"
    assert len(provider.models) > 0


def test_get_provider_invalid():
    """Test getting an invalid provider returns None."""
    provider = get_provider("invalid-provider")
    assert provider is None


def test_provider_models_have_required_fields():
    """Test all provider models have required fields."""
    providers = get_all_providers()

    for provider in providers:
        for model in provider.models:
            assert model.id, f"Model missing id in {provider.id}"
            assert model.provider, f"Model missing provider in {provider.id}"
            assert model.context_window > 0, f"Invalid context_window in {model.id}"
            assert model.max_output > 0, f"Invalid max_output in {model.id}"
            assert model.input_price >= 0, f"Invalid input_price in {model.id}"
            assert model.output_price >= 0, f"Invalid output_price in {model.id}"
