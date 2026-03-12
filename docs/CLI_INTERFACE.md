# LiteLLM CLI Interface Design

## Overview

CLI tool để tương tác với LiteLLM Proxy Server, cho phép quản lý models, virtual keys, và teams thông qua command line.

**Command name:** `llm`

## Installation

```bash
# Install via pip (sau khi publish)
pip install litellm-util

# Hoặc install từ source
cd litellm-util
poetry install
```

---

## Configuration Structure

Tất cả config được lưu tại `~/.litellm/`

```
~/.litellm/
├── config.yaml          # Main configuration file
└── .current             # File lưu org/env đang active
```

### config.yaml Format

```yaml
organizations:
  acme-corp:                    # Organization ID (slug)
    name: "ACME Corporation"    # Display name
    environments:
      dev:
        url: "http://localhost:4000"
        master_key: "sk-dev-xxxx"
      prod:
        url: "https://litellm.acme.com"
        master_key: "sk-prod-xxxx"

  another-org:
    name: "Another Organization"
    environments:
      dev:
        url: "http://localhost:4001"
        master_key: "sk-xxxx"

default:
  organization: "acme-corp"
  environment: "dev"
```

---

## Commands Reference

### 1. Init Command

Khởi tạo hoặc thêm organization/environment mới.

```bash
llm init
```

**Interactive Flow:**

```
$ llm init

? Organization ID (slug): acme-corp
? Organization Name: ACME Corporation
? Environment name: dev
? LiteLLM Proxy URL: http://localhost:4000
? Master Key: sk-xxxx

✓ Configuration saved to ~/.litellm/config.yaml
✓ Set acme-corp/dev as active environment
```

**Add thêm environment cho org có sẵn:**

```
$ llm init

? Select or create organization:
  [1] acme-corp (ACME Corporation)
  [2] + Create new organization

  Enter choice: 1

? Environment name: prod
? LiteLLM Proxy URL: https://litellm.acme.com
? Master Key: sk-prod-xxxx

✓ Added environment 'prod' to acme-corp
```

---

### 2. Config Commands

Quản lý và switch giữa các org/environment.

#### 2.1 List configurations

```bash
llm config list
```

**Output:**

```
Organizations:
┌─────────────┬────────────────────┬──────────────┬─────────────────────────────┐
│ Org ID      │ Name               │ Environment  │ URL                         │
├─────────────┼────────────────────┼──────────────┼─────────────────────────────┤
│ acme-corp   │ ACME Corporation   │ dev          │ http://localhost:4000       │
│             │                    │ prod         │ https://litellm.acme.com    │
├─────────────┼────────────────────┼──────────────┼─────────────────────────────┤
│ another-org │ Another Org        │ dev          │ http://localhost:4001       │
└─────────────┴────────────────────┴──────────────┴─────────────────────────────┘

Current: acme-corp / dev
```

#### 2.2 Switch environment

```bash
llm config use
```

**Interactive Flow:**

```
$ llm config use

? Select organization:
  [1] acme-corp (ACME Corporation)
  [2] another-org (Another Org)

  Enter choice: 1

? Select environment:
  [1] dev (http://localhost:4000)
  [2] prod (https://litellm.acme.com)

  Enter choice: 2

✓ Switched to acme-corp / prod
```

**Direct switch (non-interactive):**

```bash
llm config use acme-corp prod
```

#### 2.3 Show current context

```bash
llm config current
```

**Output:**

```
Organization: acme-corp (ACME Corporation)
Environment:  prod
URL:          https://litellm.acme.com
```

---

### 3. Provider Commands

Truy vấn thông tin về các providers và models mà LiteLLM hỗ trợ.

#### 3.1 List providers

```bash
llm provider list
```

**Output:**

