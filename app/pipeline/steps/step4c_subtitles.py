"""Step 4c: SRT 자막 생성 — TTS 실측 duration 기반."""
from __future__ import annotations

import asyncio
import json
import uuid

from loguru import logger

from app.config import settings
from app.db.models.asset import Asset
from app.db.session import async_session_factory
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app

SUBTITLE_CHUNK_SIZE = 20  # 한국어 최적화 20자


def _split_text_to_chunks(text: str, chunk_size: int = SUBTITLE_CHUNK_SIZE) -> list[str]:
    """텍스트를 chunk_size 글자 단위로 분절."""
    words = text.replace("\n", " ").split()
    chunks: list[str] = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 > chunk_size and current:
            chunks.append(current.strip())
            current = word
        else:
            current += (" " + word) if current else word

    if current.strip():
        chunks.append(current.strip())

    return chunks if chunks else [text]


def _format_srt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _build_srt(script: FullScript) -> str:
    """FullScript에서 SRT 자막 파일 생성."""
    srt_entries: list[str] = []
    idx = 1
    cumulative_time = 0.0

    for scene in script.scenes:
        duration = scene.duration_actual_sec or scene.duration_target_sec

        # subtitle_chunks가 있으면 사용, 없으면 narration에서 생성
        chunks = scene.subtitle_chunks if scene.subtitle_chunks else _split_text_to_chunks(scene.narration)

        if not chunks:
            cumulative_time += duration
            continue

        chunk_duration = duration / len(chunks)

        for chunk in chunks:
            start = cumulative_time
            end = cumulative_time + chunk_duration

            srt_entries.append(
                f"{idx}\n"
                f"{_format_srt_time(start)} --> {_format_srt_time(end)}\n"
                f"{chunk}\n"
            )
            idx += 1
            cumulative_time = end

    return "\n".join(srt_entries)


@celery_app.task(name="pipeline.subtitles", bind=True, max_retries=0)
def subtitle_task(self, job_id: str) -> str:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_subtitles(job_id))


async def _subtitles(job_id: str) -> str:
    step_name = "subtitles"
    step_id = await begin_step(job_id, step_name)

    try:
        if await check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # FullScript 로드
        script_key = f"{job_id}/script.json"
        script_bytes = await object_store.download(settings.S3_ASSETS_BUCKET, script_key)
        script = FullScript.model_validate(json.loads(script_bytes.decode("utf-8")))

        # SRT 생성
        srt_content = _build_srt(script)

        # S3 업로드
        srt_key = f"{job_id}/subtitles/subtitles.srt"
        await object_store.upload(
            settings.S3_ASSETS_BUCKET,
            srt_key,
            srt_content.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )

        # Asset 등록
        async with async_session_factory() as db:
            asset = Asset(
                job_id=uuid.UUID(job_id),
                asset_type="subtitle",
                object_key=srt_key,
                file_size_bytes=len(srt_content.encode("utf-8")),
                mime_type="text/srt",
            )
            db.add(asset)
            await db.commit()

        await complete_step(
            step_id, job_id, step_name,
            progress_percent=80,
            artifact_keys=[srt_key],
            metadata={"srt_entries": srt_content.count("\n\n")},
        )
        logger.info("Subtitles generated: job={}", job_id)
        return job_id

    except Exception as e:
        await fail_step(step_id, job_id, step_name, e)
        raise
