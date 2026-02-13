"""Tests for vehicles API endpoints."""

from fastapi.testclient import TestClient

from app.core.config import settings


class TestListVehicles:
    def test_list_all(self, client: TestClient) -> None:
        response = client.get(f"{settings.API_V1_STR}/vehicles/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_vehicle_structure(self, client: TestClient) -> None:
        response = client.get(f"{settings.API_V1_STR}/vehicles/")
        data = response.json()
        required = {"name", "vehicle_class", "width_m", "height_m", "weight_kg", "turning_radius_m"}
        for v in data:
            assert required.issubset(v.keys())


class TestGetVehicle:
    def test_get_existing(self, client: TestClient) -> None:
        # First get list to find a valid class
        list_resp = client.get(f"{settings.API_V1_STR}/vehicles/")
        vehicles = list_resp.json()
        assert len(vehicles) > 0
        vehicle_class = vehicles[0]["vehicle_class"]

        response = client.get(f"{settings.API_V1_STR}/vehicles/{vehicle_class}")
        assert response.status_code == 200
        data = response.json()
        assert data["vehicle_class"] == vehicle_class

    def test_get_not_found(self, client: TestClient) -> None:
        response = client.get(f"{settings.API_V1_STR}/vehicles/nonexistent_class")
        assert response.status_code == 404