```
Supported Providers:
┌─────┬────────────────┬─────────────────────────────────────────┬────────────┐
│ #   │ Provider       │ Description                             │ Models     │
├─────┼────────────────┼─────────────────────────────────────────┼────────────┤
│ 1   │ openai         │ OpenAI (GPT-4, GPT-3.5, etc.)           │ 15 models  │
│ 2   │ anthropic      │ Anthropic (Claude 3, Claude 3.5)        │ 8 models   │
│ 3   │ azure          │ Azure OpenAI Service                    │ 12 models  │
│ 4   │ vertex_ai      │ Google Vertex AI (Gemini, PaLM)         │ 10 models  │
│ 5   │ bedrock        │ AWS Bedrock                             │ 20 models  │
│ 6   │ cohere         │ Cohere (Command, Embed)                 │ 6 models   │
│ 7   │ huggingface    │ Hugging Face Inference                  │ Custom     │
│ 8   │ ollama         │ Ollama (Local models)                   │ Custom     │
│ 9   │ groq           │ Groq (Fast inference)                   │ 5 models   │
│ 10  │ mistral        │ Mistral AI                              │ 4 models   │
│ 11  │ deepseek       │ DeepSeek                                │ 3 models   │
│ 12  │ custom_openai  │ OpenAI-compatible endpoints             │ Custom     │
└─────┴────────────────┴─────────────────────────────────────────┴────────────┘

Use 'llm provider models <provider>' to see available models
```

#### 3.2 List models by provider

```bash
llm provider models <provider>
```

**Example - Anthropic:**

```
$ llm provider models anthropic

Anthropic Models:
┌─────┬────────────────────────────────┬───────────────┬─────────────┬────────────────┐
│ #   │ Model ID                       │ Context       │ Max Output  │ Input/Output $ │
├─────┼────────────────────────────────┼───────────────┼─────────────┼────────────────┤
│ 1   │ claude-opus-4-20250514         │ 200K          │ 32K         │ $15 / $75      │
│ 2   │ claude-sonnet-4-20250514       │ 200K          │ 64K         │ $3 / $15       │
│ 3   │ claude-3-5-sonnet-20241022     │ 200K          │ 8K          │ $3 / $15       │
│ 4   │ claude-3-5-haiku-20241022      │ 200K          │ 8K          │ $1 / $5        │
│ 5   │ claude-3-opus-20240229         │ 200K          │ 4K          │ $15 / $75      │
│ 6   │ claude-3-sonnet-20240229       │ 200K          │ 4K          │ $3 / $15       │
│ 7   │ claude-3-haiku-20240307        │ 200K          │ 4K          │ $0.25 / $1.25  │
└─────┴────────────────────────────────┴───────────────┴─────────────┴────────────────┘

Prices are per 1M tokens
```

**Example - OpenAI:**

```
$ llm provider models openai

OpenAI Models:
┌─────┬────────────────────────────────┬───────────────┬─────────────┬────────────────┐
│ #   │ Model ID                       │ Context       │ Max Output  │ Input/Output $ │
├─────┼────────────────────────────────┼───────────────┼─────────────┼────────────────┤
│ 1   │ gpt-4o                         │ 128K          │ 16K         │ $2.50 / $10    │
│ 2   │ gpt-4o-mini                    │ 128K          │ 16K         │ $0.15 / $0.60  │
│ 3   │ gpt-4-turbo                    │ 128K          │ 4K          │ $10 / $30      │
│ 4   │ gpt-4-turbo-preview            │ 128K          │ 4K          │ $10 / $30      │
│ 5   │ gpt-4                          │ 8K            │ 4K          │ $30 / $60      │
│ 6   │ gpt-3.5-turbo                  │ 16K           │ 4K          │ $0.50 / $1.50  │
│ 7   │ o1                             │ 200K          │ 100K        │ $15 / $60      │
│ 8   │ o1-mini                        │ 128K          │ 65K         │ $3 / $12       │
│ 9   │ o1-preview                     │ 128K          │ 32K         │ $15 / $60      │
└─────┴────────────────────────────────┴───────────────┴─────────────┴────────────────┘

Prices are per 1M tokens
```

**Interactive mode (chọn provider → chọn model):**

