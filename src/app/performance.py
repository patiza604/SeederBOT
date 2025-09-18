"""Performance optimization utilities and decorators."""

import asyncio
import functools
import time
from collections.abc import Callable
from typing import Any

from .logging_config import get_logger

logger = get_logger(__name__)


def async_timed(func: Callable) -> Callable:
    """Decorator to measure and log async function execution time."""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            logger.info(
                f"Function {func.__name__} completed",
                extra={
                    'event': 'function_timing',
                    'function': func.__name__,
                    'duration_ms': duration_ms,
                    'status': 'success'
                }
            )
            return result

        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    'event': 'function_timing',
                    'function': func.__name__,
                    'duration_ms': duration_ms,
                    'status': 'error',
                    'error': str(e)
                }
            )
            raise

    return wrapper


class ConnectionPool:
    """Simple async HTTP connection pool manager."""

    def __init__(self, max_connections: int = 10, timeout: float = 30.0):
        self.max_connections = max_connections
        self.timeout = timeout
        self._semaphore = asyncio.Semaphore(max_connections)

    async def __aenter__(self):
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()


class AsyncCache:
    """Simple in-memory async cache with TTL."""

    def __init__(self, default_ttl: float = 300.0):  # 5 minutes default
        self._cache: dict[str, dict[str, Any]] = {}
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        """Get a value from cache."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry['expires']:
            del self._cache[key]
            return None

        logger.debug(
            "Cache hit",
            extra={'event': 'cache_hit', 'key': key}
        )
        return entry['value']

    async def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Set a value in cache."""
        ttl = ttl or self.default_ttl
        self._cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }

        logger.debug(
            "Cache set",
            extra={'event': 'cache_set', 'key': key, 'ttl': ttl}
        )

    async def delete(self, key: str) -> None:
        """Delete a value from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(
                "Cache delete",
                extra={'event': 'cache_delete', 'key': key}
            )

    async def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared", extra={'event': 'cache_clear'})

    async def cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires']
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(
                "Cache cleanup completed",
                extra={'event': 'cache_cleanup', 'expired_count': len(expired_keys)}
            )


# Global instances
connection_pool = ConnectionPool()
cache = AsyncCache()


async def with_retry(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """Retry an async function with exponential backoff."""

    last_exception = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info(
                    f"Retrying {func.__name__} (attempt {attempt + 1}/{max_retries + 1})",
                    extra={
                        'event': 'retry_attempt',
                        'function': func.__name__,
                        'attempt': attempt + 1,
                        'max_attempts': max_retries + 1
                    }
                )

            return await func()

        except exceptions as e:
            last_exception = e

            if attempt < max_retries:
                logger.warning(
                    f"Function {func.__name__} failed, retrying in {current_delay}s",
                    extra={
                        'event': 'retry_delay',
                        'function': func.__name__,
                        'attempt': attempt + 1,
                        'delay': current_delay,
                        'error': str(e)
                    }
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(
                    f"Function {func.__name__} failed after {max_retries + 1} attempts",
                    extra={
                        'event': 'retry_exhausted',
                        'function': func.__name__,
                        'attempts': max_retries + 1,
                        'final_error': str(e)
                    }
                )

    raise last_exception


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, rate: float, burst: int):
        self.rate = rate  # tokens per second
        self.burst = burst  # max tokens
        self.tokens = burst
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        """Acquire a token, returns True if successful."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            self.last_update = now

            # Add tokens based on elapsed time
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False


# Global rate limiter for external API calls
api_rate_limiter = RateLimiter(rate=2.0, burst=5)  # 2 requests per second, burst of 5
