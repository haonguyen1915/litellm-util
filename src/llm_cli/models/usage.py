"""Usage and spend statistics schemas."""

from pydantic import BaseModel, ConfigDict, Field


class DailySpendEntry(BaseModel):
    """Single day of spend data."""

    model_config = ConfigDict(extra="ignore")

    date: str = ""
    spend: float = 0.0
    api_requests: int = 0


class TagSummaryEntry(BaseModel):
    """Single tag entry from /tag/summary."""

    model_config = ConfigDict(extra="ignore")

    tag: str = ""
    unique_users: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_spend: float = 0.0


class TagSummaryResponse(BaseModel):
    """Response from /tag/summary."""

    model_config = ConfigDict(extra="ignore")

    results: list[TagSummaryEntry] = Field(default_factory=list)



class ActivityEntry(BaseModel):
    """Daily activity entry."""

    model_config = ConfigDict(extra="ignore")

    date: str = ""
    spend: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    api_requests: int = 0
    model_group: str | None = None
    team_id: str | None = None
    api_key: str | None = None


class SpendLogEntry(BaseModel):
    """Daily spend log entry from /spend/logs.

    The API returns daily aggregations with nested dicts for users and models.
    """

    model_config = ConfigDict(extra="ignore")

    startTime: str | None = None
    spend: float = 0.0
    users: dict[str, float] = Field(default_factory=dict)
    models: dict[str, float] = Field(default_factory=dict)
