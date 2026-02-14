"""Tests for settings endpoints."""

from fastapi.testclient import TestClient

from app.core.config import settings


class TestApiKeyStatus:
    """Test the /api/v1/settings/api-keys endpoint."""

    def test_get_api_keys_as_superuser(
        self, client: TestClient, superuser_token_headers: dict[str, str]
    ):
        resp = client.get(
            f"{settings.API_V1_STR}/settings/api-keys",
            headers=superuser_token_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "os_configured" in data
        assert "here_configured" in data
        assert "mapillary_configured" in data
        assert isinstance(data["os_configured"], bool)

    def test_get_api_keys_as_normal_user(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ):
        resp = client.get(
            f"{settings.API_V1_STR}/settings/api-keys",
            headers=normal_user_token_headers,
        )
        assert resp.status_code == 403

    def test_get_api_keys_unauthenticated(self, client: TestClient):
        resp = client.get(f"{settings.API_V1_STR}/settings/api-keys")
        assert resp.status_code == 401
