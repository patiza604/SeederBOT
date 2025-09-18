import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .models import GrabRequest, GrabResponse, HealthResponse
from .radarr import radarr_client
from .blackhole import blackhole_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    logger.info(f"Starting SeederBot in {settings.mode} mode")

    # Validate configuration
    if not settings.validate_mode_config():
        logger.error(f"Invalid configuration for mode: {settings.mode}")
        if settings.mode == "radarr":
            logger.error("Missing RADARR_URL or RADARR_API_KEY")
        elif settings.mode == "blackhole":
            logger.error("Missing JACKETT_URL or JACKETT_API_KEY")

    yield

    # Shutdown
    logger.info("Shutting down SeederBot")


app = FastAPI(
    title="SeederBot",
    description="Secure FastAPI service for triggering media searches via ChatGPT webhook",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        mode=settings.mode,
        version="0.1.0"
    )


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
