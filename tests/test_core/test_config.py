"""Tests for config management."""

import pytest
import yaml

from llm_cli.core.config import load_config, save_config
from llm_cli.models.config import Config, DefaultContext, Environment, Organization


def test_load_config_empty(temp_config_dir):
    """Test loading config when no file exists."""
    config = load_config()
    assert config.organizations == {}
    assert config.default is None


def test_load_config_with_data(sample_config, temp_config_dir):
    """Test loading config with existing data."""
    config = load_config()

    assert "test-org" in config.organizations
    assert config.organizations["test-org"].name == "Test Organization"
    assert "dev" in config.organizations["test-org"].environments
    assert "prod" in config.organizations["test-org"].environments
    assert config.default.organization == "test-org"
    assert config.default.environment == "dev"


def test_save_config(temp_config_dir):
    """Test saving config to file."""
    config = Config(
        organizations={
            "my-org": Organization(
                name="My Organization",
                environments={
                    "dev": Environment(
                        url="http://localhost:4000",
                        master_key="sk-test",
                    ),
                },
            ),
        },
        default=DefaultContext(organization="my-org", environment="dev"),
    )

    save_config(config)

    # Verify file was created
    config_file = temp_config_dir / "config.yaml"
    assert config_file.exists()

    # Verify content
    with open(config_file) as f:
        data = yaml.safe_load(f)

    assert "my-org" in data["organizations"]
    assert data["organizations"]["my-org"]["name"] == "My Organization"
    assert data["default"]["organization"] == "my-org"
