import json

import redis.asyncio as aioredis
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings

IDEMPOTENCY_TTL = 86400  # 24 hours


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL)
        return self._redis

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only check POST requests with Idempotency-Key header
        if request.method != "POST":
            return await call_next(request)

        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key:
            return await call_next(request)

        redis_key = f"idempotency:{idem_key}"

        try:
            r = await self._get_redis()

            # SET NX로 race condition 방지:
            # 동시에 같은 key로 2개 요청이 들어와도 1개만 처리
            acquired = await r.set(
                redis_key,
                json.dumps({"status": "processing"}),
                ex=IDEMPOTENCY_TTL,
                nx=True,
            )

            if not acquired:
                # 이미 존재하는 key — 캐시된 응답 또는 처리 중
                cached = await r.get(redis_key)
                if cached:
                    data = json.loads(cached)
                    if data.get("status") == "processing":
                        # 다른 요청이 아직 처리 중
                        return JSONResponse(
                            content={"detail": "Request is being processed", "idempotency_key": idem_key},
                            status_code=202,
                            headers={"X-Idempotency-Processing": "true"},
                        )
                    logger.info("Idempotency hit for key={}", idem_key)
                    return JSONResponse(
                        content=data["body"],
                        status_code=data["status_code"],
                        headers={"X-Idempotency-Replay": "true"},
                    )

            # SET NX 성공 — 이 요청이 처리 담당
            response = await call_next(request)

            # Cache successful responses
            if 200 <= response.status_code < 300:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk if isinstance(chunk, bytes) else chunk.encode()
                cache_data = {
                    "status_code": response.status_code,
                    "body": json.loads(body),
                }
                await r.set(redis_key, json.dumps(cache_data), ex=IDEMPOTENCY_TTL)
                return JSONResponse(
                    content=cache_data["body"],
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )

            # 실패 시 key 삭제하여 재시도 허용
            await r.delete(redis_key)
            return response

        except Exception as e:
            logger.warning("Idempotency middleware error (passing through): {}", e)
            return await call_next(request)
