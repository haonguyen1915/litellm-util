"""Usage commands - View spend and usage statistics."""

from datetime import date, datetime, timedelta
from typing import Optional

import typer

from llm_cli.core.client import APIError, AuthenticationError, ConnectionError, LiteLLMClient
from llm_cli.core.context import ConfigurationError
from llm_cli.ui import error
from llm_cli.ui.console import console
from llm_cli.ui.tables import (
    print_daily_activity_table,
    print_spend_by_key_table,
    print_spend_by_model_table,
    print_spend_by_team_table,
    print_spend_logs_table,
    print_tag_summary_table,
)

app = typer.Typer(no_args_is_help=True)

LAST_CHOICES = {"1h": "1h", "1d": "1d", "1w": "1w", "1m": "1m"}


def _get_client(org: str | None, env: str | None) -> LiteLLMClient:
    """Get API client with error handling."""
    try:
        return LiteLLMClient(org_override=org, env_override=env)
    except ConfigurationError as e:
        error(str(e))
        raise typer.Exit(2)


def _default_start() -> str:
    """Return default start date (30 days ago)."""
    return (date.today() - timedelta(days=30)).isoformat()


def _default_end() -> str:
    """Return default end date (today)."""
    return date.today().isoformat()


def _resolve_dates(
    start: str | None, end: str | None, last: str | None
) -> tuple[str, str]:
    """Resolve start/end dates from explicit values or --last shortcut.

    --last takes precedence over --start/--end when provided.
    Accepted values: 1h, 1d, 1w, 1m.
    """
    if last:
        now = datetime.now()
        end_date = now.strftime("%Y-%m-%d")
        if last == "1h":
            start_dt = now - timedelta(hours=1)
        elif last == "1d":
            start_dt = now - timedelta(days=1)
        elif last == "1w":
            start_dt = now - timedelta(weeks=1)
        elif last == "1m":
            start_dt = now - timedelta(days=30)
        else:
            error(f"Invalid --last value: {last}. Use 1h, 1d, 1w, or 1m.")
            raise typer.Exit(2)
        start_date = start_dt.strftime("%Y-%m-%d")
        return start_date, end_date

    return start or _default_start(), end or _default_end()


