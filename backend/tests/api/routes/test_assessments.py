"""Tests for assessment API endpoints."""

from fastapi.testclient import TestClient

from app.core.config import settings


class TestQuickAssessment:
    def test_invalid_postcode_400(self, client: TestClient) -> None:
        response = client.post(
            f"{settings.API_V1_STR}/assessments/quick",
            params={"postcode": "INVALID"},
        )
        assert response.status_code == 400

    def test_empty_postcode_422(self, client: TestClient) -> None:
        response = client.post(f"{settings.API_V1_STR}/assessments/quick")
        assert response.status_code == 422  # Missing required param


class TestGeodataEndpoint:
    def test_invalid_postcode_400(self, client: TestClient) -> None:
        response = client.get(
            f"{settings.API_V1_STR}/assessments/geodata/INVALID"
        )
        assert response.status_code == 400


class TestListAssessments:
    def test_requires_auth(self, client: TestClient) -> None:
        response = client.get(f"{settings.API_V1_STR}/assessments/")
        assert response.status_code == 401

    def test_authenticated_returns_list(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        response = client.get(
            f"{settings.API_V1_STR}/assessments/",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "count" in data


class TestGetAssessmentDetail:
    def test_not_found(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        import uuid
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"{settings.API_V1_STR}/assessments/{fake_id}",
            headers=normal_user_token_headers,
        )
        assert response.status_code == 404
