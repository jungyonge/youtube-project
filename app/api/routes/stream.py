"""SSE 실시간 상태 스트리밍."""
from __future__ import annotations

import asyncio
import json
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.config import settings
from app.db.models.user import User
from app.db.repositories.job_repo import JobRepository
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/videos", tags=["stream"])

HEARTBEAT_INTERVAL = 15  # seconds
CONNECTION_TIMEOUT = 1800  # 30 minutes


@router.get("/{job_id}/stream")
async def stream_job_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    # 소유자 확인
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    async def event_generator():
        r = aioredis.from_url(settings.REDIS_URL)
        pubsub = r.pubsub()
        channel = f"video_job:{job_id}"

        try:
            await pubsub.subscribe(channel)
            elapsed = 0

            while elapsed < CONNECTION_TIMEOUT:
                try:
                    msg = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=HEARTBEAT_INTERVAL,
                    )

                    if msg and msg["type"] == "message":
                        data = msg["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")

                        try:
                            event_data = json.loads(data)
                            event_type = event_data.get("type", "progress")
                            yield {
                                "event": event_type,
                                "data": json.dumps(event_data),
                            }

                            # completed/failed/cancelled → 스트림 종료
                            if event_type in ("completed", "failed", "cancelled"):
                                return

                        except json.JSONDecodeError:
                            yield {"event": "message", "data": data}

                except asyncio.TimeoutError:
                    # Heartbeat
                    yield {"event": "ping", "data": ""}
                    elapsed += HEARTBEAT_INTERVAL

        except Exception as e:
            logger.warning("SSE stream error for job={}: {}", job_id, e)
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()
            await r.aclose()

    return EventSourceResponse(event_generator())
