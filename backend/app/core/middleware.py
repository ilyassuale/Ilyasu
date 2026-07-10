"""Custom middleware: rate limiting, audit logging, security headers."""
from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

redis_lib: Any = None
try:
    from redis import asyncio as aioredis

    redis_lib = aioredis
except ImportError:
    pass


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-IP rate limit backed by Redis, with an in-memory fallback for tests."""

    def __init__(self, app: Any, max_requests: int = 60, window: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self._redis: Any | None = None
        self._requests: dict[str, list[float]] = {}

    def _get_redis(self) -> Any | None:
        if self._redis is not None:
            return self._redis
        if redis_lib is None:
            return None
        try:
            self._redis = redis_lib.Redis.from_url(settings.redis_url, decode_responses=False)
        except Exception:
            self._redis = None
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        redis = self._get_redis()

        if redis:
            try:
                key = f"rate_limit:{client_ip}"
                async with redis.pipeline() as pipe:
                    await pipe.zremrangebyscore(key, 0, now - self.window)
                    await pipe.zadd(key, {str(now): now})
                    await pipe.zcard(key)
                    await pipe.expire(key, self.window)
                    _, _, count, _ = await pipe.execute()
                if count > self.max_requests:
                    return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
            except Exception:
                # Fallback to in-memory if Redis is unavailable
                pass

        timestamps = [t for t in self._requests.get(client_ip, []) if now - t < self.window]
        if len(timestamps) >= self.max_requests:
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
        timestamps.append(now)
        self._requests[client_ip] = timestamps
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
