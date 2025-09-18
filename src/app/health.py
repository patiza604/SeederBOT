import asyncio
import time
from typing import Any

import httpx

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)


class HealthChecker:
    """Comprehensive health checking for all system components."""

    def __init__(self):
        self.timeout = 5.0

    async def check_overall_health(self) -> dict[str, Any]:
        """Perform comprehensive health check of all components."""
        start_time = time.time()

        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "0.1.0",
            "mode": settings.mode,
            "uptime_seconds": time.time() - start_time,
            "checks": {}
        }

        # Run all health checks concurrently
        checks = [
            ("config", self._check_configuration()),
            ("radarr", self._check_radarr()) if settings.mode == "radarr" else ("radarr", self._skip_check("Not in radarr mode")),
            ("jackett", self._check_jackett()) if settings.jackett_url else ("jackett", self._skip_check("Jackett not configured")),
            ("filesystem", self._check_filesystem()) if settings.mode == "blackhole" else ("filesystem", self._skip_check("Not in blackhole mode")),
        ]

        # Execute checks
        results = await asyncio.gather(*[check[1] for check in checks], return_exceptions=True)

        # Process results
        for i, (check_name, _) in enumerate(checks):
            result = results[i]
            if isinstance(result, Exception):
                health_status["checks"][check_name] = {
                    "status": "error",
                    "error": str(result),
                    "duration_ms": 0
                }
                health_status["status"] = "unhealthy"
            else:
                health_status["checks"][check_name] = result
                if result["status"] != "healthy":
                    health_status["status"] = "degraded" if health_status["status"] == "healthy" else "unhealthy"

        health_status["duration_ms"] = round((time.time() - start_time) * 1000, 2)

        # Log health check result
        logger.info(
            "Health check completed",
            extra={
                'event': 'health_check',
                'overall_status': health_status["status"],
                'duration_ms': health_status["duration_ms"],
                'checks_count': len(health_status["checks"])
            }
        )

        return health_status

    async def _check_configuration(self) -> dict[str, Any]:
        """Check application configuration."""
        start_time = time.time()

        try:
            config_issues = []

            # Check required configuration based on mode
            if settings.mode == "radarr":
                if not settings.radarr_url:
                    config_issues.append("RADARR_URL not configured")
                if not settings.radarr_api_key:
                    config_issues.append("RADARR_API_KEY not configured")
            elif settings.mode == "blackhole":
                if not settings.jackett_url:
                    config_issues.append("JACKETT_URL not configured")
                if not settings.jackett_api_key:
                    config_issues.append("JACKETT_API_KEY not configured")
                if not settings.autoadd_watch_dir:
                    config_issues.append("AUTOADD_WATCH_DIR not configured")

            # Check app token
            if not settings.app_token or len(settings.app_token) < 32:
                config_issues.append("APP_TOKEN too weak (should be 32+ characters)")

            status = "healthy" if not config_issues else "unhealthy"

            return {
                "status": status,
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "details": {
                    "mode": settings.mode,
                    "issues": config_issues,
                    "radarr_configured": bool(settings.radarr_url and settings.radarr_api_key),
                    "jackett_configured": bool(settings.jackett_url and settings.jackett_api_key),
                }
            }

        except Exception as e:
            logger.error(f"Configuration health check failed: {e}", exc_info=True)
            return {
                "status": "error",
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }

    async def _check_radarr(self) -> dict[str, Any]:
        """Check Radarr connectivity and status."""
        if not settings.radarr_url or not settings.radarr_api_key:
            return self._skip_check("Radarr not configured")

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{settings.radarr_url}/api/v3/system/status",
                    headers={"X-Api-Key": settings.radarr_api_key}
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "healthy",
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "details": {
                            "version": data.get("version"),
                            "startup_path": data.get("startupPath"),
                            "is_debug": data.get("isDebug", False),
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }

        except Exception as e:
            logger.error(f"Radarr health check failed: {e}")
            return {
                "status": "unhealthy",
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }

    async def _check_jackett(self) -> dict[str, Any]:
        """Check Jackett connectivity and indexers."""
        if not settings.jackett_url or not settings.jackett_api_key:
            return self._skip_check("Jackett not configured")

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check server status
                response = await client.get(
                    f"{settings.jackett_url}/api/v2.0/server/config",
                    params={"apikey": settings.jackett_api_key}
                )

                if response.status_code == 200:
                    # Check indexers
                    indexers_response = await client.get(
                        f"{settings.jackett_url}/api/v2.0/indexers",
                        params={"apikey": settings.jackett_api_key}
                    )

                    indexers_data = indexers_response.json() if indexers_response.status_code == 200 else []
                    active_indexers = [idx for idx in indexers_data if idx.get("configured", False)]

                    return {
                        "status": "healthy" if active_indexers else "degraded",
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "details": {
                            "total_indexers": len(indexers_data),
                            "active_indexers": len(active_indexers),
                            "indexer_names": [idx.get("name") for idx in active_indexers[:5]]  # First 5
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "duration_ms": round((time.time() - start_time) * 1000, 2),
                        "error": f"HTTP {response.status_code}: {response.text}"
                    }

        except Exception as e:
            logger.error(f"Jackett health check failed: {e}")
            return {
                "status": "unhealthy",
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }

    async def _check_filesystem(self) -> dict[str, Any]:
        """Check filesystem access for blackhole mode."""
        if settings.mode != "blackhole":
            return self._skip_check("Not in blackhole mode")

        start_time = time.time()

        try:
            import os
            import tempfile

            watch_dir = settings.autoadd_watch_dir

            # Check if watch directory exists and is writable
            if not os.path.exists(watch_dir):
                return {
                    "status": "unhealthy",
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "error": f"Watch directory does not exist: {watch_dir}"
                }

            if not os.access(watch_dir, os.W_OK):
                return {
                    "status": "unhealthy",
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "error": f"Watch directory is not writable: {watch_dir}"
                }

            # Test write access
            try:
                with tempfile.NamedTemporaryFile(dir=watch_dir, delete=True):
                    pass
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "error": f"Cannot write to watch directory: {e}"
                }

            return {
                "status": "healthy",
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "details": {
                    "watch_dir": watch_dir,
                    "writable": True,
                    "exists": True
                }
            }

        except Exception as e:
            logger.error(f"Filesystem health check failed: {e}")
            return {
                "status": "error",
                "duration_ms": round((time.time() - start_time) * 1000, 2),
                "error": str(e)
            }

    def _skip_check(self, reason: str) -> dict[str, Any]:
        """Return a skipped check result."""
        return {
            "status": "skipped",
            "duration_ms": 0,
            "reason": reason
        }


# Global health checker instance
health_checker = HealthChecker()
