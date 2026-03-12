"""Configuration schema models."""

from pydantic import BaseModel, Field


class Environment(BaseModel):
    """Environment configuration (dev, prod, etc.)."""

    url: str
    master_key: str


class Organization(BaseModel):
    """Organization configuration."""

    name: str
    environments: dict[str, Environment] = Field(default_factory=dict)


class DefaultContext(BaseModel):
    """Default active organization and environment."""

    organization: str
    environment: str


class Config(BaseModel):
    """Main configuration schema."""

    organizations: dict[str, Organization] = Field(default_factory=dict)
    default: DefaultContext | None = None
