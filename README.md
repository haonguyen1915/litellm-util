# LiteLLM CLI (`llm`)

CLI tool for managing [LiteLLM Proxy Server](https://docs.litellm.ai/) - models, virtual keys, teams, and multi-environment configurations.

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
git clone <repo-url>
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

# 5. Create a team with budget
llm team create
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

Subsequent runs let you add new environments to existing orgs or create new orgs.

---

### `llm config`

Manage configurations and switch environments.

```bash
# List all orgs & environments
llm config list

# Show current active config
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
      prod:
        url: https://litellm.my-company.com
        master_key: sk-prod-xxx
default:
  organization: my-company
  environment: dev
```

---

### `llm provider`

Browse supported LLM providers and their models. This is a static reference - no proxy connection needed.

```bash
# List all supported providers
llm provider list
```

Output:

```
                         Supported Providers
┏━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ #  ┃ Provider  ┃ Description                        ┃    Models ┃
┡━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 1  │ openai    │ OpenAI (GPT-4, GPT-3.5, o1)       │  9 models │
│ 2  │ anthropic │ Anthropic (Claude 4, Claude 3.5)   │  7 models │
│ 3  │ azure     │ Azure OpenAI Service               │  5 models │
│ 4  │ vertex_ai │ Google Vertex AI (Gemini)          │  4 models │
│ 5  │ bedrock   │ AWS Bedrock                        │ 12 models │
│ 6  │ groq      │ Groq (Ultra-fast inference)        │  5 models │
│ 7  │ mistral   │ Mistral AI                         │  6 models │
│ 8  │ deepseek  │ DeepSeek                           │  3 models │
│ 9  │ cohere    │ Cohere                             │  4 models │
│ 10 │ ollama    │ Ollama (Local models)              │  8 models │
└────┴───────────┴────────────────────────────────────┴───────────┘
```

```bash
# List models for a provider (interactive - allows selecting a model for details)
llm provider models anthropic

# Non-interactive (just print the table)
llm provider models anthropic -n

# Filter by capability
llm provider models openai -c vision
```

---

### `llm model`

Manage models deployed on the LiteLLM Proxy. Requires a running proxy.

```bash
# List models on the proxy
llm model list

# Create model (interactive)
llm model create

# Create model (non-interactive)
llm model create --provider anthropic --model claude-sonnet-4-20250514 --alias claude-sonnet

# Create with API key
llm model create -p openai -m openai/gpt-4o -a gpt-4o -k sk-xxx

# Delete model (interactive selection)
llm model delete

# Delete model (with confirmation skip)
llm model delete my-model --yes
```

**Global flags** for all proxy commands:

```bash
# Override organization
llm model list --org my-company

# Override environment
llm model list --env prod

# Combine both
llm model list --org my-company --env prod
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
llm team create --id backend --name "Backend Team" --budget 500

# Create team with model restrictions
llm team create --id mobile --name "Mobile Team" --models "gpt-4o-mini,claude-haiku"

# Update team (interactive - choose what to update)
llm team update

# Update team directly
llm team update backend --name "Backend Engineers" --budget 1000

# Add/remove models
llm team update backend --add-models "gpt-4o"
llm team update backend --remove-models "gpt-3.5-turbo"

# Delete team (interactive selection)
llm team delete

# Delete team directly
llm team delete backend --yes
```

---

### `llm admin`

Enterprise proxy administration commands.

```bash
# Rotate master key (interactive - prompts for new key or auto-generates)
llm admin rotate-key

# With org/env override
llm admin rotate-key --org my-company --env prod
```

The `rotate-key` command:
1. Shows current context (org/env/url)
2. Prompts for a new key or auto-generates one (`sk-` prefixed)
3. Calls `POST /key/regenerate` to rotate and re-encrypt all model API keys in the DB
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

Output:

```
                    Command History
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ #  ┃ Command                            ┃ Last Run            ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ llm model list                     │ 2025-01-13 14:30:02 │
│ 2  │ llm key create --alias my-key      │ 2025-01-13 14:25:11 │
│ 3  │ llm config use my-org prod         │ 2025-01-13 13:10:45 │
│ 4  │ llm team list                      │ 2025-01-12 09:22:30 │
└────┴──────────────────────────────────────┴─────────────────────┘
```

History file location: `~/.litellm/history.jsonl`

---

## Multi-Environment Workflow

The CLI supports managing multiple organizations, each with multiple environments (dev, staging, prod).

```bash
# Set up first org
llm init
# Org ID: my-company
# Environment: dev
# URL: http://localhost:4000
# Master Key: sk-dev-xxx

# Add prod environment
llm init
# Select: my-company
# Environment: prod
# URL: https://litellm.my-company.com
# Master Key: sk-prod-xxx

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
    model.py           # llm model [list|create|delete]
    key.py             # llm key [list|create|delete]
    team.py            # llm team [list|get|create|delete|update]
    admin.py           # llm admin [rotate-key]
    history.py         # llm history
  core/
    config.py          # Config load/save (~/.litellm/)
    client.py          # LiteLLM Proxy HTTP client
    context.py         # Current org/env context
    history.py         # Command history tracking (~/.litellm/history.jsonl)
  models/              # Pydantic schemas
  providers/           # Static provider/model definitions
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
