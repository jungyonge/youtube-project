"""Celery Beat 주기적 작업."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from celery.schedules import crontab
from loguru import logger
from sqlalchemy import select, update

from app.config import settings
from app.db.models.video_job import VideoJob
from app.db.session import async_session_factory
from app.storage.artifact_registry import artifact_registry
from app.workers.celery_app import celery_app

# Beat 스케줄 등록
celery_app.conf.beat_schedule = {
    "cleanup-expired-assets": {
        "task": "workers.cleanup_expired_assets",
        "schedule": crontab(minute=0),  # 매 시간
    },
    "cleanup-stale-jobs": {
        "task": "workers.cleanup_stale_jobs",
        "schedule": crontab(minute="*/30"),  # 매 30분
    },
}


@celery_app.task(name="workers.cleanup_expired_assets")
def cleanup_expired_assets_task() -> int:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup_expired())
    finally:
        loop.close()


async def _cleanup_expired() -> int:
    count = await artifact_registry.cleanup_expired(settings.OUTPUT_TTL_HOURS)
    if count:
        logger.info("Periodic cleanup: removed {} expired assets", count)
    return count


@celery_app.task(name="workers.cleanup_stale_jobs")
def cleanup_stale_jobs_task() -> int:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_cleanup_stale())
    finally:
        loop.close()


async def _cleanup_stale() -> int:
    now = datetime.utcnow()
    stale_cutoff = now - timedelta(hours=24)
    count = 0

    async with async_session_factory() as db:
        # 24시간 이상 running → failed
        result = await db.execute(
            select(VideoJob).where(
                VideoJob.phase == "running",
                VideoJob.updated_at < stale_cutoff,
            )
        )
        stale_running = list(result.scalars().all())

        for job in stale_running:
            await db.execute(
                update(VideoJob)
                .where(VideoJob.id == job.id)
                .values(
                    phase="failed",
                    current_step_detail="Timed out after 24 hours",
                    updated_at=now,
                )
            )
            count += 1

        # 24시간 이상 awaiting_approval → cancelled
        result = await db.execute(
            select(VideoJob).where(
                VideoJob.phase == "awaiting_approval",
                VideoJob.updated_at < stale_cutoff,
            )
        )
        stale_approval = list(result.scalars().all())

        for job in stale_approval:
            await db.execute(
                update(VideoJob)
                .where(VideoJob.id == job.id)
                .values(
                    phase="cancelled",
                    is_cancelled=True,
                    current_step_detail="Auto-cancelled: approval timeout (24h)",
                    updated_at=now,
                )
            )
            count += 1

        await db.commit()

    if count:
        logger.info("Periodic stale cleanup: processed {} jobs", count)
    return count
