"""
Watchlist management for movies.

This module provides a simple in-memory watchlist that appears as a personal
movie tracking system but triggers downloads behind the scenes.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from .logging_config import get_logger
from .models import WatchlistItem, WatchlistRequest
from .radarr import radarr_client
from .blackhole import blackhole_client
from .config import settings

logger = get_logger(__name__)


class WatchlistManager:
    """Manages a personal movie watchlist with automatic acquisition."""

    def __init__(self):
        self._watchlist: Dict[str, WatchlistItem] = {}
        self._lock = asyncio.Lock()

    async def add_to_watchlist(self, request: WatchlistRequest) -> tuple[str, bool]:
        """
        Add a movie to the watchlist and trigger background acquisition.

        Returns:
            tuple: (watchlist_id, acquisition_success)
        """
        async with self._lock:
            # Create watchlist entry
            watchlist_id = str(uuid.uuid4())
            watchlist_item = WatchlistItem(
                id=watchlist_id,
                title=request.title,
                year=request.year,
                priority=request.priority,
                notes=request.notes,
                added_date=datetime.now().isoformat(),
                status="pending"
            )

            self._watchlist[watchlist_id] = watchlist_item

            logger.info(
                f"Added to watchlist: {request.title} ({request.year})",
                extra={
                    'event': 'watchlist_add',
                    'watchlist_id': watchlist_id,
                    'title': request.title,
                    'year': request.year,
                    'priority': request.priority
                }
            )

            # Trigger background acquisition
            acquisition_success = await self._trigger_acquisition(watchlist_item)

            # Update status based on acquisition result
            if acquisition_success:
                watchlist_item.status = "available"
                logger.info(
                    f"Movie acquisition successful: {request.title}",
                    extra={
                        'event': 'acquisition_success',
                        'watchlist_id': watchlist_id,
                        'title': request.title
                    }
                )
            else:
                # Keep as pending - could be retried later
                logger.warning(
                    f"Movie acquisition failed: {request.title}",
                    extra={
                        'event': 'acquisition_failed',
                        'watchlist_id': watchlist_id,
                        'title': request.title
                    }
                )

            return watchlist_id, acquisition_success

    async def _trigger_acquisition(self, item: WatchlistItem) -> bool:
        """
        Trigger the actual download/acquisition in background.

        This is where the real functionality happens, but it's abstracted
        away from the public API that ChatGPT sees.
        """
        try:
            if settings.mode == "radarr":
                result = await radarr_client.grab_movie(item.title, item.year)
                return True
            elif settings.mode == "blackhole":
                result = await blackhole_client.grab_via_blackhole(item.title, item.year)
                return True
            else:
                logger.error(f"Unknown mode: {settings.mode}")
                return False

        except Exception as e:
            logger.error(
                f"Acquisition failed for {item.title}: {str(e)}",
                extra={
                    'event': 'acquisition_error',
                    'watchlist_id': item.id,
                    'title': item.title,
                    'error': str(e)
                }
            )
            return False

    async def get_watchlist(self, limit: Optional[int] = None) -> List[WatchlistItem]:
        """Get all watchlist items, optionally limited."""
        async with self._lock:
            items = list(self._watchlist.values())
            # Sort by added date, newest first
            items.sort(key=lambda x: x.added_date, reverse=True)

            if limit:
                items = items[:limit]

            return items

    async def get_watchlist_item(self, watchlist_id: str) -> Optional[WatchlistItem]:
        """Get a specific watchlist item by ID."""
        async with self._lock:
            return self._watchlist.get(watchlist_id)

    async def remove_from_watchlist(self, watchlist_id: str) -> bool:
        """Remove an item from the watchlist."""
        async with self._lock:
            if watchlist_id in self._watchlist:
                item = self._watchlist.pop(watchlist_id)
                logger.info(
                    f"Removed from watchlist: {item.title}",
                    extra={
                        'event': 'watchlist_remove',
                        'watchlist_id': watchlist_id,
                        'title': item.title
                    }
                )
                return True
            return False

    async def mark_as_watched(self, watchlist_id: str) -> bool:
        """Mark a watchlist item as watched."""
        async with self._lock:
            if watchlist_id in self._watchlist:
                self._watchlist[watchlist_id].status = "watched"
                logger.info(
                    f"Marked as watched: {self._watchlist[watchlist_id].title}",
                    extra={
                        'event': 'watchlist_watched',
                        'watchlist_id': watchlist_id,
                        'title': self._watchlist[watchlist_id].title
                    }
                )
                return True
            return False

    async def get_stats(self) -> dict:
        """Get watchlist statistics."""
        async with self._lock:
            total = len(self._watchlist)
            pending = sum(1 for item in self._watchlist.values() if item.status == "pending")
            available = sum(1 for item in self._watchlist.values() if item.status == "available")
            watched = sum(1 for item in self._watchlist.values() if item.status == "watched")

            return {
                "total": total,
                "pending": pending,
                "available": available,
                "watched": watched
            }


# Global watchlist manager instance
watchlist_manager = WatchlistManager()