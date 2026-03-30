from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.api.routes import admin, auth, health, status, stream, video
from app.api.middleware.trace import TraceMiddleware
from app.api.middleware.rate_limit import RateLimitMiddleware
from app.api.middleware.idempotency import IdempotencyMiddleware
from app.storage.object_store import object_store
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    setup_logging()
    logger.info("Starting AI Video Generation Service")
    logger.info("Log level: {}", settings.LOG_LEVEL)

    # Ensure S3 buckets exist
    try:
        await object_store.ensure_bucket(settings.S3_ASSETS_BUCKET)
        await object_store.ensure_bucket(settings.S3_OUTPUTS_BUCKET)
        logger.info("S3 buckets verified")
    except Exception as e:
        logger.warning("S3 bucket init failed (non-fatal): {}", e)

    yield

    # Shutdown
    logger.info("Shutting down AI Video Generation Service")


app = FastAPI(
    title="AI Video Generation Service",
    description="AI 기반 유튜브 영상 자동 생성 서비스",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware (order matters: last added = first executed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TraceMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(IdempotencyMiddleware)

# Routes
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(video.router)
app.include_router(status.router)
app.include_router(stream.router)
app.include_router(admin.router)