@app.command("summary")
def summary(
    start: Optional[str] = typer.Option(None, "--start", "-s", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    last: Optional[str] = typer.Option(None, "--last", "-l", help="Time range: 1h, 1d, 1w, 1m"),
    top: int = typer.Option(0, "--top", "-t", help="Show top N results"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", help="Override environment"),
) -> None:
    """Overview: spend summary grouped by tag.

    Examples:
        llm usage summary
        llm usage summary --last 1w
        llm usage summary --start 2025-03-01 --end 2025-03-17
        llm usage summary --top 5
    """
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"
    start_date, end_date = _resolve_dates(start, end, last)

    try:
        data = client.get_tag_summary(start_date=start_date, end_date=end_date)
        print_tag_summary_table(
            data,
            context_name=context_name,
            start_date=start_date,
            end_date=end_date,
            top_n=top,
        )
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        console.print(f"  URL: {client.base_url}", style="dim")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)


@app.command("by-key")
def by_key(
    top: int = typer.Option(0, "--top", "-t", help="Show top N results"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", help="Override environment"),
) -> None:
    """Spend grouped by API key.

    Shows total spend per key from the proxy. Spend is cumulative (not date-filtered).

    Examples:
        llm usage by-key
        llm usage by-key --top 5
    """
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"

    try:
        keys = client.list_keys()
        print_spend_by_key_table(keys, context_name=context_name, top_n=top)
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        console.print(f"  URL: {client.base_url}", style="dim")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)


@app.command("by-team")
def by_team(
    top: int = typer.Option(0, "--top", "-t", help="Show top N results"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", help="Override environment"),
) -> None:
    """Spend grouped by team.

    Shows total spend per team from the proxy. Spend is cumulative (not date-filtered).

    Examples:
        llm usage by-team
        llm usage by-team --top 5
    """
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"

    try:
        teams = client.list_teams()
        print_spend_by_team_table(teams, context_name=context_name, top_n=top)
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        console.print(f"  URL: {client.base_url}", style="dim")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)


@app.command("by-model")
def by_model(
    start: Optional[str] = typer.Option(None, "--start", "-s", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    last: Optional[str] = typer.Option(None, "--last", "-l", help="Time range: 1h, 1d, 1w, 1m"),
    top: int = typer.Option(0, "--top", "-t", help="Show top N results"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", help="Override environment"),
) -> None:
    """Spend grouped by model (aggregated from spend logs).

    Examples:
        llm usage by-model
        llm usage by-model --last 1m
        llm usage by-model --start 2025-01-01 --end 2025-03-17
        llm usage by-model --top 10
    """
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"
    start_date, end_date = _resolve_dates(start, end, last)

    try:
        data = client.get_spend_logs(
            start_date=start_date,
            end_date=end_date,
        )
        if not isinstance(data, list):
            data = data.get("data", []) if isinstance(data, dict) else []
        print_spend_by_model_table(
            data,
            context_name=context_name,
            start_date=start_date,
            end_date=end_date,
            top_n=top,
        )
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        console.print(f"  URL: {client.base_url}", style="dim")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)


@app.command("activity")
def activity(
    scope: str = typer.Option("user", "--scope", help="Scope: 'user' or 'team'"),
    start: Optional[str] = typer.Option(None, "--start", "-s", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    last: Optional[str] = typer.Option(None, "--last", "-l", help="Time range: 1h, 1d, 1w, 1m"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", help="Override environment"),
) -> None:
    """Daily activity breakdown.

    Examples:
        llm usage activity
        llm usage activity --last 1w
        llm usage activity --scope team
        llm usage activity --scope team --start 2025-03-01
    """
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"
    start_date, end_date = _resolve_dates(start, end, last)

    try:
        if scope == "team":
            data = client.get_team_daily_activity(
                start_date=start_date,
                end_date=end_date,
            )
        else:
            data = client.get_user_daily_activity(
                start_date=start_date,
                end_date=end_date,
            )

        if not isinstance(data, list):
            data = data.get("data", data.get("results", [])) if isinstance(data, dict) else []
        print_daily_activity_table(
            data,
            scope=scope,
            context_name=context_name,
            start_date=start_date,
            end_date=end_date,
        )
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        console.print(f"  URL: {client.base_url}", style="dim")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)


@app.command("logs")
def logs(
    start: Optional[str] = typer.Option(None, "--start", "-s", help="Start date (YYYY-MM-DD)"),
    end: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    last: Optional[str] = typer.Option(None, "--last", "-l", help="Time range: 1h, 1d, 1w, 1m"),
    request_id: Optional[str] = typer.Option(None, "--request-id", "-r", help="Filter by request ID"),
    top: int = typer.Option(0, "--top", "-t", help="Show top N results"),
    org: Optional[str] = typer.Option(None, "--org", "-o", help="Override organization"),
    env: Optional[str] = typer.Option(None, "--env", help="Override environment"),
) -> None:
    """Daily spend logs with model breakdowns.

    Examples:
        llm usage logs
        llm usage logs --last 1h
        llm usage logs --top 10
        llm usage logs --start 2025-03-01 --end 2025-03-17
        llm usage logs --request-id abc123
    """
    client = _get_client(org, env)
    context_name = f"{client.context.organization_id}/{client.context.environment}"
    start_date, end_date = _resolve_dates(start, end, last)

    try:
        data = client.get_spend_logs(
            start_date=start_date if not request_id else start,
            end_date=end_date if not request_id else end,
            request_id=request_id,
        )
        if not isinstance(data, list):
            data = data.get("data", []) if isinstance(data, dict) else []
        print_spend_logs_table(data, context_name=context_name, top_n=top)
    except ConnectionError:
        error("Cannot connect to LiteLLM Proxy")
        console.print(f"  URL: {client.base_url}", style="dim")
        raise typer.Exit(3)
    except AuthenticationError:
        error("Authentication failed")
        raise typer.Exit(4)
    except APIError as e:
        error(f"API Error: {e.message}")
        raise typer.Exit(1)
