from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .blackhole import blackhole_client
from .config import settings
from .error_handlers import (
    general_exception_handler,
    http_exception_handler,
    seederbot_exception_handler,
    validation_exception_handler,
)
from .exceptions import SeederBotException
from .health import health_checker
from .logging_config import get_logger, setup_logging
from .middleware import RequestLoggingMiddleware
from .models import GrabRequest, GrabResponse, HealthResponse, SimpleHealthResponse
from .radarr import radarr_client

# Setup structured logging
setup_logging(level=settings.log_level, structured=settings.structured_logging)
logger = get_logger(__name__)

# Security
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.app_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(
        "Starting SeederBot",
        extra={
            'event': 'startup',
            'mode': settings.mode,
            'log_level': settings.log_level,
            'structured_logging': settings.structured_logging
        }
    )

    # Validate configuration
    config_valid = settings.validate_mode_config()
    if not config_valid:
        logger.error(
            "Invalid configuration detected",
            extra={
                'event': 'config_validation_failed',
                'mode': settings.mode,
                'radarr_configured': bool(settings.radarr_url and settings.radarr_api_key),
                'jackett_configured': bool(settings.jackett_url and settings.jackett_api_key)
            }
        )
    else:
        logger.info(
            "Configuration validated successfully",
            extra={'event': 'config_validation_success', 'mode': settings.mode}
        )

    yield

    # Shutdown
    logger.info("Shutting down SeederBot", extra={'event': 'shutdown'})


app = FastAPI(
    title="SeederBot",
    description="Secure FastAPI service for triggering media searches via ChatGPT webhook",
    version="0.1.0",
    lifespan=lifespan,
)

# Add exception handlers
app.add_exception_handler(SeederBotException, seederbot_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add middleware
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=SimpleHealthResponse)
async def health():
    """Simple health check endpoint for load balancers."""
    return SimpleHealthResponse(
        status="healthy",
        mode=settings.mode,
        version="0.1.0"
    )


@app.get("/health/detailed", response_model=HealthResponse)
async def detailed_health():
    """Comprehensive health check with component details."""
    return await health_checker.check_overall_health()


@app.post("/grab", response_model=GrabResponse)
async def grab_media(
    request: GrabRequest,
    token: str = Depends(verify_token)
):
    try:
        logger.info(f"Grab request: {request.title} ({request.type})")

        if settings.mode == "radarr":
            try:
                result = await radarr_client.grab_movie(request.title, request.year)
                return GrabResponse(
                    status="success",
                    message=f"Successfully added '{request.title}' to Radarr with auto-search",
                    details={
                        "mode": "radarr",
                        "title": request.title,
                        "year": request.year,
                        "movie_id": result["radarr_result"].get("id"),
                        "tmdb_id": result["movie"].get("tmdbId"),
                        "search_triggered": result["search_triggered"]
                    }
                )
            except ValueError as e:
                # Movie not found
                return GrabResponse(
                    status="error",
                    message=str(e),
                    details={"mode": "radarr", "title": request.title, "year": request.year}
                )
            except Exception as e:
                logger.error(f"Radarr error: {str(e)}")
                return GrabResponse(
                    status="error",
                    message="Failed to add movie to Radarr",
                    details={"mode": "radarr", "title": request.title, "error": str(e)}
                )

        elif settings.mode == "blackhole":
            try:
                result = await blackhole_client.grab_via_blackhole(request.title, request.year)
                return GrabResponse(
                    status="success",
                    message=f"Successfully downloaded torrent for '{request.title}' to blackhole",
                    details={
                        "mode": "blackhole",
                        "title": request.title,
                        "year": request.year,
                        "torrent_title": result["torrent"]["title"],
                        "filename": result["download"]["filename"],
                        "watch_dir": result["watch_dir"],
                        "seeders": result["torrent"].get("seeders"),
                        "size_gb": round(result["torrent"].get("size", 0) / (1024**3), 2)
                    }
                )
            except ValueError as e:
                # No suitable torrents found
                return GrabResponse(
                    status="error",
                    message=str(e),
                    details={"mode": "blackhole", "title": request.title, "year": request.year}
                )
            except Exception as e:
                logger.error(f"Blackhole error: {str(e)}")
                return GrabResponse(
                    status="error",
                    message="Failed to download torrent via blackhole",
                    details={"mode": "blackhole", "title": request.title, "error": str(e)}
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unknown mode: {settings.mode}"
            )

    except Exception as e:
        logger.error(f"Error processing grab request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        ) from e
