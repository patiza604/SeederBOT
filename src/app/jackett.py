import logging
import re
from typing import Any

import httpx

from .config import settings

logger = logging.getLogger(__name__)


class JackettClient:
    def __init__(self):
        self.base_url = settings.jackett_url
        self.api_key = settings.jackett_api_key
        self.categories = settings.categories
        self.min_seeders = settings.min_seeders
        self.quality_regex = re.compile(settings.quality_regex, re.IGNORECASE)
        self.exclude_regex = re.compile(settings.exclude_regex, re.IGNORECASE)
        self.min_size_bytes = int(settings.min_size_gb * 1024 * 1024 * 1024)
        self.max_size_bytes = int(settings.max_size_gb * 1024 * 1024 * 1024)

    async def search_torrents(self, query: str) -> list[dict[str, Any]]:
        """Search for torrents using Jackett's Torznab API"""

        params = {
            "apikey": self.api_key,
            "t": "search",
            "cat": self.categories,
            "q": query
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/v2.0/indexers/all/results/torznab",
                    params=params
                )
                response.raise_for_status()

                # Parse XML response and convert to dict
                results = self._parse_torznab_response(response.text)

                logger.info(f"Found {len(results)} raw results for '{query}'")
                return results

            except httpx.HTTPError as e:
                logger.error(f"Error searching Jackett: {e}")
                raise

    def _parse_torznab_response(self, xml_content: str) -> list[dict[str, Any]]:
        """Parse Torznab XML response into list of torrent dictionaries"""
        import xml.etree.ElementTree as ET

        results = []

        try:
            root = ET.fromstring(xml_content)

            # Find all items in the RSS feed
            for item in root.findall(".//item"):
                torrent = {}

                # Basic fields
                torrent["title"] = self._get_text(item.find("title"))
                torrent["link"] = self._get_text(item.find("link"))
                torrent["guid"] = self._get_text(item.find("guid"))
                torrent["pubDate"] = self._get_text(item.find("pubDate"))
                torrent["description"] = self._get_text(item.find("description"))

                # Parse torznab attributes
                for attr in item.findall(".//{http://torznab.com/schemas/2015/feed}attr"):
                    name = attr.get("name")
                    value = attr.get("value")

                    if name == "size":
                        torrent["size"] = int(value) if value else 0
                    elif name == "seeders":
                        torrent["seeders"] = int(value) if value else 0
                    elif name == "peers":
                        torrent["peers"] = int(value) if value else 0
                    elif name == "downloadvolumefactor":
                        torrent["downloadvolumefactor"] = float(value) if value else 1.0
                    elif name == "uploadvolumefactor":
                        torrent["uploadvolumefactor"] = float(value) if value else 1.0
                    elif name == "grabs":
                        torrent["grabs"] = int(value) if value else 0

                # Extract download URL from enclosure or link
                enclosure = item.find("enclosure")
                if enclosure is not None:
                    torrent["download_url"] = enclosure.get("url")
                else:
                    torrent["download_url"] = torrent.get("link")

                results.append(torrent)

        except ET.ParseError as e:
            logger.error(f"Error parsing XML response: {e}")
            return []

        return results

    def _get_text(self, element) -> str:
        """Safely get text from XML element"""
        return element.text if element is not None else ""

    def filter_torrents(self, torrents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter torrents based on quality, size, and seeder requirements"""
        filtered = []

        for torrent in torrents:
            title = torrent.get("title", "")
            size = torrent.get("size", 0)
            seeders = torrent.get("seeders", 0)

            # Check seeders
            if seeders < self.min_seeders:
                logger.debug(f"Skipping '{title}' - insufficient seeders ({seeders})")
                continue

            # Check size limits
            if size < self.min_size_bytes or size > self.max_size_bytes:
                size_gb = size / (1024 * 1024 * 1024)
                logger.debug(f"Skipping '{title}' - size {size_gb:.1f}GB outside limits")
                continue

            # Check quality regex
            if not self.quality_regex.search(title):
                logger.debug(f"Skipping '{title}' - doesn't match quality regex")
                continue

            # Check exclude regex
            if self.exclude_regex.search(title):
                logger.debug(f"Skipping '{title}' - matches exclude regex")
                continue

            # Add calculated score for sorting
            torrent["score"] = self._calculate_score(torrent)
            filtered.append(torrent)

        # Sort by score (highest first)
        filtered.sort(key=lambda x: x["score"], reverse=True)

        logger.info(f"Filtered to {len(filtered)} quality torrents")
        return filtered

    def _calculate_score(self, torrent: dict[str, Any]) -> float:
        """Calculate quality score for torrent ranking"""
        score = 0.0
        title = torrent.get("title", "").lower()
        seeders = torrent.get("seeders", 0)
        size = torrent.get("size", 0)

        # Seeder score (logarithmic)
        score += min(seeders / 10.0, 10.0)

        # Quality preference scoring
        if "web-dl" in title:
            score += 10
        elif "bluray" in title or "blu-ray" in title:
            score += 8
        elif "webrip" in title:
            score += 6

        # Size preference (closer to 4GB is better)
        size_gb = size / (1024 * 1024 * 1024)
        size_diff = abs(size_gb - 4.0)
        score += max(0, 5 - size_diff)

        # Freeleech bonus
        if torrent.get("downloadvolumefactor", 1.0) == 0.0:
            score += 15

        return score

    async def get_best_torrent(self, title: str, year: int | None = None) -> dict[str, Any] | None:
        """Search and return the best quality torrent for a movie"""

        # Construct search query
        query = f"{title} {year}" if year else title

        # Search for torrents
        raw_results = await self.search_torrents(query)

        if not raw_results:
            return None

        # Filter based on quality requirements
        filtered_results = self.filter_torrents(raw_results)

        if not filtered_results:
            logger.warning(f"No torrents found matching quality criteria for '{query}'")
            return None

        # Return the best result
        best_torrent = filtered_results[0]
        logger.info(f"Selected torrent: {best_torrent['title']} (Score: {best_torrent['score']:.1f})")

        return best_torrent


# Global client instance
jackett_client = JackettClient()
