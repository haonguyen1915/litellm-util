"""Virtual key schema."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VirtualKey(BaseModel):
    """Virtual API key information from LiteLLM Proxy."""

    model_config = ConfigDict(extra="ignore")

    token: str
    key: str | None = None
    key_alias: str | None = None
    key_name: str | None = None
    team_id: str | None = None
    team_alias: str | None = None
    models: list[str] = Field(default_factory=list)
    max_budget: float | None = None
    budget_duration: str | None = None
    expires: datetime | None = None
    spend: float = 0.0
    metadata: dict | None = None
    user_id: str | None = None

    @property
    def masked_key(self) -> str:
        """Return masked version of the secret key.

        Uses ``key_name`` (e.g. ``sk-...xa-A``) when available, as
        the API returns the partially-masked secret there.  Falls back
        to the ``key`` field or truncated ``token`` hash.
        """
        if self.key_name and self.key_name.startswith("sk-"):
            return self.key_name
        source = self.key or self.token
        if len(source) <= 10:
            return source
        return f"{source[:10]}...{source[-4:]}"
