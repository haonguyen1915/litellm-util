"""LiteLLM Proxy API client."""

from typing import Any

import httpx

from llm_cli.core.context import CurrentContext, get_current_context
from llm_cli.models.key import VirtualKey
from llm_cli.models.provider import ModelInfo, ProviderInfo
from llm_cli.models.team import Team


class APIError(Exception):
    """Raised when API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ConnectionError(Exception):
    """Raised when cannot connect to proxy."""

    pass


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class LiteLLMClient:
    """Client for interacting with LiteLLM Proxy API."""

    def __init__(
        self,
        context: CurrentContext | None = None,
        org_override: str | None = None,
        env_override: str | None = None,
    ):
        """Initialize client with context.

        Args:
            context: Optional pre-loaded context.
            org_override: Override organization.
            env_override: Override environment.
        """
        if context:
            self._context = context
        else:
            self._context = get_current_context(org_override, env_override)

        self._model_cost_cache: dict[str, Any] | None = None
        self.base_url = self._context.url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self._context.master_key}",
            "Content-Type": "application/json",
        }

    @property
    def context(self) -> CurrentContext:
        """Get current context."""
        return self._context

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and errors.

        Args:
            response: HTTP response object.

        Returns:
            Response JSON data.

        Raises:
            AuthenticationError: If 401/403.
            APIError: For other errors.
        """
        if response.status_code == 401 or response.status_code == 403:
            raise AuthenticationError(
                "Authentication failed. Master key may be invalid or expired."
            )

        if response.status_code >= 400:
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and "error" in error_data:
                    err = error_data["error"]
                    message = err.get("message", str(err)) if isinstance(err, dict) else str(err)
                else:
                    message = error_data.get(
                        "detail", error_data.get("message", str(error_data))
                    )
            except Exception:
                message = response.text or f"HTTP {response.status_code}"

            raise APIError(message, response.status_code)

        try:
            return response.json()
        except Exception:
            return {}

    def _request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list:
        """Make HTTP request to API.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            json: JSON body.
            params: Query parameters.

        Returns:
            Response data (dict or list).

        Raises:
            ConnectionError: If cannot connect.
            AuthenticationError: If auth fails.
            APIError: For other errors.
        """
        url = f"{self.base_url}{endpoint}"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json,
                    params=params,
                )
                return self._handle_response(response)
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to LiteLLM Proxy at {self.base_url}"
            )
        except httpx.TimeoutException:
            raise ConnectionError(
                f"Connection to {self.base_url} timed out"
            )
        except (AuthenticationError, APIError, ConnectionError):
            raise
        except Exception as e:
            raise APIError(f"Unexpected error: {e}")

    # ==================== Provider Operations ====================

    def list_providers(self) -> list[ProviderInfo]:
        """List providers grouped from models deployed on proxy.

        Fetches /model/info and groups models by provider prefix.

        Returns:
            List of ProviderInfo with real model data from proxy.
        """
        raw_models = self.list_models()

        providers_map: dict[str, list[ModelInfo]] = {}

        for m in raw_models:
            litellm_model = m.get("litellm_params", {}).get("model", "")
            model_name = m.get("model_name", "")
            info = m.get("model_info", {}) or {}

            if "/" in litellm_model:
                provider_id = litellm_model.split("/")[0]
            else:
                provider_id = "openai"

            model_info = self._parse_model_info(model_name, provider_id, info)

            if provider_id not in providers_map:
                providers_map[provider_id] = []
            providers_map[provider_id].append(model_info)

        result: list[ProviderInfo] = []
        for pid, models in sorted(providers_map.items()):
            result.append(
                ProviderInfo(
                    id=pid,
                    name=pid.replace("_", " ").title(),
                    description=f"{len(models)} models deployed",
                    models=models,
                )
            )

        return result

    def list_supported_models(self, provider_id: str | None = None) -> list[ProviderInfo]:
        """List all models supported by LiteLLM.

        Tries /model_cost endpoint first, falls back to GitHub JSON.
        Groups by litellm_provider. Only includes 'chat' mode models.

        Args:
            provider_id: Optional filter by provider.

        Returns:
            List of ProviderInfo with all supported models.
        """
        response = self._fetch_model_cost_map()

        providers_map: dict[str, list[ModelInfo]] = {}

        for model_key, info in response.items():
            if not isinstance(info, dict):
                continue

            # Only include chat models
            if info.get("mode") != "chat":
                continue

            pid = info.get("litellm_provider", "")
            if not pid:
                continue

            # Filter by provider if specified
            if provider_id and pid != provider_id:
                continue

            model_info = self._parse_model_info(model_key, pid, info)

            if pid not in providers_map:
                providers_map[pid] = []
            providers_map[pid].append(model_info)

        result: list[ProviderInfo] = []
        for pid, models in sorted(providers_map.items()):
            result.append(
                ProviderInfo(
                    id=pid,
                    name=pid.replace("_", " ").replace("-", " ").title(),
                    description=f"{len(models)} models available",
                    models=models,
                )
            )

        return result

    def _fetch_model_cost_map(self) -> dict[str, Any]:
        """Fetch model cost map from proxy or GitHub.

        Tries /model_cost endpoint first, falls back to LiteLLM GitHub.
        Results are cached for the lifetime of the client.
        """
        if self._model_cost_cache is not None:
            return self._model_cost_cache

        # Try proxy endpoint first
        try:
            result = self._request("GET", "/model_cost")
            if isinstance(result, dict) and len(result) > 10:
                self._model_cost_cache = result
                return result
        except (APIError, ConnectionError):
            pass

        # Fallback: fetch from LiteLLM GitHub
        url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    result = resp.json()
                    self._model_cost_cache = result
                    return result
        except Exception:
            pass

        raise APIError("Could not fetch model cost data from proxy or GitHub")

    @staticmethod
    def _parse_model_info(model_id: str, provider_id: str, info: dict) -> ModelInfo:
        """Parse model info dict into ModelInfo."""
        capabilities: list[str] = []
        if info.get("supports_vision"):
            capabilities.append("vision")
        if info.get("supports_function_calling"):
            capabilities.append("tools")
        if info.get("supports_reasoning"):
            capabilities.append("reasoning")
        if info.get("supports_audio_input"):
            capabilities.append("audio")
        if info.get("supports_web_search"):
            capabilities.append("web_search")

        input_cost = info.get("input_cost_per_token")
        output_cost = info.get("output_cost_per_token")
        input_price = (input_cost * 1_000_000) if input_cost else 0.0
        output_price = (output_cost * 1_000_000) if output_cost else 0.0

        return ModelInfo(
            id=model_id,
            provider=provider_id,
            context_window=info.get("max_input_tokens") or 0,
            max_output=info.get("max_output_tokens") or 0,
            input_price=round(input_price, 2),
            output_price=round(output_price, 2),
            capabilities=capabilities,
        )

    # ==================== Model Operations ====================

    def list_models(self) -> list[dict[str, Any]]:
        """List all models on proxy.

        Returns:
            List of model info dicts.
        """
        response = self._request("GET", "/model/info")
        return response.get("data", [])

    def create_model(
        self,
        model_name: str,
        litellm_params: dict[str, Any],
        model_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new model on proxy.

        Args:
            model_name: Display name/alias for the model.
            litellm_params: LiteLLM parameters (model, api_key, etc.).
            model_info: Optional metadata.

        Returns:
            Created model info.
        """
        # Sanitize string values in litellm_params
        clean_params = {}
        for k, v in litellm_params.items():
            clean_params[k] = v.strip() if isinstance(v, str) else v

        data = {
            "model_name": model_name,
            "litellm_params": clean_params,
        }
        if model_info:
            data["model_info"] = model_info

        return self._request("POST", "/model/new", json=data)

    def delete_model(self, model_id: str) -> dict[str, Any]:
        """Delete a model from proxy.

        Args:
            model_id: Model ID to delete.

        Returns:
            Response data.
        """
        return self._request("POST", "/model/delete", json={"id": model_id})

    # ==================== Key Operations ====================

    def list_keys(self) -> list[VirtualKey]:
        """List all virtual keys.

        Returns:
            List of VirtualKey objects.
        """
        response = self._request(
            "GET", "/key/list", params={"return_full_object": "true", "limit": 100}
        )
        keys_data = response.get("keys", response.get("data", []))

        keys = []
        for key_data in keys_data:
            try:
                keys.append(VirtualKey.model_validate(key_data))
            except Exception:
                # Skip malformed keys
                continue

        return keys

    def create_key(
        self,
        key_alias: str | None = None,
        team_id: str | None = None,
        models: list[str] | None = None,
        max_budget: float | None = None,
        budget_duration: str | None = None,
        expires: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new virtual key.

        Args:
            key_alias: Display name for the key.
            team_id: Team to assign key to.
            models: List of allowed model names.
            max_budget: Maximum budget.
            budget_duration: Budget period (e.g., 'monthly').
            expires: Expiration date string.
            metadata: Additional metadata.

        Returns:
            Created key info including the key itself.
        """
        data: dict[str, Any] = {}

        if key_alias:
            data["key_alias"] = key_alias
        if team_id:
            data["team_id"] = team_id
        # Models: specific list or "all-team-models" sentinel
        if models:
            data["models"] = models
        else:
            data["models"] = ["all-team-models"]
        if max_budget is not None:
            data["max_budget"] = max_budget
        if budget_duration:
            # LiteLLM API expects "30d" format, not "monthly"
            duration_map = {"monthly": "30d", "daily": "1d", "weekly": "7d"}
            data["budget_duration"] = duration_map.get(budget_duration, budget_duration)
        if expires:
            data["expires"] = expires
        if metadata:
            data["metadata"] = metadata

        return self._request("POST", "/key/generate", json=data)

    def delete_key(self, key: str) -> dict[str, Any]:
        """Delete a virtual key.

        Args:
            key: The key token to delete.

        Returns:
            Response data.
        """
        return self._request("POST", "/key/delete", json={"keys": [key]})

    # ==================== Team Operations ====================

    def list_teams(self) -> list[Team]:
        """List all teams.

        Returns:
            List of Team objects.
        """
        response = self._request("GET", "/team/list")
        teams_data = response if isinstance(response, list) else response.get("teams", [])

        teams = []
        for team_data in teams_data:
            try:
                teams.append(Team.model_validate(team_data))
            except Exception:
                # Skip malformed teams
                continue

        return teams

    def create_team(
        self,
        team_alias: str,
        team_id: str | None = None,
        models: list[str] | None = None,
        max_budget: float | None = None,
        budget_duration: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new team.

        Args:
            team_alias: Display name for the team.
            team_id: Optional team ID (slug).
            models: List of allowed model names.
            max_budget: Maximum budget.
            budget_duration: Budget period.
            metadata: Additional metadata.

        Returns:
            Created team info.
        """
        data: dict[str, Any] = {"team_alias": team_alias}

        if team_id:
            data["team_id"] = team_id
        # Models: specific list or "no-default-models" sentinel
        if models:
            data["models"] = models
        else:
            data["models"] = ["no-default-models"]
        if max_budget is not None:
            data["max_budget"] = max_budget
        if budget_duration:
            duration_map = {"monthly": "30d", "daily": "1d", "weekly": "7d"}
            data["budget_duration"] = duration_map.get(budget_duration, budget_duration)
        if metadata:
            data["metadata"] = metadata

        return self._request("POST", "/team/new", json=data)

    def update_team(
        self,
        team_id: str,
        team_alias: str | None = None,
        models: list[str] | None = None,
        max_budget: float | None = None,
        budget_duration: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update an existing team.

        Args:
            team_id: Team ID to update.
            team_alias: New display name.
            models: New list of allowed models.
            max_budget: New budget.
            budget_duration: New budget period.
            metadata: New metadata.

        Returns:
            Updated team info.
        """
        data: dict[str, Any] = {"team_id": team_id}

        if team_alias is not None:
            data["team_alias"] = team_alias
        if models is not None:
            data["models"] = models
        if max_budget is not None:
            data["max_budget"] = max_budget
        if budget_duration is not None:
            duration_map = {"monthly": "30d", "daily": "1d", "weekly": "7d"}
            data["budget_duration"] = duration_map.get(budget_duration, budget_duration)
        if metadata is not None:
            data["metadata"] = metadata

        return self._request("POST", "/team/update", json=data)

    def delete_team(self, team_id: str) -> dict[str, Any]:
        """Delete a team.

        Args:
            team_id: Team ID to delete.

        Returns:
            Response data.
        """
        return self._request("POST", "/team/delete", json={"team_ids": [team_id]})

    # ==================== Model Testing ====================

    @staticmethod
    def test_model_completion(
        model_name: str,
        litellm_params: dict[str, Any],
    ) -> tuple[bool, str]:
        """Test a model by calling the provider API directly via litellm SDK.

        Sends a minimal completion request directly to the provider
        (bypasses the proxy) to verify credentials and model access.

        Args:
            model_name: Display name (unused, kept for interface compatibility).
            litellm_params: LiteLLM parameters (model, api_key, etc.).

        Returns:
            Tuple of (success, message).
        """
        import litellm

        # Sanitize params - strip whitespace from string values
        clean_params = {}
        for k, v in litellm_params.items():
            clean_params[k] = v.strip() if isinstance(v, str) else v

        model = clean_params.pop("model")
        try:
            litellm.completion(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
                **clean_params,
            )
            return True, "Model responded successfully"
        except litellm.AuthenticationError:
            return False, "Authentication failed - check your API key"
        except litellm.NotFoundError:
            return False, f"Model '{model}' not found - check provider/model ID"
        except litellm.RateLimitError:
            # Rate limited means credentials work, model is accessible
            return True, "Model is accessible (rate limited on test request)"
        except litellm.BadRequestError as e:
            return False, f"Bad request: {e}"
        except litellm.APIConnectionError as e:
            return False, f"Cannot connect to provider API: {e}"
        except litellm.Timeout:
            return False, "Request timed out - provider may be slow or unreachable"
        except Exception as e:
            # Extract meaningful message from litellm exceptions
            msg = str(e)
            # Truncate very long error messages
            if len(msg) > 200:
                msg = msg[:200] + "..."
            return False, msg

    # ==================== Health Check ====================

    def health_check(self) -> bool:
        """Check if proxy is reachable.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            self._request("GET", "/health")
            return True
        except Exception:
            return False
