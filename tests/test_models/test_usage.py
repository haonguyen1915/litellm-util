"""Tests for usage Pydantic models."""

import pytest

from llm_cli.models.usage import (
    ActivityEntry,
    DailySpendEntry,
    SpendLogEntry,
    TagSummaryEntry,
    TagSummaryResponse,
)


class TestDailySpendEntry:
    def test_empty(self):
        entry = DailySpendEntry()
        assert entry.date == ""
        assert entry.spend == 0.0
        assert entry.api_requests == 0

    def test_full(self):
        entry = DailySpendEntry(date="2025-03-01", spend=12.34, api_requests=100)
        assert entry.date == "2025-03-01"
        assert entry.spend == 12.34
        assert entry.api_requests == 100

    def test_extra_fields_ignored(self):
        entry = DailySpendEntry(date="2025-03-01", spend=1.0, unknown_field="ignored")
        assert entry.date == "2025-03-01"
        assert not hasattr(entry, "unknown_field")


class TestTagSummaryEntry:
    def test_empty(self):
        entry = TagSummaryEntry()
        assert entry.tag == ""
        assert entry.total_spend == 0.0
        assert entry.total_requests == 0
        assert entry.unique_users == 0

    def test_full(self):
        entry = TagSummaryEntry(
            tag="User-Agent: OpenAI",
            unique_users=1,
            total_requests=18528,
            successful_requests=18528,
            failed_requests=0,
            total_tokens=100074824,
            total_spend=166.22,
        )
        assert entry.tag == "User-Agent: OpenAI"
        assert entry.total_spend == 166.22
        assert entry.total_requests == 18528
        assert entry.successful_requests == 18528
        assert entry.failed_requests == 0

    def test_extra_fields_ignored(self):
        entry = TagSummaryEntry(tag="test", unknown="ignored")
        assert entry.tag == "test"
        assert not hasattr(entry, "unknown")


class TestTagSummaryResponse:
    def test_empty(self):
        resp = TagSummaryResponse()
        assert resp.results == []

    def test_full(self):
        resp = TagSummaryResponse(
            results=[
                {
                    "tag": "User-Agent: OpenAI",
                    "unique_users": 1,
                    "total_requests": 100,
                    "successful_requests": 100,
                    "failed_requests": 0,
                    "total_tokens": 50000,
                    "total_spend": 10.0,
                },
                {
                    "tag": "litellm-health-check",
                    "unique_users": 0,
                    "total_requests": 50,
                    "successful_requests": 50,
                    "failed_requests": 0,
                    "total_tokens": 1000,
                    "total_spend": 0.01,
                },
            ]
        )
        assert len(resp.results) == 2
        assert isinstance(resp.results[0], TagSummaryEntry)
        assert resp.results[0].tag == "User-Agent: OpenAI"
        assert resp.results[1].total_spend == 0.01

    def test_from_dict(self):
        data = {
            "results": [
                {
                    "tag": "test-tag",
                    "unique_users": 2,
                    "total_requests": 200,
                    "successful_requests": 195,
                    "failed_requests": 5,
                    "total_tokens": 80000,
                    "total_spend": 25.50,
                },
            ],
            "extra_field": "should be ignored",
        }
        resp = TagSummaryResponse.model_validate(data)
        assert len(resp.results) == 1
        assert resp.results[0].total_spend == 25.50

    def test_extra_fields_ignored(self):
        resp = TagSummaryResponse(results=[], unknown="test")
        assert resp.results == []



class TestActivityEntry:
    def test_empty(self):
        entry = ActivityEntry()
        assert entry.date == ""
        assert entry.model_group is None

    def test_full(self):
        entry = ActivityEntry(
            date="2025-03-01",
            spend=5.0,
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            api_requests=10,
            model_group="gpt-4",
            team_id="team-1",
        )
        assert entry.model_group == "gpt-4"
        assert entry.team_id == "team-1"


class TestSpendLogEntry:
    def test_empty(self):
        entry = SpendLogEntry()
        assert entry.spend == 0.0
        assert entry.models == {}
        assert entry.users == {}

    def test_full(self):
        entry = SpendLogEntry(
            startTime="2025-03-16",
            spend=5.0,
            users={"default_user_id": 5.0},
            models={"gpt-4": 3.0, "claude-3": 2.0},
        )
        assert entry.startTime == "2025-03-16"
        assert entry.spend == 5.0
        assert entry.models["gpt-4"] == 3.0
        assert len(entry.users) == 1

    def test_extra_fields_ignored(self):
        entry = SpendLogEntry(
            startTime="2025-03-16",
            spend=1.0,
            some_hash_key=0.5,
        )
        assert entry.spend == 1.0
