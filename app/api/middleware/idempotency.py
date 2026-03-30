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
            cached = await r.get(redis_key)
            if cached:
                logger.info("Idempotency hit for key={}", idem_key)
                data = json.loads(cached)
                return JSONResponse(
                    content=data["body"],
                    status_code=data["status_code"],
                    headers={"X-Idempotency-Replay": "true"},
                )

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

            return response

        except Exception as e:
            logger.warning("Idempotency middleware error (passing through): {}", e)
            return await call_next(request)
