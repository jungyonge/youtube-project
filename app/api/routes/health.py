from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from loguru import logger
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.storage.object_store import object_store

router = APIRouter(tags=["system"])


async def _check_db(db: AsyncSession) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        logger.error("DB health check failed: {}", e)
        return {"status": "unhealthy", "error": str(e)}


async def _check_redis() -> dict:
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        return {"status": "healthy"}
    except Exception as e:
        logger.error("Redis health check failed: {}", e)
        return {"status": "unhealthy", "error": str(e)}


async def _check_minio() -> dict:
    try:
        await object_store.ensure_bucket(settings.S3_ASSETS_BUCKET)
        return {"status": "healthy"}
    except Exception as e:
        logger.error("MinIO health check failed: {}", e)
        return {"status": "unhealthy", "error": str(e)}


async def _check_api_keys() -> dict:
    issues = []
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key":
        issues.append("GEMINI_API_KEY not configured")
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key":
        issues.append("OPENAI_API_KEY not configured")
    if issues:
        return {"status": "warning", "issues": issues}
    return {"status": "healthy"}


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    db_status = await _check_db(db)
    redis_status = await _check_redis()
    minio_status = await _check_minio()
    api_keys_status = await _check_api_keys()

    components = {
        "database": db_status,
        "redis": redis_status,
        "minio": minio_status,
        "api_keys": api_keys_status,
    }

    overall = "healthy"
    for comp in components.values():
        if comp["status"] == "unhealthy":
            overall = "unhealthy"
            break

    return {"status": overall, "components": components}


@router.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )
