
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.app.config import settings
from src.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": f"Bearer {settings.app_token}"}


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["mode"] == settings.mode
    assert data["version"] == "0.1.0"


def test_grab_endpoint_requires_auth(client):
    response = client.post("/grab", json={"title": "Test Movie"})
    assert response.status_code == 403  # FastAPI returns 403 for missing auth header


def test_grab_endpoint_invalid_token(client):
    headers = {"Authorization": "Bearer invalid-token"}
    response = client.post("/grab", json={"title": "Test Movie"}, headers=headers)
    assert response.status_code == 401


def test_grab_endpoint_valid_request(client, auth_headers):
    response = client.post(
        "/grab",
        json={"title": "Inception 2010"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"  # Expected since Radarr not accessible in test
    assert "Failed to add movie to Radarr" in data["message"]


def test_grab_endpoint_with_year(client, auth_headers):
    response = client.post(
        "/grab",
        json={"title": "Inception", "year": 2010},
        headers=auth_headers
    )
    assert response.status_code == 200


def test_grab_endpoint_validation(client, auth_headers):
    # Missing title
    response = client.post("/grab", json={}, headers=auth_headers)
    assert response.status_code == 422

    # Invalid type
    response = client.post(
        "/grab",
        json={"title": "Test", "type": "invalid"},
        headers=auth_headers
    )
    assert response.status_code == 422


@patch('src.app.main.settings.mode', 'blackhole')
def test_grab_endpoint_blackhole_mode(client, auth_headers):
    """Test grab endpoint in blackhole mode"""
    mock_result = {
        "method": "blackhole",
        "title": "Test Movie",
        "year": 2023,
        "torrent": {
            "title": "Test.Movie.2023.1080p.WEB-DL.x264",
            "seeders": 50,
            "size": 4 * 1024 * 1024 * 1024
        },
        "download": {
            "filename": "test_movie.torrent",
            "path": "/tmp/test/test_movie.torrent"
        },
        "watch_dir": "/tmp/test"
    }

    with patch('src.app.main.blackhole_client.grab_via_blackhole', new_callable=AsyncMock) as mock_grab:
        mock_grab.return_value = mock_result

        response = client.post(
            "/grab",
            json={"title": "Test Movie", "year": 2023},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "blackhole" in data["message"]
        assert data["details"]["mode"] == "blackhole"
        assert data["details"]["torrent_title"] == "Test.Movie.2023.1080p.WEB-DL.x264"


@patch('src.app.main.settings.mode', 'blackhole')
def test_grab_endpoint_blackhole_mode_no_results(client, auth_headers):
    """Test grab endpoint in blackhole mode when no torrents found"""

    with patch('src.app.main.blackhole_client.grab_via_blackhole', new_callable=AsyncMock) as mock_grab:
        mock_grab.side_effect = ValueError("No suitable torrents found for 'Nonexistent Movie'")

        response = client.post(
            "/grab",
            json={"title": "Nonexistent Movie", "year": 2023},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "No suitable torrents found" in data["message"]

