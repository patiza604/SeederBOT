import logging
import os
import hashlib
from pathlib import Path
from typing import Any
import httpx
from .config import settings

logger = logging.getLogger(__name__)


class BlackholeClient:
    def __init__(self):
        self.watch_dir = Path(settings.autoadd_watch_dir)

    async def download_torrent(self, torrent_data: dict[str, Any]) -> dict[str, Any]:
        """Download torrent file and save to blackhole directory"""

        download_url = torrent_data.get("download_url")
        title = torrent_data.get("title", "unknown")

        if not download_url:
            raise ValueError("No download URL found in torrent data")

        # Create watch directory if it doesn't exist
        self.watch_dir.mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        filename = self._generate_filename(title)
        file_path = self.watch_dir / filename

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Download the torrent file
                response = await client.get(download_url)
                response.raise_for_status()

                # Verify it's actually a torrent file
                content = response.content
                if not self._is_valid_torrent(content):
                    raise ValueError("Downloaded file is not a valid torrent")

                # Write to blackhole directory
                with open(file_path, "wb") as f:
                    f.write(content)

                logger.info(f"Downloaded torrent: {filename}")

                return {
                    "filename": filename,
                    "path": str(file_path),
                    "size": len(content),
                    "torrent_data": torrent_data
                }

            except httpx.HTTPError as e:
                logger.error(f"Error downloading torrent: {e}")
                raise

            except IOError as e:
                logger.error(f"Error writing torrent file: {e}")
                raise

    def _generate_filename(self, title: str) -> str:
        """Generate a safe filename for the torrent file"""
        # Remove/replace unsafe characters
        safe_title = "".join(c for c in title if c.isalnum() or c in " .-_")
        safe_title = safe_title.strip()

        # Truncate if too long
        if len(safe_title) > 200:
            safe_title = safe_title[:200]

        # Add timestamp hash to avoid duplicates
        title_hash = hashlib.md5(title.encode()).hexdigest()[:8]

        filename = f"{safe_title}_{title_hash}.torrent"
        return filename

    def _is_valid_torrent(self, content: bytes) -> bool:
        """Basic validation that content is a torrent file"""
        try:
            # Torrent files start with 'd' (dictionary) in bencode format
            if not content.startswith(b'd'):
                return False

            # Look for common torrent file markers
            content_str = content.decode('latin-1', errors='ignore')
            return 'announce' in content_str and 'info' in content_str

        except Exception:
            return False

    def get_watch_dir_status(self) -> dict[str, Any]:
        """Get status information about the watch directory"""
        try:
            if not self.watch_dir.exists():
                return {
                    "exists": False,
                    "path": str(self.watch_dir),
                    "writable": False,
                    "torrent_count": 0
                }

            # Count .torrent files
            torrent_files = list(self.watch_dir.glob("*.torrent"))

            # Check if directory is writable
            writable = os.access(self.watch_dir, os.W_OK)

            return {
                "exists": True,
                "path": str(self.watch_dir),
                "writable": writable,
                "torrent_count": len(torrent_files),
                "torrent_files": [f.name for f in torrent_files[-5:]]  # Last 5 files
            }

        except Exception as e:
            logger.error(f"Error checking watch directory: {e}")
            return {
                "exists": False,
                "path": str(self.watch_dir),
                "writable": False,
                "torrent_count": 0,
                "error": str(e)
            }

    async def grab_via_blackhole(self, title: str, year: int | None = None) -> dict[str, Any]:
        """High-level method: search via Jackett and download to blackhole"""
        from .jackett import jackett_client

        # Search for the best torrent
        best_torrent = await jackett_client.get_best_torrent(title, year)

        if not best_torrent:
            raise ValueError(f"No suitable torrents found for '{title}'")

        # Download the torrent file
        download_result = await self.download_torrent(best_torrent)

        return {
            "method": "blackhole",
            "title": title,
            "year": year,
            "torrent": best_torrent,
            "download": download_result,
            "watch_dir": str(self.watch_dir)
        }


# Global client instance
blackhole_client = BlackholeClient()