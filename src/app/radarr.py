import logging
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class RadarrClient:
    def __init__(self):
        self.base_url = settings.radarr_url
        self.api_key = settings.radarr_api_key
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

    async def search_movie(self, title: str, year: int | None = None) -> list[dict[str, Any]]:
        """Search for movies using Radarr's lookup endpoint"""
        search_term = f"{title} {year}" if year else title

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v3/movie/lookup",
                    headers=self.headers,
                    params={"term": search_term}
                )
                response.raise_for_status()
                results = response.json()

                logger.info(f"Found {len(results)} results for '{search_term}'")
                return results

            except httpx.HTTPError as e:
                logger.error(f"Error searching Radarr: {e}")
                raise

    async def add_movie(self, movie_data: dict[str, Any]) -> dict[str, Any]:
        """Add a movie to Radarr and trigger search"""

        # Build the payload for adding a movie
        payload = {
            "title": movie_data["title"],
            "qualityProfileId": settings.quality_profile_id,
            "rootFolderPath": settings.root_folder,
            "monitored": True,
            "minimumAvailability": "released",
            "tmdbId": movie_data.get("tmdbId"),
            "imdbId": movie_data.get("imdbId"),
            "year": movie_data.get("year"),
            "titleSlug": movie_data.get("titleSlug"),
            "images": movie_data.get("images", []),
            "genres": movie_data.get("genres", []),
            "runtime": movie_data.get("runtime"),
            "overview": movie_data.get("overview"),
            "addOptions": {
                "searchForMovie": True  # This triggers the search automatically
            }
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v3/movie",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"Added movie '{movie_data['title']}' to Radarr (ID: {result.get('id')})")
                return result

            except httpx.HTTPError as e:
                logger.error(f"Error adding movie to Radarr: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response content: {e.response.text}")
                raise

    async def get_system_status(self) -> dict[str, Any]:
        """Get Radarr system status for health checks"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v3/system/status",
                    headers=self.headers
                )
                response.raise_for_status()
                return response.json()

            except httpx.HTTPError as e:
                logger.error(f"Error getting Radarr status: {e}")
                raise

    async def grab_movie(self, title: str, year: int | None = None) -> dict[str, Any]:
        """High-level method: search for movie and add it with auto-search"""

        # Search for the movie
        search_results = await self.search_movie(title, year)

        if not search_results:
            raise ValueError(f"No movies found for '{title}'")

        # Pick the first result (you could add more sophisticated selection logic)
        selected_movie = search_results[0]

        # Check if year filter should be applied
        if year:
            # Try to find a result that matches the year
            year_matches = [
                movie for movie in search_results
                if movie.get("year") == year
            ]
            if year_matches:
                selected_movie = year_matches[0]

        logger.info(f"Selected movie: {selected_movie['title']} ({selected_movie.get('year')})")

        # Add the movie to Radarr
        result = await self.add_movie(selected_movie)

        return {
            "movie": selected_movie,
            "radarr_result": result,
            "search_triggered": True
        }


# Global client instance
radarr_client = RadarrClient()
