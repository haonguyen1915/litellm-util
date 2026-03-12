"""Core business logic."""

from llm_cli.core.config import (
    CONFIG_DIR,
    CONFIG_FILE,
    load_config,
    save_config,
)
from llm_cli.core.context import (
    CurrentContext,
    get_current_context,
    set_current_context,
)

__all__ = [
    "CONFIG_DIR",
    "CONFIG_FILE",
    "load_config",
    "save_config",
    "CurrentContext",
    "get_current_context",
    "set_current_context",
]
