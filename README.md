# LiteLLM CLI (`llm`)

[![PyPI version](https://img.shields.io/pypi/v/litellm-util.svg)](https://pypi.org/project/litellm-util/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A powerful CLI tool for managing [LiteLLM Proxy Server](https://docs.litellm.ai/) - models, virtual keys, teams, usage analytics, and multi-environment configurations.

## Features

- **Model Management** - Create, list, delete, and bulk-apply models with connection testing
- **Virtual Key Management** - Create, update, test, and delete API keys with team/budget/model controls
- **Team Management** - Create teams with budgets, model restrictions, and member management
- **Usage Analytics** - Track spend by key, team, model with daily activity breakdowns
- **Multi-Environment** - Manage multiple orgs and environments (dev/staging/prod) from one CLI
- **Version-Aware** - Supports both LiteLLM Proxy v1 (<=1.72.x) and v2 (>=1.80.x)
- **Interactive & Scriptable** - Full interactive prompts or non-interactive flags for CI/CD
- **76+ Providers** - Browse and deploy models from OpenAI, Anthropic, Azure, AWS Bedrock, Vertex AI, and more

## Installation

Requires Python 3.10+.

```bash
pip install litellm-util
```

Or with [pipx](https://pipx.pypa.io/) (recommended for CLI tools):

```bash
pipx install litellm-util
```

Verify:

```bash
llm --help
```

### From source

```bash
git clone https://github.com/haonguyen1915/litellm-util.git
cd litellm-util
poetry install
```

## Quick Start

```bash
# 1. Initialize - set up your first org & environment
llm init

# 2. Browse available providers & models
llm provider list
llm provider models anthropic

# 3. Add a model to your proxy
llm model create

# 4. Generate a virtual API key
llm key create

# 5. Test the key
llm key test

# 6. Check usage
llm usage summary --last 7d
```

## Commands

### `llm init`

Interactive setup wizard. Creates or adds organizations and environments to `~/.litellm/config.yaml`.

```bash
llm init
```

First run prompts:
- Organization ID (slug, e.g. `my-company`)
- Organization Name
- Environment name (`dev`, `prod`, `staging`)
- LiteLLM Proxy URL (e.g. `https://litellm.example.com`)
- Master Key
- Proxy Version (`v1` for <=1.72.x or `v2` for >=1.80.x)

Subsequent runs let you add new environments to existing orgs or create new orgs.

---

### `llm config`

Manage configurations and switch environments.

```bash
# List all orgs & environments
llm config list

# Show current active config (org, env, URL, version)
llm config current

# Switch environment (interactive)
llm config use

# Switch environment (direct)
llm config use my-org prod
```

Config file location: `~/.litellm/config.yaml`

Example config structure:

```yaml
organizations:
  my-company:
    name: My Company
    environments:
      dev:
        url: http://localhost:4000
        master_key: sk-dev-xxx
        version: v2
      prod:
        url: https://litellm.my-company.com
        master_key: sk-prod-xxx
        version: v1    # for LiteLLM <= 1.72.x
default:
  organization: my-company
  environment: dev
```

---

### `llm provider`

Browse 76+ supported LLM providers and their models. This is a static reference - no proxy connection needed.

```bash
# List all supported providers
llm provider list

# Search providers by name
llm provider list --search vertex
```

```bash
# List models for a provider (interactive - select model for details)
llm provider models anthropic

# Non-interactive (just print the table)
llm provider models anthropic -n

# Sort by price or context window
llm provider models openai --sort price
llm provider models openai --sort context

# Filter by capability
llm provider models openai -c vision
```

---

### `llm model`

Manage models deployed on the LiteLLM Proxy. Requires a running proxy.

```bash
# List models on the proxy
llm model list

# Create model (interactive - guided wizard)
llm model create

# Create model (non-interactive)
llm model create --provider anthropic --model claude-sonnet-4-20250514 --alias claude-sonnet

# Create with API key
llm model create -p openai -m openai/gpt-4o -a gpt-4o -k sk-xxx

# Create with specific mode (embedding, image_generation, etc.)
llm model create -p openai -m openai/text-embedding-3-small -a embedding --mode embedding

# Replace existing model (delete old + create new)
llm model create -p anthropic -m claude-sonnet-4-20250514 -a claude-sonnet --replace

# Bulk create models from YAML file
llm model apply -f models.yaml

# Bulk apply with replace mode and skip testing
llm model apply -f models.yaml --replace --skip-test

# Dry-run to validate YAML without creating
llm model apply -f models.yaml --dry-run

# Use custom .env file for API keys
llm model apply -f models.yaml --env-file /path/to/.env

# Delete model (interactive selection)
llm model delete

# Delete model (with confirmation skip)
llm model delete my-model --yes
```

#### Model Modes

When creating models, use `--mode` to specify the model type:

| Mode | Description |
|------|-------------|
| `chat` | Chat completion (default) |
| `embedding` | Text embedding |
| `image_generation` | Image generation |
| `audio_transcription` | Audio transcription |
| `text_completion` | Text completion |

#### Model Apply YAML Format

```yaml
defaults:
  replace: true  # Replace existing models by default

models:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY

  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-4-20250514
      api_key: os.environ/ANTHROPIC_API_KEY
```

---

### `llm key`

Manage virtual API keys on the proxy.

```bash
# List all keys
llm key list

# Create key (interactive - prompts for team, budget, models, expiration)
llm key create

# Create key with options
llm key create --alias my-key --team backend --budget 100 --models "gpt-4o,claude-sonnet"

# Create key with expiration
llm key create --alias temp-key --expires 2025-12-31

# Update key name
llm key update my-key --name "New Key Name"

# Update key team assignment
llm key update my-key --team new-team

# Update key model access
llm key update my-key --models "gpt-4o,claude-sonnet"

# Grant access to all team models
llm key update my-key --models all-team-models

# Test a key with a chat completion request
llm key test

# Test with specific key and model
llm key test --key sk-xxx --model gpt-4o

# Delete key (interactive selection)
llm key delete

# Delete key by alias
llm key delete my-key --yes
```

When creating a key, it is automatically copied to clipboard and displayed once. Save it - it won't be shown again.

---

### `llm team`

Manage teams and their permissions/budgets.

```bash
# List all teams
llm team list

# Get team details (interactive selection)
llm team get

# Get team details (direct)
llm team get <team-id>

# Create team (interactive)
llm team create

# Create team with options
llm team create --name "Backend Team" --budget 500 --models "gpt-4o,claude-sonnet"

# Create team with auto-resetting monthly budget
llm team create --name "Mobile Team" --budget 200 --reset-monthly

# Update team (interactive - choose what to update)
llm team update

# Update team directly
llm team update backend --name "Backend Engineers" --budget 1000

# Add/remove models
llm team update backend --add-models "gpt-4o"
llm team update backend --remove-models "gpt-3.5-turbo"

# Delete team
llm team delete backend --yes
```

---

### `llm usage`

View spend and usage analytics. Supports date range filtering with explicit dates or shorthand.

```bash
# Spend summary grouped by tag
llm usage summary --last 7d

# Spend by API key
llm usage by-key --last 30d

# Spend by team
llm usage by-team --last 7d

# Spend by model
llm usage by-model --last 30d

# Daily activity breakdown (user scope)
llm usage activity --last 7d

# Daily activity breakdown (team scope)
llm usage activity --scope team --last 7d

# Spend logs with model breakdown
llm usage logs --last 7d

# Filter logs by request ID
llm usage logs --request-id req_xxx

# Custom date range
llm usage summary --start 2025-01-01 --end 2025-01-31

# Show top N results
llm usage by-key --last 30d --top 10
```

#### Date Filtering

All usage commands support flexible date filtering:

| Flag | Description | Example |
|------|-------------|---------|
| `--last 1h` | Last 1 hour | `llm usage summary --last 1h` |
| `--last 1d` | Last 1 day | `llm usage by-key --last 1d` |
| `--last 7d` | Last 7 days | `llm usage by-team --last 7d` |
| `--last 15d` | Last 15 days | `llm usage activity --last 15d` |
| `--last 30d` | Last 30 days | `llm usage by-model --last 30d` |
| `--start / --end` | Explicit range | `--start 2025-01-01 --end 2025-01-31` |

---

### `llm admin`

Enterprise proxy administration commands.

```bash
# Rotate master key (interactive)
llm admin rotate-key

# With org/env override
llm admin rotate-key --org my-company --env prod
```

The `rotate-key` command:
1. Shows current context (org/env/url)
2. Prompts for a new key or auto-generates one (`sk-` prefixed)
3. Calls the proxy to rotate and re-encrypt all model API keys in the DB
4. Offers to update local config with the new key
5. Copies new key to clipboard

> **Note:** This is a LiteLLM Enterprise feature. Requires an Enterprise license on the proxy.

---

### `llm history`

View CLI command history. Every invocation is recorded (deduplicated by command string, keeping the latest timestamp).

```bash
# Show recent commands (default: 50)
llm history

# Limit entries
llm history -n 10

# Clear all history
llm history --clear
```

---

## Global Flags

All proxy commands support overriding the active organization and environment:

```bash
# Override organization
llm model list --org my-company

# Override environment
llm model list --env prod

# Combine both
llm model list --org my-company --env prod
```

---

## Multi-Environment Workflow

The CLI supports managing multiple organizations, each with multiple environments (dev, staging, prod).

```bash
# Set up first org
llm init
# Org ID: my-company
# Environment: dev
# URL: http://localhost:4000
# Version: v2

# Add prod environment
llm init
# Select: my-company
# Environment: prod
# URL: https://litellm.my-company.com
# Version: v1

# Switch between environments
llm config use my-company dev
llm config use my-company prod

# Or interactively
llm config use

# Check which environment is active
llm config current

# Run commands against a specific environment without switching
llm model list --env prod
llm key list --org my-company --env staging
```

---

## Proxy Version Support

The CLI supports both LiteLLM Proxy versions with automatic API adaptation:

| Version | LiteLLM Proxy | Description |
|---------|---------------|-------------|
| `v2` (default) | >= 1.80.x | Uses newer aggregated API endpoints |
| `v1` | <= 1.72.x | Uses legacy activity-based endpoints with data flattening |

Set the version per environment in `~/.litellm/config.yaml`:

```yaml
environments:
  prod:
    url: https://litellm.example.com
    master_key: sk-xxx
    version: v1   # or v2
```

Or configure during `llm init`.

---

## Development

```bash
# Install with dev dependencies
poetry install

# Run tests
pytest

# Run tests with coverage
pytest --cov=llm_cli --cov-report=html

# Lint
ruff check src/
ruff format src/

# Type check
mypy src/
```

### Integration Tests

Integration tests run against a real LiteLLM Proxy. Set credentials in `.env`:

```
TEST_LITELLM_URL=https://litellm.example.com
TEST_LITELLM_KEY=sk-your-master-key
```

```bash
# Run integration tests
pytest tests/test_core/test_client_integration.py -v

# Skip integration tests (they auto-skip if .env is not set)
pytest -k "not integration"
```

## Project Structure

```
src/llm_cli/
  main.py              # Typer app entry point
  commands/
    init.py            # llm init
    config.py          # llm config [list|use|current]
    provider.py        # llm provider [list|models]
    model.py           # llm model [list|create|apply|delete]
    key.py             # llm key [list|create|update|test|delete]
    team.py            # llm team [list|get|create|update|delete]
    usage.py           # llm usage [summary|by-key|by-team|by-model|activity|logs]
    admin.py           # llm admin [rotate-key]
    history.py         # llm history
  core/
    config.py          # Config load/save (~/.litellm/)
    client.py          # LiteLLM Proxy HTTP client (v1/v2 aware)
    context.py         # Current org/env context
    apply.py           # Bulk model apply logic
    history.py         # Command history tracking (~/.litellm/history.jsonl)
  models/              # Pydantic schemas
  providers/           # Static provider/model definitions (76+ providers)
  ui/
    console.py         # Rich console helpers
    prompts.py         # questionary wrappers
    tables.py          # Rich table builders
  utils/
    clipboard.py       # Copy to clipboard
    validators.py      # Input validators
```

## License

GPL-3.0-or-later