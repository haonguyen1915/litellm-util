"""Command history tracking — stores invocations in ~/.litellm/history.jsonl."""

import json
from datetime import datetime, timezone
from pathlib import Path

from llm_cli.core.config import CONFIG_DIR, ensure_config_dir

HISTORY_FILE = CONFIG_DIR / "history.jsonl"


def record_command(args: list[str]) -> None:
    """Append command to history file.

    Args:
        args: sys.argv[1:] — the CLI arguments after the program name.
    """
    command = " ".join(args)
    if not command:
        return

    entry = {
        "command": command,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
    }

    ensure_config_dir()
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def load_history(limit: int = 50) -> list[dict]:
    """Load history, deduplicate by command string, sort latest-first.

    Args:
        limit: Maximum number of entries to return.

    Returns:
        List of dicts with 'command' and 'timestamp' keys,
        deduplicated by command (latest timestamp wins), sorted newest-first.
    """
    if not HISTORY_FILE.exists():
        return []

    seen: dict[str, str] = {}  # command -> latest timestamp
    with open(HISTORY_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                cmd = entry["command"]
                ts = entry["timestamp"]
                if cmd not in seen or ts > seen[cmd]:
                    seen[cmd] = ts
            except (json.JSONDecodeError, KeyError):
                continue

    entries = [{"command": cmd, "timestamp": ts} for cmd, ts in seen.items()]
    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    return entries[:limit]


def clear_history() -> bool:
    """Delete the history file.

    Returns:
        True if file was deleted, False if it didn't exist.
    """
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
        return True
    return False
