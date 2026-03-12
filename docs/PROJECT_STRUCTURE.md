# Project Structure & Dependencies

## Tech Stack Overview

| Component | Library | Lý do chọn |
|-----------|---------|------------|
| CLI Framework | **Typer** | Type hints, auto-generate help, tích hợp Rich |
| Interactive Prompts | **questionary** | Beautiful prompts, style customization |
| Pretty Output | **Rich** | Tables, colors, progress bars, markdown |
| HTTP Client | **httpx** | Async support, modern API |
| Data Validation | **Pydantic** | Type safety, settings management |
| YAML Config | **PyYAML** | Config file parsing |
| Testing | **pytest** | Standard testing framework |

---

## Project Structure

```
litellm-util/
├── pyproject.toml              # Poetry config & dependencies
├── README.md                   # Project documentation
├── LICENSE
│
├── docs/
│   ├── CLI_INTERFACE.md        # CLI interface design
│   └── PROJECT_STRUCTURE.md    # This file
│
├── src/
│   └── llm_cli/                # Main package
│       ├── __init__.py
│       ├── __main__.py         # Entry point: python -m llm_cli
│       ├── main.py             # Typer app setup
│       │
│       ├── commands/           # CLI commands
│       │   ├── __init__.py
│       │   ├── init.py         # llm init
│       │   ├── config.py       # llm config [list|use|current]
│       │   ├── provider.py     # llm provider [list|models]
│       │   ├── model.py        # llm model [list|create|delete]
│       │   ├── key.py          # llm key [list|create|delete]
│       │   └── team.py         # llm team [list|create|delete|update]
│       │
│       ├── core/               # Core business logic
│       │   ├── __init__.py
│       │   ├── config.py       # Config management (~/.litellm/)
│       │   ├── client.py       # LiteLLM API client
│       │   └── context.py      # Current org/env context
│       │
│       ├── models/             # Pydantic models
│       │   ├── __init__.py
│       │   ├── config.py       # Config schema
│       │   ├── provider.py     # Provider & model info
│       │   ├── team.py         # Team schema
│       │   └── key.py          # Virtual key schema
│       │
│       ├── ui/                 # UI components
│       │   ├── __init__.py
│       │   ├── prompts.py      # questionary prompts
│       │   ├── tables.py       # Rich tables
│       │   └── console.py      # Rich console setup
│       │
│       ├── providers/          # Provider definitions
│       │   ├── __init__.py
│       │   ├── base.py         # Base provider class
│       │   ├── openai.py       # OpenAI models
│       │   ├── anthropic.py    # Anthropic models
│       │   ├── azure.py        # Azure models
│       │   ├── vertex.py       # Vertex AI models
│       │   └── ...
│       │
│       └── utils/              # Utilities
│           ├── __init__.py
│           ├── clipboard.py    # Copy to clipboard
│           └── validators.py   # Input validators
│
└── tests/
    ├── __init__.py
    ├── conftest.py             # Pytest fixtures
    ├── test_commands/
    │   ├── test_init.py
    │   ├── test_config.py
    │   └── ...
    ├── test_core/
    │   ├── test_config.py
    │   └── test_client.py
    └── test_ui/
        └── test_prompts.py
```

---

## Dependencies

### pyproject.toml

```toml
[tool.poetry]
name = "litellm-util"
version = "0.1.0"
description = "CLI tool for managing LiteLLM Proxy Server"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
license = "MIT"
packages = [{include = "llm_cli", from = "src"}]

[tool.poetry.scripts]
llm = "llm_cli.main:app"

[tool.poetry.dependencies]
python = "^3.10"

# CLI Framework
typer = {extras = ["all"], version = "^0.12.0"}

# Interactive Prompts
questionary = "^2.0.1"

# Pretty Output
rich = "^13.7.0"

# HTTP Client
httpx = "^0.27.0"

# Data Validation & Settings
pydantic = "^2.6.0"
pydantic-settings = "^2.2.0"

# Config
pyyaml = "^6.0.1"

# Clipboard
pyperclip = "^1.8.2"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.23.0"
mypy = "^1.8.0"
ruff = "^0.2.0"
pre-commit = "^3.6.0"

# Type stubs
types-pyyaml = "^6.0.12"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## Key Libraries Details

### 1. Typer - CLI Framework

```python
# src/llm_cli/main.py
import typer
from llm_cli.commands import config, model, key, team, provider, init

app = typer.Typer(
    name="llm",
    help="CLI tool for managing LiteLLM Proxy Server",
    no_args_is_help=True,
)

# Register sub-commands
app.add_typer(config.app, name="config")
app.add_typer(provider.app, name="provider")
app.add_typer(model.app, name="model")
app.add_typer(key.app, name="key")
app.add_typer(team.app, name="team")

# Direct command
app.command()(init.init)

if __name__ == "__main__":
    app()
```

### 2. Questionary - Interactive Prompts

```python
# src/llm_cli/ui/prompts.py
import questionary
from questionary import Style

# Custom style matching CLI theme
custom_style = Style([
    ('qmark', 'fg:cyan bold'),           # ? mark
    ('question', 'bold'),                  # Question text
    ('answer', 'fg:green'),               # Selected answer
    ('pointer', 'fg:cyan bold'),          # > pointer
    ('highlighted', 'fg:cyan bold'),      # Highlighted choice
    ('selected', 'fg:green'),             # Selected items
    ('separator', 'fg:gray'),             # Separator
    ('instruction', 'fg:gray italic'),    # Instructions
])

