"""Rich table builders for various data types."""

from rich.table import Table

from llm_cli.models.key import VirtualKey
from llm_cli.models.provider import ModelInfo, ProviderInfo
from llm_cli.models.team import Team
from llm_cli.ui.console import console


def print_providers_table(providers: list[ProviderInfo]) -> None:
    """Print providers in a pretty table."""
    table = Table(
        title="Supported Providers",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Provider", style="white")
    table.add_column("Description", style="dim")
    table.add_column("Models", style="green", justify="right")

    for i, provider in enumerate(providers, 1):
        model_count = len(provider.models)
        models_str = f"{model_count} models" if model_count > 0 else "Custom"
        table.add_row(str(i), provider.id, provider.description, models_str)

    console.print(table)
    console.print("\nUse 'llm provider models <provider>' to see available models", style="dim")


def print_models_table(
    models: list[ModelInfo],
    title: str = "Models",
    page_size: int = 0,
) -> None:
    """Print models in a pretty table with optional pagination.

    Args:
        models: List of models to display.
        title: Table title.
        page_size: Items per page (0 = no pagination, show all).
    """
    if page_size <= 0 or len(models) <= page_size:
        # No pagination needed
        _print_models_page(models, title, start_index=1)
        console.print(f"\nPrices are per 1M tokens | Total: {len(models)} models", style="dim")
        return

    # Paginated output
    total_pages = (len(models) + page_size - 1) // page_size
    page = 0

    while page < total_pages:
        start = page * page_size
        end = min(start + page_size, len(models))
        page_models = models[start:end]

        page_title = f"{title} (page {page + 1}/{total_pages})"
        _print_models_page(page_models, page_title, start_index=start + 1)

        console.print(
            f"\nShowing {start + 1}-{end} of {len(models)} | Prices per 1M tokens",
            style="dim",
        )

        # Prompt for next page
        if page < total_pages - 1:
            console.print(
                "[dim]Press [bold]Enter[/bold] for next page, [bold]q[/bold] to quit[/dim]"
            )
            try:
                user_input = input()
                if user_input.strip().lower() == "q":
                    break
            except (EOFError, KeyboardInterrupt):
                break
        page += 1


def _print_models_page(
    models: list[ModelInfo], title: str, start_index: int = 1
) -> None:
    """Print a single page of models."""
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Model ID", style="white")
    table.add_column("Context", style="cyan", justify="right")
    table.add_column("Max Output", style="cyan", justify="right")
    table.add_column("Input/Output $", style="green", justify="right")

    for i, model in enumerate(models, start_index):
        context = format_tokens(model.context_window)
        max_output = format_tokens(model.max_output)
        price = f"${model.input_price} / ${model.output_price}"
        table.add_row(str(i), model.id, context, max_output, price)

    console.print(table)


def print_model_details(model: ModelInfo) -> None:
    """Print detailed information about a single model."""
    table = Table(
        title="Model Details",
        show_header=False,
        box=None,
    )

    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="white")

    table.add_row("Model ID", model.id)
    table.add_row("Provider", model.provider)
    table.add_row("Context Window", f"{model.context_window:,} tokens")
    table.add_row("Max Output", f"{model.max_output:,} tokens")
    table.add_row("Input Price", f"${model.input_price:.2f} / 1M tokens")
    table.add_row("Output Price", f"${model.output_price:.2f} / 1M tokens")

    if model.capabilities:
        table.add_row("Capabilities", ", ".join(model.capabilities))

    if model.training_cutoff:
        table.add_row("Training Cutoff", model.training_cutoff)

    console.print(table)


def print_proxy_models_table(models: list[dict], context_name: str = "") -> None:
    """Print models from LiteLLM Proxy."""
    title = f"Models on {context_name}" if context_name else "Models"
    table = Table(
        title=title,
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
            model.get("model_name", ""),
            model.get("litellm_params", {}).get("model", "").split("/")[0],
            model.get("litellm_params", {}).get("model", ""),
        )

    console.print(table)
    console.print(f"\nTotal: {len(models)} models", style="dim")


