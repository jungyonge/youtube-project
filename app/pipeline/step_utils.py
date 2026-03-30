"""파이프라인 Step 공통 유틸리티: step 실행 기록, 진행률 발행.

Celery Worker 전용 — 모든 함수는 동기(sync)로 구현.
절대로 AsyncSession을 사용하지 않는다.
"""
from __future__ import annotations

import json
import traceback
import uuid
from datetime import datetime, timezone

import redis as sync_redis
from loguru import logger
from sqlalchemy import select, update

from app.config import settings
from app.db.models.job_step import JobStepExecution
from app.db.models.video_job import VideoJob
from app.db.sync_session import SyncSessionLocal
from app.utils.metrics import active_celery_tasks, video_jobs_total


def begin_step(job_id: str, step_name: str) -> uuid.UUID:
    """Step 시작 기록."""
    with SyncSessionLocal() as db:
        step = JobStepExecution(
            job_id=uuid.UUID(job_id),
            step_name=step_name,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        active_celery_tasks.inc()
        logger.info("Step started: job={} step={}", job_id, step_name)
        return step.id


def complete_step(
    step_id: str | uuid.UUID,
    job_id: str,
    step_name: str,
    progress_percent: int,
    artifact_keys: list[str] | None = None,
    cost_usd: float = 0.0,
    metadata: dict | None = None,
) -> None:
    """Step 완료 기록 + 진행률 업데이트."""
    now = datetime.now(timezone.utc)
    with SyncSessionLocal() as db:
        step_uuid = uuid.UUID(step_id) if isinstance(step_id, str) else step_id
        db.execute(
            update(JobStepExecution)
            .where(JobStepExecution.id == step_uuid)
            .values(
                status="completed",
                completed_at=now,
                output_artifact_keys=artifact_keys or [],
                cost_usd=cost_usd,
                metadata_json=metadata,
            )
        )
        db.execute(
            update(VideoJob)
            .where(VideoJob.id == uuid.UUID(job_id))
            .values(
                progress_percent=progress_percent,
                last_completed_step=step_name,
                current_step_detail=f"{step_name} completed",
                updated_at=now,
            )
        )
        db.commit()
    active_celery_tasks.dec()
    video_jobs_total.labels(status="running").inc(0)  # ensure label exists
    logger.info("Step completed: job={} step={} progress={}%", job_id, step_name, progress_percent)
    publish_progress(job_id, progress_percent, f"{step_name} completed")


def fail_step(
    step_id: str | uuid.UUID,
    job_id: str,
    step_name: str,
    error: Exception,
) -> None:
    """Step 실패 기록."""
    now = datetime.now(timezone.utc)
    tb = traceback.format_exception(type(error), error, error.__traceback__)
    with SyncSessionLocal() as db:
        step_uuid = uuid.UUID(step_id) if isinstance(step_id, str) else step_id
        db.execute(
            update(JobStepExecution)
            .where(JobStepExecution.id == step_uuid)
            .values(
                status="failed",
                completed_at=now,
                error_message=str(error),
                error_traceback="".join(tb),
            )
        )
        db.execute(
            update(VideoJob)
            .where(VideoJob.id == uuid.UUID(job_id))
            .values(
                phase="failed",
                current_step_detail=f"{step_name} failed: {error}",
                updated_at=now,
            )
        )
        db.commit()
    active_celery_tasks.dec()
    video_jobs_total.labels(status="failed").inc()
    logger.error("Step failed: job={} step={} error={}", job_id, step_name, error)


def check_cancelled(job_id: str) -> bool:
    """Job 취소 여부 확인."""
    with SyncSessionLocal() as db:
        result = db.execute(
            select(VideoJob.is_cancelled).where(VideoJob.id == uuid.UUID(job_id))
        )
        cancelled = result.scalar_one_or_none()
        return bool(cancelled)


def publish_progress(job_id: str, progress_percent: int, detail: str) -> None:
    """Redis PUBLISH로 SSE 진행 상태 전송."""
    try:
        r = sync_redis.from_url(settings.REDIS_URL)
        event = json.dumps({
            "type": "progress",
            "job_id": job_id,
            "progress_percent": progress_percent,
            "current_step_detail": detail,
        })
        r.publish(f"video_job:{job_id}", event)
        r.close()
    except Exception as e:
        logger.warning("Failed to publish progress: {}", e)
