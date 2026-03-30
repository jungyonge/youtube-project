"""Step 3c: Human Approval 게이트 — 민감 주제는 승인 대기."""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select, update

from app.config import settings
from app.db.models.video_job import VideoJob
from app.db.session import async_session_factory
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step, publish_progress
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app

import redis.asyncio as aioredis


@celery_app.task(name="pipeline.human_gate", bind=True, max_retries=0)
def human_gate_task(self, job_id: str) -> str:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_human_gate(job_id))


async def _human_gate(job_id: str) -> str:
    step_name = "human_gate"
    step_id = await begin_step(job_id, step_name)

    try:
        if await check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # Job + Script 로드
        async with async_session_factory() as db:
            result = await db.execute(
                select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
            )
            job = result.scalar_one()

        script_key = f"{job_id}/script.json"
        script_bytes = await object_store.download(settings.S3_ASSETS_BUCKET, script_key)
        script = FullScript.model_validate(json.loads(script_bytes.decode("utf-8")))

        # 승인 필요 여부 판단
        needs_approval = script.overall_sensitivity == "high" or script.requires_human_approval

        if not needs_approval:
            logger.info("Auto-approved (no sensitive content): job={}", job_id)
            await complete_step(
                step_id, job_id, step_name,
                progress_percent=55,
                metadata={"auto_approved": True, "sensitivity": script.overall_sensitivity},
            )
            return job_id

        # 승인 대기 모드
        script_url = await object_store.presigned_url(
            settings.S3_ASSETS_BUCKET, script_key, expires_in=86400
        )

        async with async_session_factory() as db:
            await db.execute(
                update(VideoJob)
                .where(VideoJob.id == uuid.UUID(job_id))
                .values(
                    phase="awaiting_approval",
                    requires_human_approval=True,
                    current_step_detail="대본 승인 대기 중",
                    progress_percent=55,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()

        # SSE 이벤트: approval_required
        try:
            r = aioredis.from_url(settings.REDIS_URL)
            event = json.dumps({
                "type": "approval_required",
                "job_id": job_id,
                "script_preview_url": script_url,
                "sensitivity_level": script.overall_sensitivity,
            })
            await r.publish(f"video_job:{job_id}", event)
            await r.aclose()
        except Exception as e:
            logger.warning("Failed to publish approval_required event: {}", e)

        # Step 완료 (파이프라인은 여기서 멈춤)
        await complete_step(
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
        await fail_step(step_id, job_id, step_name, e)
        raise
