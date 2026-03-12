"""Tests for context management."""

import pytest

from llm_cli.core.context import ConfigurationError, get_current_context, set_current_context
from llm_cli.core.config import load_config, save_config


def test_get_current_context(sample_config, temp_config_dir):
    """Test getting current context with valid config."""
    ctx = get_current_context()

    assert ctx.organization_id == "test-org"
    assert ctx.organization_name == "Test Organization"
    assert ctx.environment == "dev"
    assert ctx.url == "http://localhost:4000"
    assert ctx.master_key == "sk-test-key-12345"


def test_get_current_context_with_override(sample_config, temp_config_dir):
    """Test getting context with org/env override."""
    ctx = get_current_context(org_override="test-org", env_override="prod")

    assert ctx.organization_id == "test-org"
    assert ctx.environment == "prod"
    assert ctx.url == "https://litellm.example.com"
    assert ctx.master_key == "sk-prod-key-67890"


def test_get_current_context_no_config(temp_config_dir):
    """Test getting context with no config raises error."""
    with pytest.raises(ConfigurationError, match="No organizations configured"):
        get_current_context()


def test_get_current_context_invalid_org(sample_config, temp_config_dir):
    """Test getting context with invalid org raises error."""
    with pytest.raises(ConfigurationError, match="not found"):
        get_current_context(org_override="invalid-org")


def test_get_current_context_invalid_env(sample_config, temp_config_dir):
    """Test getting context with invalid env raises error."""
    with pytest.raises(ConfigurationError, match="not found"):
        get_current_context(env_override="invalid-env")


def test_set_current_context(sample_config, temp_config_dir):
    """Test setting current context."""
    config = load_config()
    set_current_context(config, "test-org", "prod")
    save_config(config)

    # Reload and verify
    config = load_config()
    assert config.default.organization == "test-org"
    assert config.default.environment == "prod"
