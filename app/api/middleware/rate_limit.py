import time

import redis.asyncio as aioredis
from fastapi import HTTPException, Request, status
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import settings

RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 60  # per window


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.REDIS_URL)
        return self._redis

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only rate-limit API mutation endpoints
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Identify client by Authorization header user or IP
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            client_id = f"auth:{auth_header[7:20]}"
        else:
            client_id = f"ip:{request.client.host if request.client else 'unknown'}"

        try:
            r = await self._get_redis()
            key = f"ratelimit:{client_id}"
            now = time.time()

            pipe = r.pipeline()
            pipe.zremrangebyscore(key, 0, now - RATE_LIMIT_WINDOW)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, RATE_LIMIT_WINDOW)
            results = await pipe.execute()

            request_count = results[2]
            if request_count > RATE_LIMIT_MAX_REQUESTS:
                logger.warning("Rate limit exceeded for {}", client_id)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Rate limit check failed (allowing request): {}", e)

        return await call_next(request)