```
$ llm provider models

? Select provider:
  [1] openai
  [2] anthropic
  [3] azure
  [4] vertex_ai
  [5] bedrock
  [6] cohere
  [7] groq
  [8] mistral
  [9] deepseek

  Enter choice: 2

Anthropic Models:
┌─────┬────────────────────────────────┬───────────────┬─────────────┬────────────────┐
│ #   │ Model ID                       │ Context       │ Max Output  │ Input/Output $ │
├─────┼────────────────────────────────┼───────────────┼─────────────┼────────────────┤
│ 1   │ claude-opus-4-20250514         │ 200K          │ 32K         │ $15 / $75      │
│ 2   │ claude-sonnet-4-20250514       │ 200K          │ 64K         │ $3 / $15       │
│ 3   │ claude-3-5-sonnet-20241022     │ 200K          │ 8K          │ $3 / $15       │
│ 4   │ claude-3-5-haiku-20241022      │ 200K          │ 8K          │ $1 / $5        │
│ 5   │ claude-3-opus-20240229         │ 200K          │ 4K          │ $15 / $75      │
│ 6   │ claude-3-sonnet-20240229       │ 200K          │ 4K          │ $3 / $15       │
│ 7   │ claude-3-haiku-20240307        │ 200K          │ 4K          │ $0.25 / $1.25  │
└─────┴────────────────────────────────┴───────────────┴─────────────┴────────────────┘

? Select model (or press Enter to skip):
  Enter choice: 2

Model Details:
┌────────────────────┬─────────────────────────────────────────────────┐
│ Model ID           │ claude-sonnet-4-20250514                        │
│ Provider           │ anthropic                                       │
│ Context Window     │ 200,000 tokens                                  │
│ Max Output         │ 64,000 tokens                                   │
│ Input Price        │ $3.00 / 1M tokens                               │
│ Output Price       │ $15.00 / 1M tokens                              │
│ Capabilities       │ vision, tools, streaming                        │
│ Training Cutoff    │ April 2025                                      │
└────────────────────┴─────────────────────────────────────────────────┘

? What would you like to do?
  [1] Add to proxy (llm model create)
  [2] Copy model ID to clipboard
  [3] Back to model list
  [q] Quit

  Enter choice: 1

→ Starting model creation with claude-sonnet-4-20250514...

? Model alias (display name): claude-sonnet
? API Key (or press Enter to use env var): sk-ant-xxxx

✓ Model 'claude-sonnet' created successfully
```

**Interactive với provider đã chỉ định:**

```
$ llm provider models anthropic

Anthropic Models:
┌─────┬────────────────────────────────┬───────────────┬─────────────┬────────────────┐
│ #   │ Model ID                       │ Context       │ Max Output  │ Input/Output $ │
├─────┼────────────────────────────────┼───────────────┼─────────────┼────────────────┤
│ 1   │ claude-opus-4-20250514         │ 200K          │ 32K         │ $15 / $75      │
│ ... │ ...                            │ ...           │ ...         │ ...            │
└─────┴────────────────────────────────┴───────────────┴─────────────┴────────────────┘

? Select model (or press Enter to skip): 1

Model Details:
...
```

**Non-interactive mode (chỉ list, không prompt):**

```bash
# Chỉ list models, không interactive
llm provider models anthropic --no-interactive

# Hoặc short flag
llm provider models anthropic -n
```

**Filter by capability:**

```bash
# Only show models with vision capability
llm provider models openai --capability vision

# Only show models with function calling
llm provider models anthropic --capability tools
```

---

### 4. Model Commands

Quản lý models trên LiteLLM Proxy.

#### 4.1 List models

```bash
llm model list
```

**Output:**

```
Models on acme-corp/prod:
┌─────┬─────────────────────────┬─────────────┬─────────────────────────────────┐
│ #   │ Model Name              │ Provider    │ LiteLLM Model                   │
├─────┼─────────────────────────┼─────────────┼─────────────────────────────────┤
│ 1   │ gpt-4-turbo             │ openai      │ gpt-4-turbo-preview             │
│ 2   │ claude-3-opus           │ anthropic   │ claude-3-opus-20240229          │
│ 3   │ gemini-pro              │ vertex_ai   │ gemini-pro                      │
└─────┴─────────────────────────┴─────────────┴─────────────────────────────────┘

Total: 3 models
```

#### 4.2 Create model

```bash
llm model create
```

**Interactive Flow:**

```
$ llm model create

? Select provider:
  [1] openai
  [2] anthropic
  [3] azure
  [4] vertex_ai
  [5] bedrock
  [6] cohere
  [7] huggingface
  [8] ollama
  [9] custom_openai

  Enter choice: 2

? Select model:
  [1] claude-3-opus-20240229
  [2] claude-3-sonnet-20240229
  [3] claude-3-haiku-20240307
  [4] claude-3-5-sonnet-20241022
  [5] claude-3-5-haiku-20241022

  Enter choice: 4

? Model alias (display name): claude-sonnet
? API Key (or press Enter to use env var): sk-ant-xxxx

✓ Model 'claude-sonnet' created successfully
  Provider: anthropic
  Model: claude-3-5-sonnet-20241022
```

