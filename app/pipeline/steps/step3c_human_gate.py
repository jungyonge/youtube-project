"""Step 3c: Human Approval 게이트 — 민감 주제는 승인 대기."""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select, update

import redis.asyncio as aioredis

from app.config import settings
from app.db.models.video_job import VideoJob
from app.db.sync_session import SyncSessionLocal
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step, publish_progress
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app


def _run_async(coro):
    """Run an async coroutine from sync Celery task context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


@celery_app.task(name="pipeline.human_gate", bind=True, max_retries=0)
def human_gate_task(self, job_id: str) -> str:
    step_name = "human_gate"
    step_id = begin_step(job_id, step_name)

    try:
        if check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # Job + Script 로드
        with SyncSessionLocal() as db:
            result = db.execute(
                select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
            )
            job = result.scalar_one()

        script_key = f"{job_id}/script.json"
        script_bytes = _run_async(object_store.download(settings.S3_ASSETS_BUCKET, script_key))
        script = FullScript.model_validate(json.loads(script_bytes.decode("utf-8")))

        # 승인 필요 여부 판단
        needs_approval = script.overall_sensitivity == "high" or script.requires_human_approval

        if not needs_approval:
            logger.info("Auto-approved (no sensitive content): job={}", job_id)
            complete_step(
                step_id, job_id, step_name,
                progress_percent=55,
                metadata={"auto_approved": True, "sensitivity": script.overall_sensitivity},
            )
            return job_id

        # 승인 대기 모드
        script_url = _run_async(object_store.presigned_url(
            settings.S3_ASSETS_BUCKET, script_key, expires_in=86400
        ))

        with SyncSessionLocal() as db:
            db.execute(
                update(VideoJob)
                .where(VideoJob.id == uuid.UUID(job_id))
                .values(
                    phase="awaiting_approval",
                    requires_human_approval=True,
                    current_step_detail="대본 승인 대기 중",
                    progress_percent=55,
                    updated_at=datetime.utcnow(),
                )
            )
            db.commit()

        # SSE 이벤트: approval_required
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            event = json.dumps({
                "type": "approval_required",
                "job_id": job_id,
                "script_preview_url": script_url,
                "sensitivity_level": script.overall_sensitivity,
            })
            _run_async(r.publish(f"video_job:{job_id}", event))
            _run_async(r.aclose())
        except Exception as e:
            logger.warning("Failed to publish approval_required event: {}", e)

        # Step 완료 (파이프라인은 여기서 멈춤)
        complete_step(
            step_id, job_id, step_name,
            progress_percent=55,
            metadata={
                "awaiting_approval": True,
                "sensitivity": script.overall_sensitivity,
            },
        )

        logger.info(
            "Human approval required: job={} sensitivity={}",
            job_id, script.overall_sensitivity,
        )
        return job_id

    except Exception as e:
        fail_step(step_id, job_id, step_name, e)
        raise
