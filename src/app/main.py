import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings
from .models import GrabRequest, GrabResponse, HealthResponse

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
            # TODO: Implement Radarr path in Stage 2
            return GrabResponse(
                status="error",
                message="Radarr mode not yet implemented",
                details={"mode": "radarr", "title": request.title}
            )

        elif settings.mode == "blackhole":
            # TODO: Implement blackhole path in Stage 3
            return GrabResponse(
                status="error",
                message="Blackhole mode not yet implemented",
                details={"mode": "blackhole", "title": request.title}
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