**Non-interactive mode:**

```bash
llm model create \
  --provider anthropic \
  --model claude-3-5-sonnet-20241022 \
  --alias claude-sonnet \
  --api-key sk-ant-xxxx
```

#### 4.3 Delete model

```bash
llm model delete
```

**Interactive Flow:**

```
$ llm model delete

? Select model to delete:
  [1] gpt-4-turbo (openai)
  [2] claude-3-opus (anthropic)
  [3] gemini-pro (vertex_ai)

  Enter choice: 2

? Are you sure you want to delete 'claude-3-opus'? (y/N): y

✓ Model 'claude-3-opus' deleted
```

**Non-interactive mode:**

```bash
llm model delete claude-3-opus --yes
```

---

### 5. Virtual Key Commands

Quản lý API keys cho users/applications.

#### 5.1 List keys

```bash
llm key list
```

**Output:**

```
Virtual Keys on acme-corp/prod:
┌─────┬─────────────────┬─────────────────┬────────────┬─────────────┬─────────────┐
│ #   │ Key Alias       │ Key (masked)    │ Team       │ Budget      │ Expires     │
├─────┼─────────────────┼─────────────────┼────────────┼─────────────┼─────────────┤
│ 1   │ frontend-app    │ sk-...abc123    │ frontend   │ $100/month  │ Never       │
│ 2   │ backend-service │ sk-...def456    │ backend    │ $500/month  │ 2024-12-31  │
│ 3   │ test-key        │ sk-...ghi789    │ -          │ Unlimited   │ Never       │
└─────┴─────────────────┴─────────────────┴────────────┴─────────────┴─────────────┘

Total: 3 keys
```

#### 5.2 Create key

```bash
llm key create
```

**Interactive Flow:**

```
$ llm key create

? Key alias: mobile-app
? Assign to team? (y/N): y

? Select team:
  [1] frontend (Frontend Team)
  [2] backend (Backend Team)
  [3] ml-team (ML Team)

  Enter choice: 1

? Set budget limit? (y/N): y
? Monthly budget ($): 200

? Restrict to specific models? (y/N): y
? Select models (comma-separated):
  [1] gpt-4-turbo
  [2] claude-3-opus
  [3] gemini-pro

  Enter choices: 1,2

? Set expiration? (y/N): N

✓ Virtual key created:
  Alias: mobile-app
  Key: sk-litellm-xxxxxxxxxxxxxxxxxxxxxx
  Team: frontend
  Budget: $200/month
  Models: gpt-4-turbo, claude-3-opus

⚠️  Save this key! It won't be shown again.
```

**Non-interactive mode với flags:**

```bash
llm key create \
  --alias mobile-app \
  --team frontend \
  --budget 200 \
  --models gpt-4-turbo,claude-3-opus \
  --expires 2024-12-31
```

#### 5.3 Delete key

```bash
llm key delete
```

**Interactive Flow:**

```
$ llm key delete

? Select key to delete:
  [1] frontend-app (sk-...abc123)
  [2] backend-service (sk-...def456)
  [3] test-key (sk-...ghi789)

  Enter choice: 3

? Are you sure you want to delete 'test-key'? (y/N): y

✓ Key 'test-key' deleted
```

---

### 6. Team Commands

Quản lý teams và phân quyền.

#### 6.1 List teams

```bash
llm team list
```

**Output:**

```
Teams on acme-corp/prod:
┌─────┬─────────────┬─────────────────┬─────────────┬───────────────────────────────┐
│ #   │ Team ID     │ Name            │ Budget      │ Models                        │
├─────┼─────────────┼─────────────────┼─────────────┼───────────────────────────────┤
│ 1   │ frontend    │ Frontend Team   │ $500/month  │ gpt-4-turbo, claude-3-opus    │
│ 2   │ backend     │ Backend Team    │ $1000/month │ All models                    │
│ 3   │ ml-team     │ ML Team         │ Unlimited   │ claude-3-opus, gemini-pro     │
└─────┴─────────────┴─────────────────┴─────────────┴───────────────────────────────┘

Total: 3 teams
```

