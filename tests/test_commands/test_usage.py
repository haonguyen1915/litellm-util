"""Tests for usage commands."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from llm_cli.main import app
from llm_cli.models.key import VirtualKey
from llm_cli.models.team import Team

runner = CliRunner()


def _mock_context():
    ctx = MagicMock()
    ctx.organization_id = "test-org"
    ctx.environment = "dev"
    return ctx


def _mock_client(**overrides):
    client = MagicMock()
    client.context = _mock_context()
    client.base_url = "http://localhost:4000"
    for k, v in overrides.items():
        setattr(client, k, v)
    return client


SAMPLE_TAG_SUMMARY = {
    "results": [
        {
            "tag": "User-Agent: OpenAI",
            "unique_users": 1,
            "total_requests": 18528,
            "successful_requests": 18528,
            "failed_requests": 0,
            "total_tokens": 100074824,
            "total_spend": 166.22,
        },
        {
            "tag": "litellm-health-check",
            "unique_users": 0,
            "total_requests": 1512,
            "successful_requests": 1512,
            "failed_requests": 0,
            "total_tokens": 129796,
            "total_spend": 0.30,
        },
    ],
}

SAMPLE_KEYS = [
    VirtualKey(
        token="sk-key-111111111111111111111111111111111111",
        key_alias="primary-key",
        team_id="team-eng",
        spend=80.0,
        max_budget=100.0,
        budget_duration="30d",
    ),
    VirtualKey(
        token="sk-key-222222222222222222222222222222222222",
        key_alias="secondary-key",
        team_id="team-mkt",
        spend=20.0,
    ),
]

SAMPLE_TEAMS = [
    Team(
        team_id="team-eng",
        team_alias="Engineering",
        spend=90.0,
        max_budget=200.0,
        budget_duration="30d",
        models=["gpt-4", "claude-3"],
    ),
    Team(
        team_id="team-mkt",
        team_alias="Marketing",
        spend=10.0,
        models=["gpt-4"],
    ),
]

SAMPLE_SPEND_LOGS = [
    {
        "users": {"default_user_id": 5.0},
        "models": {"gpt-4": 3.0, "claude-3": 2.0},
        "spend": 5.0,
        "startTime": "2025-03-16",
    },
    {
        "users": {"default_user_id": 1.0},
        "models": {"gpt-4": 0.5, "gpt-3.5-turbo": 0.5},
        "spend": 1.0,
        "startTime": "2025-03-15",
    },
]

SAMPLE_DAILY_LOGS = [
    {
        "users": {"default_user_id": 5.0},
        "models": {"gpt-4": 3.0, "claude-3": 2.0},
        "spend": 5.0,
        "startTime": "2025-03-16",
    },
    {
        "users": {"default_user_id": 1.0},
        "models": {"gpt-4": 0.5, "gpt-3.5-turbo": 0.5},
        "spend": 1.0,
        "startTime": "2025-03-15",
    },
]


class TestSummary:
    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_summary_success(self, mock_cls):
        client = _mock_client()
        client.get_tag_summary.return_value = SAMPLE_TAG_SUMMARY
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "summary"])
        assert result.exit_code == 0
        assert "Usage Summary" in result.output
        assert "OpenAI" in result.output

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_summary_connection_error(self, mock_cls):
        from llm_cli.core.client import ConnectionError

        client = _mock_client()
        client.get_tag_summary.side_effect = ConnectionError("Cannot connect")
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "summary"])
        assert result.exit_code == 3

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_summary_with_dates(self, mock_cls):
        client = _mock_client()
        client.get_tag_summary.return_value = SAMPLE_TAG_SUMMARY
        mock_cls.return_value = client

        result = runner.invoke(
            app, ["usage", "summary", "--start", "2026-03-10", "--end", "2026-03-17"]
        )
        assert result.exit_code == 0
        client.get_tag_summary.assert_called_once_with(
            start_date="2026-03-10",
            end_date="2026-03-17",
        )

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_summary_top_n(self, mock_cls):
        client = _mock_client()
        client.get_tag_summary.return_value = SAMPLE_TAG_SUMMARY
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "summary", "--top", "1"])
        assert result.exit_code == 0
        assert "1 tags" in result.output.lower()

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_summary_last_1w(self, mock_cls):
        client = _mock_client()
        client.get_tag_summary.return_value = SAMPLE_TAG_SUMMARY
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "summary", "--last", "1w"])
        assert result.exit_code == 0
        call_kwargs = client.get_tag_summary.call_args[1]
        expected_start = (datetime.now() - timedelta(weeks=1)).strftime("%Y-%m-%d")
        assert call_kwargs["start_date"] == expected_start
        assert call_kwargs["end_date"] == datetime.now().strftime("%Y-%m-%d")

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_summary_last_1h(self, mock_cls):
        client = _mock_client()
        client.get_tag_summary.return_value = SAMPLE_TAG_SUMMARY
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "summary", "--last", "1h"])
        assert result.exit_code == 0
        call_kwargs = client.get_tag_summary.call_args[1]
        expected_start = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d")
        assert call_kwargs["start_date"] == expected_start

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_summary_last_invalid(self, mock_cls):
        client = _mock_client()
        client.get_tag_summary.return_value = SAMPLE_TAG_SUMMARY
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "summary", "--last", "2y"])
        assert result.exit_code == 2


class TestByKey:
    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_key_success(self, mock_cls):
        client = _mock_client()
        client.list_keys.return_value = SAMPLE_KEYS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-key"])
        assert result.exit_code == 0
        assert "Spend by API Key" in result.output
        assert "primary-key" in result.output

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_key_empty(self, mock_cls):
        client = _mock_client()
        client.list_keys.return_value = []
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-key"])
        assert result.exit_code == 0
        assert "0 api keys" in result.output.lower()

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_key_top_n(self, mock_cls):
        client = _mock_client()
        client.list_keys.return_value = SAMPLE_KEYS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-key", "--top", "1"])
        assert result.exit_code == 0
        assert "primary-key" in result.output

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_key_calls_list_keys(self, mock_cls):
        """by-key uses /key/list endpoint."""
        client = _mock_client()
        client.list_keys.return_value = SAMPLE_KEYS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-key"])
        assert result.exit_code == 0
        client.list_keys.assert_called_once()


class TestByTeam:
    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_team_success(self, mock_cls):
        client = _mock_client()
        client.list_teams.return_value = SAMPLE_TEAMS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-team"])
        assert result.exit_code == 0
        assert "Spend by Team" in result.output
        assert "Engineering" in result.output
        assert "Marketing" in result.output

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_team_calls_list_teams(self, mock_cls):
        """by-team uses /team/list endpoint."""
        client = _mock_client()
        client.list_teams.return_value = SAMPLE_TEAMS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-team"])
        assert result.exit_code == 0
        client.list_teams.assert_called_once()

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_team_top_n(self, mock_cls):
        client = _mock_client()
        client.list_teams.return_value = SAMPLE_TEAMS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-team", "--top", "1"])
        assert result.exit_code == 0
        assert "Engineering" in result.output


class TestByModel:
    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_model_aggregation(self, mock_cls):
        """Verify model spend is aggregated from spend logs."""
        client = _mock_client()
        client.get_spend_logs.return_value = SAMPLE_SPEND_LOGS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-model"])
        assert result.exit_code == 0
        assert "Spend by Model" in result.output
        assert "gpt-4" in result.output
        assert "claude-3" in result.output

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_model_empty(self, mock_cls):
        client = _mock_client()
        client.get_spend_logs.return_value = []
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-model"])
        assert result.exit_code == 0
        assert "0 models" in result.output.lower()

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_by_model_last_1w(self, mock_cls):
        client = _mock_client()
        client.get_spend_logs.return_value = SAMPLE_SPEND_LOGS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "by-model", "--last", "1w"])
        assert result.exit_code == 0
        call_kwargs = client.get_spend_logs.call_args[1]
        expected_start = (datetime.now() - timedelta(weeks=1)).strftime("%Y-%m-%d")
        assert call_kwargs["start_date"] == expected_start


class TestActivity:
    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_activity_user_scope(self, mock_cls):
        client = _mock_client()
        client.get_user_daily_activity.return_value = [
            {
                "date": "2025-03-15",
                "spend": 5.0,
                "prompt_tokens": 1000,
                "completion_tokens": 500,
                "total_tokens": 1500,
                "api_requests": 10,
                "model_group": "gpt-4",
            }
        ]
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "activity"])
        assert result.exit_code == 0
        assert "Daily Activity" in result.output

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_activity_team_scope(self, mock_cls):
        client = _mock_client()
        client.get_team_daily_activity.return_value = [
            {
                "date": "2025-03-15",
                "spend": 10.0,
                "prompt_tokens": 2000,
                "completion_tokens": 1000,
                "total_tokens": 3000,
                "api_requests": 20,
                "model_group": "gpt-4",
                "team_id": "team-eng",
            }
        ]
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "activity", "--scope", "team"])
        assert result.exit_code == 0
        assert "Daily Activity" in result.output
        assert "team-eng" in result.output


class TestLogs:
    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_logs_success(self, mock_cls):
        client = _mock_client()
        client.get_spend_logs.return_value = SAMPLE_DAILY_LOGS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "logs"])
        assert result.exit_code == 0
        assert "Daily Spend Logs" in result.output
        assert "gpt-4" in result.output

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_logs_with_top(self, mock_cls):
        client = _mock_client()
        client.get_spend_logs.return_value = SAMPLE_DAILY_LOGS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "logs", "--top", "1"])
        assert result.exit_code == 0
        assert "1 days" in result.output.lower()

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_logs_with_request_id(self, mock_cls):
        client = _mock_client()
        client.get_spend_logs.return_value = [SAMPLE_DAILY_LOGS[0]]
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "logs", "--request-id", "req-001"])
        assert result.exit_code == 0
        client.get_spend_logs.assert_called_once_with(
            start_date=None,
            end_date=None,
            request_id="req-001",
        )

    @patch("llm_cli.commands.usage.LiteLLMClient")
    def test_logs_last_1h(self, mock_cls):
        client = _mock_client()
        client.get_spend_logs.return_value = SAMPLE_DAILY_LOGS
        mock_cls.return_value = client

        result = runner.invoke(app, ["usage", "logs", "--last", "1h"])
        assert result.exit_code == 0
        call_kwargs = client.get_spend_logs.call_args[1]
        expected_start = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d")
        assert call_kwargs["start_date"] == expected_start
