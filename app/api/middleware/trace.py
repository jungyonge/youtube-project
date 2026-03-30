import uuid
from contextvars import ContextVar

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


class TraceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        tid = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        trace_id_var.set(tid)

        with logger.contextualize(trace_id=tid):
            logger.debug("{} {}", request.method, request.url.path)
            response = await call_next(request)
            response.headers["X-Trace-ID"] = tid
            return response