#### 6.2 Create team

```bash
llm team create
```

**Interactive Flow:**

```
$ llm team create

? Team ID (slug): data-science
? Team Name: Data Science Team

? Select models for team:
  [1] gpt-4-turbo
  [2] claude-3-opus
  [3] gemini-pro
  [a] All models

  Enter choices (comma-separated): 2,3

? Set monthly budget? (y/N): y
? Monthly budget ($): 2000

? Enable auto-reset monthly? (Y/n): y

✓ Team created:
  ID: data-science
  Name: Data Science Team
  Models: claude-3-opus, gemini-pro
  Budget: $2000/month (auto-reset)
```

**Non-interactive mode:**

```bash
llm team create \
  --id data-science \
  --name "Data Science Team" \
  --models claude-3-opus,gemini-pro \
  --budget 2000 \
  --reset-monthly
```

#### 6.3 Delete team

```bash
llm team delete
```

**Interactive Flow:**

```
$ llm team delete

? Select team to delete:
  [1] frontend (Frontend Team)
  [2] backend (Backend Team)
  [3] ml-team (ML Team)

  Enter choice: 3

⚠️  Warning: This will also revoke all keys assigned to this team!

? Are you sure you want to delete 'ml-team'? (y/N): y

✓ Team 'ml-team' deleted
```

#### 6.4 Update team

```bash
llm team update
```

**Interactive Flow:**

```
$ llm team update

? Select team to update:
  [1] frontend (Frontend Team)
  [2] backend (Backend Team)
  [3] data-science (Data Science Team)

  Enter choice: 1

Current team info:
  Name: Frontend Team
  Models: gpt-4-turbo, claude-3-opus
  Budget: $500/month

? What would you like to update?
  [1] Add models
  [2] Remove models
  [3] Update budget
  [4] Update name
  [m] Multiple options

  Enter choice: 1

Available models to add:
  [1] gemini-pro
  [2] mistral-large

  Enter choices (comma-separated): 1

✓ Team 'frontend' updated
  Models: gpt-4-turbo, claude-3-opus, gemini-pro
```

**Non-interactive mode:**

```bash
# Add models
llm team update frontend --add-models gemini-pro,mistral-large

# Remove models
llm team update frontend --remove-models gpt-4-turbo

# Update budget
llm team update frontend --budget 800

# Update name
llm team update frontend --name "Frontend & Mobile Team"

# Combined
llm team update frontend \
  --add-models gemini-pro \
  --budget 800 \
  --name "Frontend & Mobile Team"
```

---

## Global Flags

Các flags có thể dùng với mọi command:

| Flag | Short | Description |
|------|-------|-------------|
| `--org` | `-o` | Override organization (không cần switch) |
| `--env` | `-e` | Override environment |
| `--output` | | Output format: `table` (default), `json`, `yaml` |
| `--no-color` | | Disable colored output |
| `--verbose` | `-v` | Show detailed output |
| `--help` | `-h` | Show help |

**Examples:**

```bash
# List models trên prod mà không cần switch
llm model list --org acme-corp --env prod

# Output JSON format
llm team list --output json

# Verbose mode
llm model create -v
```

---

## Error Handling

### Connection errors

```
$ llm model list

✗ Error: Cannot connect to LiteLLM Proxy
  URL: http://localhost:4000

  Please check:
  - Is the proxy server running?
  - Is the URL correct?

  Run 'llm config current' to see current configuration
```

### Authentication errors

```
$ llm model create

✗ Error: Authentication failed
  Master key may be invalid or expired

  Run 'llm init' to update credentials
```

### Invalid selection

```
$ llm model delete

? Select model to delete:
  [1] gpt-4-turbo
  [2] claude-3-opus

  Enter choice: 5

✗ Invalid selection. Please enter a number between 1 and 2
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Connection error |
| 4 | Authentication error |
| 5 | Invalid input |

---

## Future Enhancements (v2)

- [ ] `llm usage` - Xem usage statistics
- [ ] `llm logs` - Xem request logs
- [ ] `llm spend` - Xem spending reports
- [ ] `llm budget alert` - Thiết lập budget alerts
- [ ] `llm model test` - Test model connectivity
- [ ] Shell completion (bash, zsh, fish)