def print_keys_table(keys: list[VirtualKey], context_name: str = "") -> None:
    """Print virtual keys in a pretty table."""
    title = f"Virtual Keys on {context_name}" if context_name else "Virtual Keys"
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Key Alias", style="white")
    table.add_column("Key (masked)", style="dim")
    table.add_column("Team", style="green")
    table.add_column("Budget", style="cyan", justify="right")
    table.add_column("Expires", style="yellow")

    for i, key in enumerate(keys, 1):
        alias = key.key_alias or key.key_name or "-"
        team = key.team_id or "-"

        if key.max_budget:
            duration = key.budget_duration or "month"
            budget = f"${key.max_budget:.0f}/{duration}"
        else:
            budget = "Unlimited"

        if key.expires:
            expires = key.expires.strftime("%Y-%m-%d")
        else:
            expires = "Never"

        table.add_row(str(i), alias, key.masked_key, team, budget, expires)

    console.print(table)
    console.print(f"\nTotal: {len(keys)} keys", style="dim")


def print_teams_table(teams: list[Team], context_name: str = "") -> None:
    """Print teams in a pretty table."""
    title = f"Teams on {context_name}" if context_name else "Teams"
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Team ID", style="white")
    table.add_column("Name", style="green")
    table.add_column("Budget", style="cyan", justify="right")
    table.add_column("Models", style="blue")

    for i, team in enumerate(teams, 1):
        name = team.team_alias or "-"

        if team.max_budget:
            duration = team.budget_duration or "month"
            budget = f"${team.max_budget:.0f}/{duration}"
        else:
            budget = "Unlimited"

        if team.models:
            models = ", ".join(team.models[:3])
            if len(team.models) > 3:
                models += f" (+{len(team.models) - 3})"
        else:
            models = "All models"

        table.add_row(str(i), team.team_id, name, budget, models)

    console.print(table)
    console.print(f"\nTotal: {len(teams)} teams", style="dim")


def print_team_details(team: "Team") -> None:
    """Print detailed information about a single team."""
    table = Table(
        title="Team Details",
        show_header=False,
        box=None,
    )

    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="white")

    table.add_row("Team ID", team.team_id)
    table.add_row("Name", team.team_alias or "-")

    if team.models:
        table.add_row("Models", f"{len(team.models)} model(s)")
    else:
        table.add_row("Models", "All models")

    if team.max_budget:
        duration = team.budget_duration or "month"
        table.add_row("Budget", f"${team.max_budget:.0f}/{duration}")
    else:
        table.add_row("Budget", "Unlimited")

    table.add_row("Blocked", "Yes" if team.blocked else "No")
    table.add_row("Members", str(len(team.members)))

    console.print(table)

    # Show models in a separate table if any
    if team.models:
        models_table = Table(
            title="Team Models",
            show_header=True,
            header_style="bold cyan",
        )
        models_table.add_column("#", style="dim", width=4)
        models_table.add_column("Model Name", style="white")
        for i, model in enumerate(sorted(team.models), 1):
            models_table.add_row(str(i), model)
        console.print(models_table)


