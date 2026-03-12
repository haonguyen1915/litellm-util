"""Integration tests for LiteLLMClient against a real proxy.

Uses TEST_LITELLM_URL and TEST_LITELLM_KEY from .env file.
Requires a running LiteLLM Proxy server.
"""

import os
import uuid

import pytest
from dotenv import load_dotenv

from llm_cli.core.client import APIError, LiteLLMClient
from llm_cli.core.context import CurrentContext

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

LITELLM_URL = os.getenv("TEST_LITELLM_URL")
LITELLM_KEY = os.getenv("TEST_LITELLM_KEY")

# Skip all tests if env vars not set
pytestmark = pytest.mark.skipif(
    not LITELLM_URL or not LITELLM_KEY,
    reason="TEST_LITELLM_URL and TEST_LITELLM_KEY not set",
)


@pytest.fixture
def client():
    """Create a LiteLLMClient with test credentials."""
    context = CurrentContext(
        organization_id="test",
        organization_name="Test",
        environment="test",
        url=LITELLM_URL,
        master_key=LITELLM_KEY,
    )
    return LiteLLMClient(context=context)


@pytest.fixture
def unique_id():
    """Generate a unique suffix for test resources."""
    return uuid.uuid4().hex[:8]


# ==================== Health Check ====================


class TestHealthCheck:
    def test_health_check(self, client):
        """Proxy should be healthy."""
        assert client.health_check() is True

    def test_health_check_bad_url(self):
        """Bad URL should return False."""
        context = CurrentContext(
            organization_id="test",
            organization_name="Test",
            environment="test",
            url="http://localhost:19999",
            master_key="bad-key",
        )
        bad_client = LiteLLMClient(context=context)
        assert bad_client.health_check() is False


# ==================== Model Operations ====================


class TestModelOperations:
    def test_list_models(self, client):
        """Should list models from the proxy."""
        models = client.list_models()

        assert isinstance(models, list)
        assert len(models) > 0

        # Each model should have expected structure
        first_model = models[0]
        assert "model_name" in first_model
        assert "litellm_params" in first_model
        assert "model" in first_model["litellm_params"]

    def test_model_create_and_delete(self, client, unique_id):
        """Should create and then delete a model."""
        model_name = f"test-model-{unique_id}"

        # Create
        result = client.create_model(
            model_name=model_name,
            litellm_params={"model": "openai/gpt-3.5-turbo"},
        )
        assert result is not None

        # Verify it exists
        models = client.list_models()
        created = [m for m in models if m.get("model_name") == model_name]
        assert len(created) == 1

        # Delete
        model_id = created[0].get("model_info", {}).get("id")
        assert model_id is not None
        client.delete_model(model_id)

        # Verify it's gone
        models_after = client.list_models()
        remaining = [m for m in models_after if m.get("model_name") == model_name]
        assert len(remaining) == 0


# ==================== Key Operations ====================


class TestKeyOperations:
    def test_list_keys(self, client):
        """Should list virtual keys."""
        keys = client.list_keys()

        assert isinstance(keys, list)
        # There should be at least one key (the master key itself or others)
        # Don't assert > 0 since some envs may have no keys returned for this endpoint

    def test_key_create_and_delete(self, client, unique_id):
        """Should create and then delete a key."""
        alias = f"test-key-{unique_id}"

        # Create
        result = client.create_key(key_alias=alias)

        assert result is not None
        assert "key" in result or "token" in result
        key_value = result.get("key", result.get("token"))
        assert key_value is not None
        assert len(key_value) > 10

        # Delete using the key value
        delete_result = client.delete_key(key_value)
        assert delete_result is not None

    def test_key_create_with_budget(self, client, unique_id):
        """Should create a key with budget."""
        alias = f"test-budget-key-{unique_id}"

        result = client.create_key(
            key_alias=alias,
            max_budget=100.0,
            budget_duration="monthly",
        )

        assert result is not None
        key_value = result.get("key", result.get("token"))

        # Cleanup
        client.delete_key(key_value)


# ==================== Team Operations ====================


class TestTeamOperations:
    def test_list_teams(self, client):
        """Should list teams."""
        teams = client.list_teams()

        assert isinstance(teams, list)
        assert len(teams) > 0

        first_team = teams[0]
        assert first_team.team_id is not None
        assert first_team.team_alias is not None or first_team.team_id is not None

    def test_team_create_update_delete(self, client, unique_id):
        """Should create, update, and then delete a team."""
        team_alias = f"Test Team {unique_id}"
        team_id = f"test-team-{unique_id}"

        # Create
        result = client.create_team(
            team_alias=team_alias,
            team_id=team_id,
        )
        assert result is not None

        # Verify it exists
        teams = client.list_teams()
        created = [t for t in teams if t.team_id == team_id]
        assert len(created) == 1
        assert created[0].team_alias == team_alias

        # Update
        new_alias = f"Updated Team {unique_id}"
        update_result = client.update_team(
            team_id=team_id,
            team_alias=new_alias,
            max_budget=500.0,
            budget_duration="monthly",
        )
        assert update_result is not None

        # Verify update
        teams_after = client.list_teams()
        updated = [t for t in teams_after if t.team_id == team_id]
        assert len(updated) == 1
        assert updated[0].team_alias == new_alias

        # Delete
        client.delete_team(team_id)

        # Verify deletion
        teams_final = client.list_teams()
        remaining = [t for t in teams_final if t.team_id == team_id]
        assert len(remaining) == 0

    def test_team_create_with_models(self, client, unique_id):
        """Should create a team with model restrictions."""
        team_id = f"test-models-team-{unique_id}"

        # Get available models first
        models = client.list_models()
        if models:
            model_names = [m.get("model_name") for m in models[:2]]
        else:
            model_names = ["gpt-3.5-turbo"]

        result = client.create_team(
            team_alias=f"Models Team {unique_id}",
            team_id=team_id,
            models=model_names,
        )
        assert result is not None

        # Cleanup
        client.delete_team(team_id)


# ==================== Full Workflow ====================


class TestFullWorkflow:
    def test_team_key_workflow(self, client, unique_id):
        """Test creating a team, then a key for that team."""
        team_id = f"test-wf-team-{unique_id}"

        # 1. Create team
        client.create_team(
            team_alias=f"Workflow Team {unique_id}",
            team_id=team_id,
        )

        # 2. Create key for team
        result = client.create_key(
            key_alias=f"wf-key-{unique_id}",
            team_id=team_id,
        )
        key_value = result.get("key", result.get("token"))
        assert key_value is not None

        # 3. Verify key is in list
        keys = client.list_keys()
        team_keys = [k for k in keys if k.team_id == team_id]
        assert len(team_keys) >= 1

        # 4. Cleanup - delete key first, then team
        client.delete_key(key_value)
        client.delete_team(team_id)
