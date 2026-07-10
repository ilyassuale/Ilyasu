"""Admin dashboard routes."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker
from app.db.session import get_db
from app.models.models import AuditLog, Job, User

router = APIRouter(prefix="/admin", tags=["Admin"])

require_admin = RoleChecker(["admin"])


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at,
            }
            for u in users
        ]
    }


@router.put("/users/{user_id}/toggle")
async def toggle_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict[str, Any]:
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalar_one_or_none()
    if not target:
        return {"error": "User not found"}
    target.is_active = not target.is_active
    await db.commit()
    return {"id": target.id, "is_active": target.is_active}


@router.get("/analytics")
async def admin_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> dict[str, Any]:
    total_users = await db.execute(select(func.count(User.id)))
    by_role = await db.execute(select(User.role, func.count(User.id)).group_by(User.role))
    total_jobs = await db.execute(select(func.count(Job.id)))
    recent_audit = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20))
    users_by_role: dict[str, int] = {}
    for role, count in by_role.all():
        users_by_role[role] = count
    return {
        "total_users": total_users.scalar(),
        "users_by_role": users_by_role,
        "total_jobs": total_jobs.scalar(),
        "recent_audit": [
            {
                "action": a.action,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "created_at": a.created_at,
            }
            for a in recent_audit.scalars().all()
        ],
    }