def print_config_table(orgs: dict) -> None:
    """Print configuration table with all orgs and environments."""
    table = Table(
        title="Organizations",
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Org ID", style="white")
    table.add_column("Name", style="green")
    table.add_column("Environment", style="cyan")
    table.add_column("URL", style="dim")

    for org_id, org in orgs.items():
        first = True
        for env_name, env in org.environments.items():
            table.add_row(
                org_id if first else "",
                org.name if first else "",
                env_name,
                env.url,
            )
            first = False
        # Add separator between orgs
        if len(orgs) > 1:
            table.add_section()

    console.print(table)


def print_history_table(entries: list[dict]) -> None:
    """Print command history as a simple list.

    Args:
        entries: List of dicts with 'command' and 'timestamp' keys.
    """
    for i, entry in enumerate(entries, 1):
        ts = entry["timestamp"].replace("T", " ")
        console.print(f"[dim]{i:>3}[/dim]  {entry['command']}  [dim]{ts}[/dim]")


def format_tokens(tokens: int) -> str:
    """Format token count to human readable string."""
    if tokens >= 1_000_000:
        return f"{tokens // 1_000_000}M"
    if tokens >= 1_000:
        return f"{tokens // 1_000}K"
    return str(tokens)


# ==================== Usage & Spend Tables ====================


def _format_spend(amount: float) -> str:
    """Format spend amount as currency string."""
    if amount >= 1000:
        return f"${amount:,.0f}"
    return f"${amount:.2f}"


def _format_token_count(tokens: int) -> str:
    """Format token count with K/M suffixes."""
    if tokens >= 1_000_000:
        return f"{tokens / 1_000_000:.1f}M"
    if tokens >= 1_000:
        return f"{tokens / 1_000:.1f}K"
    return str(tokens)


def print_tag_summary_table(
    data: dict,
    context_name: str = "",
    start_date: str = "",
    end_date: str = "",
    top_n: int = 0,
) -> None:
    """Print tag-level spend summary from /tag/summary."""
    from llm_cli.models.usage import TagSummaryResponse

    response = TagSummaryResponse.model_validate(data)
    entries = sorted(response.results, key=lambda e: e.total_spend, reverse=True)

    if top_n > 0:
        entries = entries[:top_n]

    title = "Usage Summary"
    if context_name:
        title += f" on {context_name}"
    if start_date and end_date:
        title += f" ({start_date} to {end_date})"

    # Compute grand totals
    grand_spend = sum(e.total_spend for e in entries)
    grand_requests = sum(e.total_requests for e in entries)
    grand_tokens = sum(e.total_tokens for e in entries)

    console.print(f"\n[bold]{title}[/bold]")
    console.print(
        f"  Total Spend: [green]{_format_spend(grand_spend)}[/green]  |  "
        f"Requests: [cyan]{grand_requests:,}[/cyan]  |  "
        f"Tokens: [cyan]{_format_token_count(grand_tokens)}[/cyan]\n"
    )

    table = Table(
        title="Spend by Tag",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Tag", style="white")
    table.add_column("Spend", style="green", justify="right")
    table.add_column("Requests", style="cyan", justify="right")
    table.add_column("Success", style="green", justify="right")
    table.add_column("Failed", style="red", justify="right")
    table.add_column("Tokens", style="cyan", justify="right")
    table.add_column("Users", style="yellow", justify="right")

    for i, entry in enumerate(entries, 1):
        table.add_row(
            str(i),
            entry.tag,
            _format_spend(entry.total_spend),
            str(entry.total_requests),
            str(entry.successful_requests),
            str(entry.failed_requests),
            _format_token_count(entry.total_tokens),
            str(entry.unique_users),
        )

    console.print(table)
    console.print(f"\nTotal: {len(entries)} tags", style="dim")


def print_spend_by_key_table(
    keys: list[VirtualKey],
    context_name: str = "",
    top_n: int = 0,
) -> None:
    """Print spend by API key using data from /key/list."""
    keys_sorted = sorted(keys, key=lambda k: k.spend, reverse=True)

    if top_n > 0:
        keys_sorted = keys_sorted[:top_n]

    title = "Spend by API Key"
    if context_name:
        title += f" on {context_name}"

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Key", style="dim")
    table.add_column("Alias", style="white")
    table.add_column("Team", style="yellow")
    table.add_column("Spend", style="green", justify="right")
    table.add_column("Budget", style="cyan", justify="right")

    total_spend = 0.0
    for i, key in enumerate(keys_sorted, 1):
        alias = key.key_alias or key.key_name or "-"
        team = key.team_id or "-"
        if key.max_budget:
            duration = key.budget_duration or "month"
            budget = f"${key.max_budget:.0f}/{duration}"
        else:
            budget = "Unlimited"

        table.add_row(
            str(i),
            key.masked_key,
            alias,
            team,
            _format_spend(key.spend),
            budget,
        )
        total_spend += key.spend

    console.print(table)
    console.print(
        f"\nTotal: {len(keys_sorted)} API keys | Combined spend: {_format_spend(total_spend)}",
        style="dim",
    )
    console.print("Spend is cumulative within each key's budget period.", style="dim italic")


def print_spend_by_team_table(
    teams: list[Team],
    context_name: str = "",
    top_n: int = 0,
) -> None:
    """Print spend by team using data from /team/list."""
    teams_sorted = sorted(teams, key=lambda t: t.spend, reverse=True)

    if top_n > 0:
        teams_sorted = teams_sorted[:top_n]

    title = "Spend by Team"
    if context_name:
        title += f" on {context_name}"

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Team", style="white")
    table.add_column("Spend", style="green", justify="right")
    table.add_column("Budget", style="cyan", justify="right")
    table.add_column("Models", style="blue", justify="right")
    table.add_column("Members", style="yellow", justify="right")

    total_spend = 0.0
    for i, team in enumerate(teams_sorted, 1):
        name = team.team_alias or team.team_id
        if team.max_budget:
            duration = team.budget_duration or "month"
            budget = f"${team.max_budget:.0f}/{duration}"
        else:
            budget = "Unlimited"

        model_count = str(len(team.models)) if team.models else "All"
        member_count = str(len(team.members))

        table.add_row(
            str(i),
            name,
            _format_spend(team.spend),
            budget,
            model_count,
            member_count,
        )
        total_spend += team.spend

    console.print(table)
    console.print(
        f"\nTotal: {len(teams_sorted)} teams | Combined spend: {_format_spend(total_spend)}",
        style="dim",
    )
    console.print("Spend is cumulative within each team's budget period.", style="dim italic")


def print_spend_by_model_table(
    data: list[dict],
    context_name: str = "",
    start_date: str = "",
    end_date: str = "",
    top_n: int = 0,
) -> None:
    """Print spend aggregated by model from /spend/logs data."""
    from collections import defaultdict

    # Aggregate model spend from spend logs
    # Each log entry has: models dict {model_name: spend_amount}
    model_agg: dict[str, float] = defaultdict(float)

    for entry in data:
        models = entry.get("models", {})
        if isinstance(models, dict):
            for model_name, spend in models.items():
                model_agg[model_name] += spend

    sorted_models = sorted(model_agg.items(), key=lambda x: x[1], reverse=True)
    if top_n > 0:
        sorted_models = sorted_models[:top_n]

    title = "Spend by Model"
    if context_name:
        title += f" on {context_name}"
    if start_date and end_date:
        title += f" ({start_date} to {end_date})"

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Model", style="white")
    table.add_column("Spend", style="green", justify="right")

    total_spend = 0.0
    for i, (model_name, spend) in enumerate(sorted_models, 1):
        table.add_row(
            str(i),
            model_name,
            _format_spend(spend),
        )
        total_spend += spend

    console.print(table)
    console.print(
        f"\nTotal: {len(sorted_models)} models | Combined spend: {_format_spend(total_spend)}",
        style="dim",
    )


def print_daily_activity_table(
    data: list[dict],
    scope: str = "user",
    context_name: str = "",
    start_date: str = "",
    end_date: str = "",
) -> None:
    """Print daily activity table."""
    from llm_cli.models.usage import ActivityEntry

    entries = [ActivityEntry.model_validate(d) for d in data]

    title = "Daily Activity"
    if context_name:
        title += f" on {context_name}"
    if start_date and end_date:
        title += f" ({start_date} to {end_date})"

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Date", style="white")
    table.add_column("Model", style="blue")
    table.add_column("Spend", style="green", justify="right")
    table.add_column("Requests", style="cyan", justify="right")
    table.add_column("Prompt Tok.", style="cyan", justify="right")
    table.add_column("Compl. Tok.", style="cyan", justify="right")

    if scope == "team":
        table.add_column("Team", style="yellow")

    total_spend = 0.0
    for entry in entries:
        row = [
            entry.date,
            entry.model_group or "-",
            _format_spend(entry.spend),
            str(entry.api_requests),
            _format_token_count(entry.prompt_tokens),
            _format_token_count(entry.completion_tokens),
        ]
        if scope == "team":
            row.append(entry.team_id or "-")
        table.add_row(*row)
        total_spend += entry.spend

    console.print(table)
    console.print(
        f"\nTotal: {len(entries)} entries | Combined spend: {_format_spend(total_spend)}",
        style="dim",
    )


def print_spend_logs_table(
    data: list[dict],
    context_name: str = "",
    top_n: int = 0,
) -> None:
    """Print daily spend logs.

    The /spend/logs endpoint returns daily aggregations with nested model/user dicts.
    """
    from llm_cli.models.usage import SpendLogEntry

    entries = [SpendLogEntry.model_validate(d) for d in data]
    # Sort by date descending (most recent first)
    entries.sort(key=lambda e: e.startTime or "", reverse=True)

    if top_n > 0:
        entries = entries[:top_n]

    title = "Daily Spend Logs"
    if context_name:
        title += f" on {context_name}"

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Date", style="white")
    table.add_column("Spend", style="green", justify="right")
    table.add_column("Models", style="blue")
    table.add_column("Users", style="cyan", justify="right")

    total_spend = 0.0
    for entry in entries:
        date_str = entry.startTime or "-"

        # Format model breakdown: "gpt-4 ($3.00), claude-3 ($2.00)"
        model_parts = []
        for model_name, model_spend in sorted(
            entry.models.items(), key=lambda x: x[1], reverse=True
        ):
            if model_spend > 0:
                model_parts.append(f"{model_name} ({_format_spend(model_spend)})")
        models_str = ", ".join(model_parts) if model_parts else "-"

        # Count active users (those with spend > 0)
        active_users = sum(1 for s in entry.users.values() if s > 0)

        table.add_row(
            date_str,
            _format_spend(entry.spend),
            models_str,
            str(active_users),
        )
        total_spend += entry.spend

    console.print(table)
    console.print(
        f"\nTotal: {len(entries)} days | Combined spend: {_format_spend(total_spend)}",
        style="dim",
    )
