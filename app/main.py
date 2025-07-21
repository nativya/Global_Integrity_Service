import logging
import redis.asyncio as redis
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from contextlib import asynccontextmanager

from .config import settings
from .models import UniquenessPayload, UniquenessResponse

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Redis Connection Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the application's lifespan events.
    Connects to Redis on startup and disconnects on shutdown.
    """
    try:
        app.state.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        await app.state.redis.ping()
        logger.info("Successfully connected to Redis.")
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to Redis: {e}")
        app.state.redis = None
    
    yield
    
    if app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed.")


# --- FastAPI App Initialization ---
app = FastAPI(
    title="Vana Global Integrity Service",
    description="Provides global uniqueness checks for chatbot data using Redis.",
    version="1.0.0",
    lifespan=lifespan
)

# --- API Key Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    """Dependency to validate the API key from the request header."""
    if api_key == settings.API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key"
        )

# --- API Endpoints ---
@app.get("/", summary="API Information")
async def root():
    """
    Root endpoint that provides basic information about the Global Integrity Service API.
    """
    return {
        "service": "Vana Global Integrity Service",
        "version": "1.0.0",
        "description": "Provides global uniqueness checks for chatbot data using Redis.",
        "endpoints": {
            "health": "/health",
            "validate_uniqueness": "/validate-global-uniqueness"
        },
        "documentation": "/docs"
    }

@app.get("/health", summary="Health Check")
async def health_check():
    """
    Simple health check endpoint to verify that the service is running
    and can connect to Redis.
    """
    if not app.state.redis:
        raise HTTPException(status_code=503, detail="Redis service is unavailable")
    return {"status": "ok", "redis_connected": True}


@app.post(
    "/validate-global-uniqueness",
    response_model=UniquenessResponse,
    summary="Validate Global Uniqueness of Fingerprints",
    dependencies=[Depends(get_api_key)]
)
async def validate_global_uniqueness(payload: UniquenessPayload):
    """
    Checks a list of fingerprints against the global Redis database to determine uniqueness.

    - **Receives**: A list of SimHash fingerprints.
    - **Checks**: How many already exist in the Redis set.
    - **Stores**: Any new, unique fingerprints into the Redis set.
    - **Returns**: A global uniqueness score and counts.
    """
    if not app.state.redis:
        raise HTTPException(status_code=503, detail="Redis service is unavailable")

    fingerprints_to_check = payload.fingerprints
    total_fingerprints = len(fingerprints_to_check)
    
    # Use SISMEMBER to check for existence of multiple items in a set.
    # This is more efficient than checking one by one.
    # The command returns a list of 1s and 0s.
    redis_key = "global_fingerprints"
    pipe = app.state.redis.pipeline()
    for fp in fingerprints_to_check:
        pipe.sismember(redis_key, fp)
    
    existence_results = await pipe.execute() # [True, False, True, ...]
    
    duplicates_count = sum(existence_results)
    new_fingerprints = [
        fp for fp, exists in zip(fingerprints_to_check, existence_results) if not exists
    ]
    
    # If there are new fingerprints, add them to the set using SADD
    if new_fingerprints:
        await app.state.redis.sadd(redis_key, *new_fingerprints)
        logger.info(f"Added {len(new_fingerprints)} new fingerprints to the global set.")

    global_uniqueness_score = len(new_fingerprints) / total_fingerprints if total_fingerprints > 0 else 0.0

    return UniquenessResponse(
        total_fingerprints_received=total_fingerprints,
        new_fingerprints_found=len(new_fingerprints),
        duplicate_fingerprints_found=duplicates_count,
        global_uniqueness_score=global_uniqueness_score
    )

