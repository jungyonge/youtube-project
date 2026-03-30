"""Step 1: 콘텐츠 추출 — 각 소스 URL에서 텍스트를 추출하고 S3에 저장."""
from __future__ import annotations

import asyncio
import json
import uuid

from loguru import logger
from sqlalchemy import select, update

from app.config import settings
from app.db.models.source import Source
from app.db.models.video_job import VideoJob
from app.db.session import async_session_factory
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.services.content_extractor import ContentExtractorService, ExtractedContent
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app


@celery_app.task(name="pipeline.extract", bind=True, max_retries=0)
def extract_task(self, job_id: str) -> str:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_extract(job_id))


async def _extract(job_id: str) -> str:
    step_name = "extract"
    step_id = await begin_step(job_id, step_name)

    try:
        if await check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # Load sources
        async with async_session_factory() as db:
            result = await db.execute(
                select(Source).where(Source.job_id == uuid.UUID(job_id))
            )
            sources = list(result.scalars().all())

        if not sources:
            raise ValueError("No sources found for job")

        extractor = ContentExtractorService()
        success_count = 0
        artifact_keys: list[str] = []

        for source in sources:
            try:
                content = await extractor.extract(
                    url=source.original_url,
                    source_type=source.source_type,
                )

                # S3에 스냅샷 저장
                snapshot_key = f"{job_id}/snapshots/{source.id}.json"
                snapshot_data = json.dumps({
                    "url": content.url,
                    "title": content.title,
                    "author": content.author,
                    "text_content": content.text_content,
                    "word_count": content.word_count,
                    "extraction_method": content.extraction_method,
                    "published_date": content.published_date.isoformat() if content.published_date else None,
                }, ensure_ascii=False)

                await object_store.upload(
                    settings.S3_ASSETS_BUCKET,
                    snapshot_key,
                    snapshot_data.encode("utf-8"),
                    content_type="application/json",
                )
                artifact_keys.append(snapshot_key)

                # Source 레코드 업데이트
                async with async_session_factory() as db:
                    await db.execute(
                        update(Source)
                        .where(Source.id == source.id)
                        .values(
                            title=content.title,
                            author=content.author,
                            published_at=content.published_date,
                            word_count=content.word_count,
                            extraction_method=content.extraction_method,
                            content_snapshot_key=snapshot_key,
                        )
                    )
                    await db.commit()

                success_count += 1
                logger.info(
                    "Extracted source: job={} source={} method={}",
                    job_id, source.id, content.extraction_method,
                )

            except Exception as e:
                logger.warning(
                    "Failed to extract source: job={} url={} error={}",
                    job_id, source.original_url[:80], e,
                )

        if success_count == 0:
            raise RuntimeError("All source extractions failed")

        await complete_step(
            step_id, job_id, step_name,
            progress_percent=10,
            artifact_keys=artifact_keys,
            metadata={"total_sources": len(sources), "extracted": success_count},
        )
        return job_id

    except Exception as e:
        await fail_step(step_id, job_id, step_name, e)
        raise
