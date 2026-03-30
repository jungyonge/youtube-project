"""SSE 실시간 상태 스트리밍."""
from __future__ import annotations

import asyncio
import json
import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from loguru import logger
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import decode_access_token
from app.config import settings
from app.db.models.user import User
from app.db.repositories.job_repo import JobRepository
from app.db.repositories.user_repo import UserRepository
from app.db.session import get_db

router = APIRouter(prefix="/api/v1/videos", tags=["stream"])

HEARTBEAT_INTERVAL = 15  # seconds
CONNECTION_TIMEOUT = 1800  # 30 minutes


async def _get_user_from_request(
    request: Request,
    token: str | None,
    db: AsyncSession,
) -> User:
    """
    SSE 토큰 처리: EventSource API는 커스텀 헤더를 지원하지 않으므로,
    Authorization 헤더와 query parameter 모두에서 JWT를 추출한다.

    1. Authorization 헤더에서 토큰 추출 시도
    2. 없으면 query parameter 'token'에서 추출
    3. 둘 다 없으면 401 반환
    """
    jwt_token = None

    # 1. Authorization 헤더
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        jwt_token = auth_header.removeprefix("Bearer ")

    # 2. Query parameter fallback
    if not jwt_token and token:
        jwt_token = token

    if not jwt_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token required (header or query parameter)",
        )

    try:
        payload = decode_access_token(jwt_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(uuid.UUID(user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.get("/{job_id}/stream")
async def stream_job_status(
    job_id: uuid.UUID,
    request: Request,
    token: str | None = Query(default=None, description="JWT token (EventSource fallback)"),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    # SSE는 커스텀 헤더 미지원 → header + query param 모두 지원
    current_user = await _get_user_from_request(request, token, db)

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
