"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / ".litellm"
    config_dir.mkdir()

    # Patch the config paths
    monkeypatch.setattr("llm_cli.core.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("llm_cli.core.config.CONFIG_FILE", config_dir / "config.yaml")
    monkeypatch.setattr("llm_cli.core.config.CURRENT_FILE", config_dir / ".current")

    return config_dir


@pytest.fixture
def sample_config(temp_config_dir):
    """Create a sample config file for testing."""
    config_data = {
        "organizations": {
            "test-org": {
                "name": "Test Organization",
                "environments": {
                    "dev": {
                        "url": "http://localhost:4000",
                        "master_key": "sk-test-key-12345",
                    },
                    "prod": {
                        "url": "https://litellm.example.com",
                        "master_key": "sk-prod-key-67890",
                    },
                },
            },
        },
        "default": {
            "organization": "test-org",
            "environment": "dev",
        },
    }

    config_file = temp_config_dir / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    return config_data


@pytest.fixture
def cli_runner():
    """Get Typer CLI test runner."""
    from typer.testing import CliRunner

    return CliRunner()
