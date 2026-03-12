"""Configuration management for ~/.litellm/ directory."""

from pathlib import Path

import yaml

from llm_cli.models.config import Config

CONFIG_DIR = Path.home() / ".litellm"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CURRENT_FILE = CONFIG_DIR / ".current"


def ensure_config_dir() -> None:
    """Create config directory if not exists."""
    CONFIG_DIR.mkdir(exist_ok=True)


def load_config() -> Config:
    """Load config from file.

    Returns:
        Config object, empty if file doesn't exist.
    """
    if not CONFIG_FILE.exists():
        return Config()

    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f) or {}

    return Config.model_validate(data)


def save_config(config: Config) -> None:
    """Save config to file.

    Args:
        config: Config object to save.
    """
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(
            config.model_dump(exclude_none=True),
            f,
            default_flow_style=False,
            sort_keys=False,
        )


def config_exists() -> bool:
    """Check if config file exists."""
    return CONFIG_FILE.exists()
