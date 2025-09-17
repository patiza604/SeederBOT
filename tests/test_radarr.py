import pytest
from unittest.mock import AsyncMock, patch

from src.app.radarr import RadarrClient


@pytest.fixture
def radarr_client():
    return RadarrClient()


@pytest.mark.asyncio
async def test_grab_movie_integration(radarr_client):
    """Test the high-level grab_movie method with mocked dependencies"""

    # Mock search results
    search_results = [
        {
            "title": "Inception",
            "year": 2010,
            "tmdbId": 27205,
            "imdbId": "tt1375666",
            "titleSlug": "inception-2010",
            "runtime": 148,
            "overview": "Dom Cobb is a skilled thief...",
            "images": [],
            "genres": ["Action", "Sci-Fi"]
        }
    ]

    # Mock add result
    add_result = {
        "id": 123,
        "title": "Inception",
        "year": 2010,
        "monitored": True
    }

    with patch.object(radarr_client, 'search_movie', return_value=search_results) as mock_search, \
         patch.object(radarr_client, 'add_movie', return_value=add_result) as mock_add:

        result = await radarr_client.grab_movie("Inception", 2010)

        # Verify search was called
        mock_search.assert_called_once_with("Inception", 2010)

        # Verify add was called with the first search result
        mock_add.assert_called_once_with(search_results[0])

        # Verify result structure
        assert result["search_triggered"] is True
        assert result["movie"]["title"] == "Inception"
        assert result["radarr_result"]["id"] == 123


@pytest.mark.asyncio
async def test_grab_movie_no_results(radarr_client):
    """Test grab_movie when no search results are found"""

    with patch.object(radarr_client, 'search_movie', return_value=[]):
        with pytest.raises(ValueError, match="No movies found"):
            await radarr_client.grab_movie("NonexistentMovie")


@pytest.mark.asyncio
async def test_grab_movie_year_filtering(radarr_client):
    """Test that grab_movie properly filters by year"""

    search_results = [
        {"title": "Inception", "year": 2020, "tmdbId": 12345},  # Wrong year
        {"title": "Inception", "year": 2010, "tmdbId": 27205}   # Correct year
    ]

    add_result = {"id": 123, "title": "Inception", "year": 2010}

    with patch.object(radarr_client, 'search_movie', return_value=search_results), \
         patch.object(radarr_client, 'add_movie', return_value=add_result) as mock_add:

        result = await radarr_client.grab_movie("Inception", 2010)

        # Should have selected the 2010 version
        mock_add.assert_called_once()
        called_movie = mock_add.call_args[0][0]
        assert called_movie["year"] == 2010
        assert called_movie["tmdbId"] == 27205


@pytest.mark.asyncio
async def test_config_validation(radarr_client):
    """Test that RadarrClient is properly configured"""
    assert radarr_client.base_url is not None
    assert radarr_client.api_key is not None
    assert "X-Api-Key" in radarr_client.headers
    assert radarr_client.headers["Content-Type"] == "application/json"