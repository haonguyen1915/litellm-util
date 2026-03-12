"""Team schema."""

from pydantic import BaseModel, ConfigDict, Field


class Team(BaseModel):
    """Team information from LiteLLM Proxy."""

    model_config = ConfigDict(extra="ignore")

    team_id: str
    team_alias: str | None = None
    models: list[str] = Field(default_factory=list)
    max_budget: float | None = None
    budget_duration: str | None = None  # e.g., "monthly", "daily"
    metadata: dict | None = None
    members: list = Field(default_factory=list)
    blocked: bool = False
