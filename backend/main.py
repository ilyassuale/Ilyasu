"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.interview import router as interview_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.recruiter import router as recruiter_router
from app.api.v1.resume import router as resume_router
from app.core.config import settings
from app.core.middleware import AuditLogMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from app.db.session import Base, engine

logging.basicConfig(level=logging.getLevelName(settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Application startup complete.")
    yield
    await engine.dispose()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.frontend_url)] if settings.frontend_url else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not settings.debug:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

app.add_middleware(RateLimitMiddleware, max_requests=settings.rate_limit_per_minute)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLogMiddleware)


# API v1
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(resume_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(recruiter_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
