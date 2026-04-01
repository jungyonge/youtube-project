"""관리자 API — Job 목록, 강제 취소, 통계."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.models.cost_log import CostLog
from app.db.models.user import User
from app.db.models.video_job import VideoJob
from app.db.repositories.job_repo import JobRepository
from app.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/jobs")
async def list_all_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    user_id: uuid.UUID | None = None,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(VideoJob)

    if status_filter:
        stmt = stmt.where(VideoJob.phase == status_filter)
    if user_id:
        stmt = stmt.where(VideoJob.user_id == user_id)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Paginate
    offset = (page - 1) * per_page
    result = await db.execute(
        stmt.order_by(VideoJob.created_at.desc()).offset(offset).limit(per_page)
    )
    jobs = result.scalars().all()

    return {
        "items": [
            {
                "job_id": str(j.id),
                "user_id": str(j.user_id),
                "topic": j.topic,
                "phase": j.phase,
                "progress_percent": j.progress_percent,
                "total_cost_usd": j.total_cost_usd,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.post("/jobs/{job_id}/force-cancel")
async def force_cancel_job(
    job_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.phase in ("completed", "cancelled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job already {job.phase}")

    await repo.cancel(job_id)
    logger.info("Admin force-cancelled job={}", job_id)
    return {"job_id": str(job_id), "phase": "cancelled"}


@router.get("/stats")
async def get_stats(
    target_date: date | None = None,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    day_start = datetime(target_date.year, target_date.month, target_date.day)
    day_end = day_start + timedelta(days=1)

    # Job 통계
    day_filter = [VideoJob.created_at >= day_start, VideoJob.created_at < day_end]

    created = (await db.execute(
        select(func.count()).where(*day_filter)
    )).scalar_one()

    completed = (await db.execute(
        select(func.count()).where(*day_filter, VideoJob.phase == "completed")
    )).scalar_one()

    failed = (await db.execute(
        select(func.count()).where(*day_filter, VideoJob.phase == "failed")
    )).scalar_one()

    cancelled = (await db.execute(
        select(func.count()).where(*day_filter, VideoJob.phase == "cancelled")
    )).scalar_one()

    active = (await db.execute(
        select(func.count()).where(VideoJob.phase.in_(["queued", "running", "awaiting_approval"]))
    )).scalar_one()

    # 비용 통계
    cost_result = await db.execute(
        select(CostLog.provider, func.sum(CostLog.cost_usd))
        .where(CostLog.created_at >= day_start, CostLog.created_at < day_end)
        .group_by(CostLog.provider)
    )
    cost_by_provider = {row[0]: round(row[1], 4) for row in cost_result.all()}
    total_cost = sum(cost_by_provider.values())

    # 성능 통계
    perf_result = await db.execute(
        select(
            func.avg(VideoJob.generation_time_sec),
        ).where(*day_filter, VideoJob.phase == "completed")
    )
    avg_time = perf_result.scalar_one()

    failure_rate = (failed / created) if created > 0 else 0

    return {
        "date": target_date.isoformat(),
        "jobs": {
            "created": created,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "active": active,
        },
        "cost": {
            "total_usd": round(total_cost, 4),
            "by_provider": cost_by_provider,
        },
        "performance": {
            "avg_generation_time_sec": round(avg_time, 1) if avg_time else None,
            "failure_rate": round(failure_rate, 3),
        },
    }
