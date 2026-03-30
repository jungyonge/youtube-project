"""Step 4a: TTS 음성 생성 — 씬별 나레이션 오디오."""
from __future__ import annotations

import asyncio
import io
import json
import struct
import uuid

from loguru import logger
from sqlalchemy import select

from app.config import settings
from app.db.models.video_job import VideoJob
from app.db.session import async_session_factory
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.services.cost_tracker import cost_tracker
from app.services.openai_client import OpenAIClient
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app


def _estimate_mp3_duration(data: bytes) -> float:
    """MP3 파일의 대략적인 재생 시간을 추정 (바이트 크기 기반)."""
    # 평균 비트레이트 128kbps 기준
    return len(data) * 8 / (128 * 1000)


@celery_app.task(name="pipeline.tts", bind=True, max_retries=0)
def tts_task(self, job_id: str) -> str:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_tts(job_id))


async def _tts(job_id: str) -> str:
    step_name = "tts"
    step_id = await begin_step(job_id, step_name)

    try:
        if await check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # Job 정보 로드
        async with async_session_factory() as db:
            result = await db.execute(
                select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
            )
            job = result.scalar_one()

        # FullScript 로드
        script_key = f"{job_id}/script.json"
        script_bytes = await object_store.download(settings.S3_ASSETS_BUCKET, script_key)
        script = FullScript.model_validate(json.loads(script_bytes.decode("utf-8")))

        client = OpenAIClient()
        artifact_keys: list[str] = []
        total_cost = 0.0
        scene_durations: dict[int, float] = {}

        for scene in script.scenes:
            if await check_cancelled(job_id):
                raise RuntimeError("Job cancelled")

            # 예산 체크
            budget = await cost_tracker.check_budget(job_id)
            if budget.degrade_level >= 4:
                logger.warning("Budget exceeded, skipping remaining TTS: job={}", job_id)
                break

            try:
                audio_bytes, cost = await client.tts(
                    text=scene.narration,
                    voice=job.tts_voice,
                )

                # S3 업로드
                audio_key = f"{job_id}/audio/scene_{scene.scene_id}.mp3"
                await object_store.upload(
                    settings.S3_ASSETS_BUCKET,
                    audio_key,
                    audio_bytes,
                    content_type="audio/mpeg",
                )
                artifact_keys.append(audio_key)

                # 오디오 길이 추정
                duration = _estimate_mp3_duration(audio_bytes)
                scene_durations[scene.scene_id] = duration

                # Asset 등록
                async with async_session_factory() as db:
                    from app.db.models.asset import Asset
                    asset = Asset(
                        job_id=uuid.UUID(job_id),
                        asset_type="tts_audio",
                        scene_id=scene.scene_id,
                        object_key=audio_key,
                        file_size_bytes=len(audio_bytes),
                        mime_type="audio/mpeg",
                        duration_sec=duration,
                    )
                    db.add(asset)
                    await db.commit()

                # CostLog
                await cost_tracker.record_cost(
                    job_id=job_id,
                    step_name=step_name,
                    provider="openai_tts",
                    model=settings.OPENAI_TTS_MODEL,
                    cost_usd=cost,
                    audio_seconds=duration,
                )
                total_cost += cost

                logger.debug(
                    "TTS scene {}: {} chars, {:.1f}s, ${:.4f}",
                    scene.scene_id, len(scene.narration), duration, cost,
                )

            except Exception as e:
                logger.warning("TTS failed for scene {}: {}", scene.scene_id, e)
                # placeholder: 무음
                scene_durations[scene.scene_id] = scene.duration_target_sec

        # FullScript에 실측 duration 반영 → S3 업데이트
        for scene in script.scenes:
            if scene.scene_id in scene_durations:
                scene.duration_actual_sec = int(scene_durations[scene.scene_id])

        await object_store.upload(
            settings.S3_ASSETS_BUCKET,
            script_key,
            script.model_dump_json(indent=2).encode("utf-8"),
            content_type="application/json",
        )

        await complete_step(
            step_id, job_id, step_name,
            progress_percent=65,
            artifact_keys=artifact_keys,
            cost_usd=total_cost,
            metadata={"scenes_processed": len(scene_durations), "total_cost": round(total_cost, 4)},
        )
        logger.info("TTS completed: job={} scenes={} cost=${:.4f}", job_id, len(scene_durations), total_cost)
        return job_id

    except Exception as e:
        await fail_step(step_id, job_id, step_name, e)
        raise
