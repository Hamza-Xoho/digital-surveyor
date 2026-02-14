"""Tests for saved locations CRUD endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings


class TestSavedLocations:
    """Test the /api/v1/locations/ endpoints."""

    @patch(
        "app.api.routes.locations.geocode_postcode",
        new_callable=AsyncMock,
        return_value={
            "postcode": "BN1 1AB",
            "latitude": 50.8225,
            "longitude": -0.1372,
            "easting": 530500,
            "northing": 104500,
        },
    )
    def test_create_location(
        self, mock_geocode, client: TestClient, normal_user_token_headers: dict[str, str]
    ):
        resp = client.post(
            f"{settings.API_V1_STR}/locations/",
            headers=normal_user_token_headers,
            json={"label": "Test Home", "postcode": "BN1 1AB"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["label"] == "Test Home"
        assert data["postcode"] == "BN1 1AB"
        assert "id" in data

    def test_create_location_unauthenticated(self, client: TestClient):
        resp = client.post(
            f"{settings.API_V1_STR}/locations/",
            json={"label": "Test", "postcode": "BN1 1AB"},
        )
        assert resp.status_code == 401

    @patch(
        "app.api.routes.locations.geocode_postcode",
        new_callable=AsyncMock,
        return_value={
            "postcode": "BN1 1AB",
            "latitude": 50.8225,
            "longitude": -0.1372,
            "easting": 530500,
            "northing": 104500,
        },
    )
    def test_list_locations(
        self, mock_geocode, client: TestClient, normal_user_token_headers: dict[str, str]
    ):
        # Create a location first
        client.post(
            f"{settings.API_V1_STR}/locations/",
            headers=normal_user_token_headers,
            json={"label": "List Test", "postcode": "BN1 1AB"},
        )
        # List
        resp = client.get(
            f"{settings.API_V1_STR}/locations/",
            headers=normal_user_token_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @patch(
        "app.api.routes.locations.geocode_postcode",
        new_callable=AsyncMock,
        return_value={
            "postcode": "BN1 1AB",
            "latitude": 50.8225,
            "longitude": -0.1372,
            "easting": 530500,
            "northing": 104500,
        },
    )
    def test_delete_location(
        self, mock_geocode, client: TestClient, normal_user_token_headers: dict[str, str]
    ):
        # Create
        resp = client.post(
            f"{settings.API_V1_STR}/locations/",
            headers=normal_user_token_headers,
            json={"label": "To Delete", "postcode": "BN1 1AB"},
        )
        loc_id = resp.json()["id"]
        # Delete
        resp = client.delete(
            f"{settings.API_V1_STR}/locations/{loc_id}",
            headers=normal_user_token_headers,
        )
        assert resp.status_code == 200

    def test_delete_nonexistent_location(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ):
        resp = client.delete(
            f"{settings.API_V1_STR}/locations/00000000-0000-0000-0000-000000000000",
            headers=normal_user_token_headers,
        )
        assert resp.status_code == 404
