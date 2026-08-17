import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import correlation_id_var, request_id_var


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages X-Request-ID and X-Correlation-ID headers and sets contextvars
    so all structured JSON logs emitted during request processing carry correlation trace IDs.
    """

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
        corr_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or f"corr-{uuid.uuid4().hex[:12]}"
        )

        token_req = request_id_var.set(req_id)
        token_corr = correlation_id_var.set(corr_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            request_id_var.reset(token_req)
            correlation_id_var.reset(token_corr)
