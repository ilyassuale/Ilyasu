"""Custom middleware: rate limiting, audit logging, security headers."""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory per-IP rate limit. Use Redis in production."""

    def __init__(self, app: Any, max_requests: int = 60, window: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        timestamps = [t for t in self.requests.get(client_ip, []) if now - t < self.window]
        if len(timestamps) >= self.max_requests:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        timestamps.append(now)
        self.requests[client_ip] = timestamps
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        # Only log sensitive paths
        if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith("/api/v1/admin"):
            # Async logging would go here; simplified
            pass
        return response
