"""Step 4d: BGM 선택 + 루프 처리."""
from __future__ import annotations

import asyncio
import json
import os
import uuid

from loguru import logger

from app.config import settings
from app.db.models.asset import Asset
from app.db.session import async_session_factory
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app

# 스타일별 BGM 매핑
_BGM_MAP = {
    "informative": "calm_bgm.mp3",
    "entertaining": "upbeat_bgm.mp3",
    "educational": "neutral_bgm.mp3",
    "news": "news_bgm.mp3",
}

BGM_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "assets", "bgm")


@celery_app.task(name="pipeline.bgm", bind=True, max_retries=0)
def bgm_task(self, job_id: str) -> str:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_bgm(job_id))


async def _bgm(job_id: str) -> str:
    step_name = "bgm"
    step_id = await begin_step(job_id, step_name)

    try:
        if await check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # Job style 확인
        async with async_session_factory() as db:
            from sqlalchemy import select
            from app.db.models.video_job import VideoJob
            result = await db.execute(
                select(VideoJob.style).where(VideoJob.id == uuid.UUID(job_id))
            )
            style = result.scalar_one()

        # BGM 파일 찾기
        bgm_filename = _BGM_MAP.get(style, "calm_bgm.mp3")
        bgm_path = os.path.normpath(os.path.join(BGM_DIR, bgm_filename))

        bgm_key = f"{job_id}/audio/bgm.mp3"

        if os.path.exists(bgm_path):
            with open(bgm_path, "rb") as f:
                bgm_bytes = f.read()
            logger.info("Using BGM file: {}", bgm_filename)
        else:
            # BGM 파일이 없으면 빈 placeholder 생성
            logger.warning("BGM file not found: {}, creating silent placeholder", bgm_path)
            bgm_bytes = b"\x00" * 1024  # minimal placeholder

        # S3 업로드
        await object_store.upload(
            settings.S3_ASSETS_BUCKET,
            bgm_key,
            bgm_bytes,
            content_type="audio/mpeg",
        )

        # Asset 등록
        async with async_session_factory() as db:
            asset = Asset(
                job_id=uuid.UUID(job_id),
                asset_type="bgm",
                object_key=bgm_key,
                file_size_bytes=len(bgm_bytes),
                mime_type="audio/mpeg",
                is_fallback=not os.path.exists(bgm_path),
            )
            db.add(asset)
            await db.commit()

        await complete_step(
            step_id, job_id, step_name,
            progress_percent=82,
            artifact_keys=[bgm_key],
            metadata={"bgm_file": bgm_filename, "size_bytes": len(bgm_bytes)},
        )
        logger.info("BGM completed: job={} file={}", job_id, bgm_filename)
        return job_id

    except Exception as e:
        await fail_step(step_id, job_id, step_name, e)
        raise