def select_from_list(
    message: str,
    choices: list[str],
    show_index: bool = True
) -> str | None:
    """Select single item from list with index numbers."""
    if show_index:
        indexed_choices = [f"[{i+1}] {c}" for i, c in enumerate(choices)]
    else:
        indexed_choices = choices

    return questionary.select(
        message,
        choices=indexed_choices,
        style=custom_style,
        use_shortcuts=True,
    ).ask()

def select_multiple(
    message: str,
    choices: list[str],
) -> list[str]:
    """Select multiple items from list."""
    return questionary.checkbox(
        message,
        choices=choices,
        style=custom_style,
    ).ask() or []

def text_input(
    message: str,
    default: str = "",
    password: bool = False,
    validate: callable = None,
) -> str:
    """Get text input from user."""
    if password:
        return questionary.password(
            message,
            style=custom_style,
            validate=validate,
        ).ask()

    return questionary.text(
        message,
        default=default,
        style=custom_style,
        validate=validate,
    ).ask()

def confirm(message: str, default: bool = False) -> bool:
    """Yes/No confirmation."""
    return questionary.confirm(
        message,
        default=default,
        style=custom_style,
    ).ask()
```

### 3. Rich - Pretty Output

```python
# src/llm_cli/ui/console.py
from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red bold",
    "highlight": "cyan bold",
})

console = Console(theme=custom_theme)

def success(message: str):
    console.print(f"✓ {message}", style="success")

def error(message: str):
    console.print(f"✗ {message}", style="error")

def warning(message: str):
    console.print(f"⚠️  {message}", style="warning")

def info(message: str):
    console.print(f"ℹ {message}", style="info")
```

```python
# src/llm_cli/ui/tables.py
from rich.table import Table
from llm_cli.ui.console import console

def print_models_table(models: list[dict]):
    """Print models in a pretty table."""
    table = Table(
        title="Models",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Model Name", style="white")
    table.add_column("Provider", style="green")
    table.add_column("LiteLLM Model", style="blue")

    for i, model in enumerate(models, 1):
        table.add_row(
            str(i),
            model["name"],
            model["provider"],
            model["litellm_model"],
        )

    console.print(table)
    console.print(f"\nTotal: {len(models)} models", style="dim")
```

### 4. Pydantic - Data Models

```python
# src/llm_cli/models/config.py
from pathlib import Path
from pydantic import BaseModel, Field

class Environment(BaseModel):
    url: str
    master_key: str

class Organization(BaseModel):
    name: str
    environments: dict[str, Environment]

class DefaultContext(BaseModel):
    organization: str
    environment: str

class Config(BaseModel):
    organizations: dict[str, Organization] = Field(default_factory=dict)
    default: DefaultContext | None = None

# src/llm_cli/models/provider.py
class ModelInfo(BaseModel):
    id: str
    provider: str
    context_window: int
    max_output: int
    input_price: float  # per 1M tokens
    output_price: float  # per 1M tokens
    capabilities: list[str] = []
    training_cutoff: str | None = None
```

### 5. HTTPX - API Client

```python
# src/llm_cli/core/client.py
import httpx
from llm_cli.core.context import get_current_context

class LiteLLMClient:
    def __init__(self):
        ctx = get_current_context()
        self.base_url = ctx.url
        self.headers = {
            "Authorization": f"Bearer {ctx.master_key}",
            "Content-Type": "application/json",
        }

    async def list_models(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/model/info",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()["data"]

    async def create_model(self, model_data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/model/new",
                headers=self.headers,
                json=model_data,
            )
            response.raise_for_status()
            return response.json()

    # ... more methods
```

---

## Config Management

### Config file location

```python
# src/llm_cli/core/config.py
from pathlib import Path
import yaml
from llm_cli.models.config import Config

CONFIG_DIR = Path.home() / ".litellm"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
CURRENT_FILE = CONFIG_DIR / ".current"

def ensure_config_dir():
    """Create config directory if not exists."""
    CONFIG_DIR.mkdir(exist_ok=True)

def load_config() -> Config:
    """Load config from file."""
    if not CONFIG_FILE.exists():
        return Config()

    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f) or {}

    return Config.model_validate(data)

def save_config(config: Config):
    """Save config to file."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config.model_dump(exclude_none=True), f, default_flow_style=False)
```

---

## Development Setup

```bash
# Clone repository
git clone <repo-url>
cd litellm-util

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run CLI
llm --help

# Run tests
pytest

# Run with coverage
pytest --cov=llm_cli --cov-report=html

# Lint & format
ruff check src/
ruff format src/

# Type check
mypy src/
```

---

## Entry Points

### __main__.py

```python
# src/llm_cli/__main__.py
from llm_cli.main import app

if __name__ == "__main__":
    app()
```

Cho phép chạy:
```bash
# Via poetry script
llm --help

# Via python module
python -m llm_cli --help
```

---

## Future Considerations

### Alternative Libraries

| Library | Thay thế cho | Khi nào dùng |
|---------|--------------|--------------|
| **InquirerPy** | questionary | Cần nhiều prompt types hơn |
| **click** | Typer | Không cần type hints |
| **aiohttp** | httpx | Cần WebSocket support |
| **textual** | Rich | Cần TUI (Terminal UI) phức tạp |

### Optional Features

```toml
[tool.poetry.extras]
tui = ["textual"]  # Full terminal UI
completion = ["shellingham"]  # Shell completion
```
