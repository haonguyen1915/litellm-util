"""Virtual key schema."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VirtualKey(BaseModel):
    """Virtual API key information from LiteLLM Proxy."""

    model_config = ConfigDict(extra="ignore")

    token: str
    key_alias: str | None = None
    key_name: str | None = None
    team_id: str | None = None
    models: list[str] = Field(default_factory=list)
    max_budget: float | None = None
    budget_duration: str | None = None
    expires: datetime | None = None
    spend: float = 0.0
    metadata: dict | None = None
    user_id: str | None = None

    @property
    def masked_key(self) -> str:
        """Return masked version of the key."""
        if len(self.token) <= 10:
            return self.token
        return f"{self.token[:7]}...{self.token[-6:]}"
