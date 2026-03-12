"""Integration tests for LiteLLMClient against a real proxy.

Uses TEST_LITELLM_URL and TEST_LITELLM_KEY from .env file.
Requires a running LiteLLM Proxy server.
"""

import os
import time
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


# ==================== Provider Operations ====================


class TestProviderOperations:
    def test_list_providers(self, client):
        """Should list providers grouped from proxy models."""
        providers = client.list_providers()

        assert isinstance(providers, list)
        assert len(providers) > 0

        # Each provider should have expected structure
        for p in providers:
            assert p.id
            assert p.name
            assert len(p.models) > 0
            assert p.description

    def test_providers_have_model_info(self, client):
        """Provider models should have pricing and token info from proxy."""
        providers = client.list_providers()

        # Find a provider with populated data (not all models have full info)
        models_with_pricing = []
        for p in providers:
            for m in p.models:
                if m.input_price > 0:
                    models_with_pricing.append(m)

        assert len(models_with_pricing) > 0, "At least some models should have pricing"

        # Check a model with pricing has valid data
        model = models_with_pricing[0]
        assert model.id
        assert model.provider
        assert model.input_price > 0
        assert model.output_price > 0

    def test_providers_group_by_prefix(self, client):
        """Models should be grouped by provider prefix."""
        providers = client.list_providers()
        provider_ids = [p.id for p in providers]

        # The test proxy has anthropic and azure models
        assert "anthropic" in provider_ids or "openai" in provider_ids


# ==================== Supported Models (model_cost) ====================


class TestSupportedModels:
    def test_list_supported_models(self, client):
        """Should list all LiteLLM-supported providers from model cost map."""
        providers = client.list_supported_models()

        assert isinstance(providers, list)
        # LiteLLM supports many providers (50+)
        assert len(providers) > 30

        for p in providers:
            assert p.id
            assert p.name
            assert len(p.models) > 0

    def test_supported_models_filter_by_provider(self, client):
        """Should filter supported models by provider."""
        providers = client.list_supported_models(provider_id="anthropic")

        assert len(providers) == 1
        assert providers[0].id == "anthropic"
        assert len(providers[0].models) > 5

        # All models should belong to anthropic
        for m in providers[0].models:
            assert m.provider == "anthropic"

    def test_supported_models_have_pricing(self, client):
        """Supported models should have pricing info."""
        providers = client.list_supported_models(provider_id="openai")

        assert len(providers) == 1
        models_with_pricing = [m for m in providers[0].models if m.input_price > 0]
        assert len(models_with_pricing) > 0

    def test_supported_models_have_capabilities(self, client):
        """Supported models should have capability info."""
        providers = client.list_supported_models(provider_id="anthropic")

        assert len(providers) == 1
        models_with_caps = [m for m in providers[0].models if len(m.capabilities) > 0]
        assert len(models_with_caps) > 0

    def test_supported_models_nonexistent_provider(self, client):
        """Non-existent provider should return empty list."""
        providers = client.list_supported_models(provider_id="nonexistent_xxx")
        assert providers == []


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

        # Wait for proxy cache to refresh
        time.sleep(2)

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
