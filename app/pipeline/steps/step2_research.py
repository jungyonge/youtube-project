"""Step 2: Gemini 대본 생성 — EvidencePack → FullScript."""
from __future__ import annotations

import asyncio
import json
import uuid

from loguru import logger
from sqlalchemy import select, update

from app.config import settings
from app.db.models.video_job import VideoJob
from app.db.sync_session import SyncSessionLocal
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.services.cost_tracker import cost_tracker
from app.services.gemini_client import GeminiClient
from app.storage.object_store import object_store
from app.utils.prompts import SCRIPT_GENERATION_PROMPT
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


@celery_app.task(name="pipeline.research", bind=True, max_retries=0)
def research_task(self, job_id: str) -> str:
    step_name = "research"
    step_id = begin_step(job_id, step_name)

    try:
        if check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # Job 정보 로드
        with SyncSessionLocal() as db:
            result = db.execute(
                select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
            )
            job = result.scalar_one()

        # EvidencePack 로드
        pack_key = f"{job_id}/evidence_pack.json"
        pack_bytes = _run_async(object_store.download(settings.S3_ASSETS_BUCKET, pack_key))
        pack_data = json.loads(pack_bytes.decode("utf-8"))

        # 비용 체크 → 모델 결정
        budget_status = _run_async(cost_tracker.check_budget(job_id))
        model = None
        if budget_status.degrade_level >= 2:
            model = "gemini-2.5-flash"
            logger.info("Budget degrade: using Flash model for job={}", job_id)

        client = GeminiClient(model=model)

        # 프롬프트 렌더링
        target_duration = job.target_duration_minutes
        total_sec = target_duration * 60
        min_scenes = max(target_duration * 2, 15)
        max_scenes = target_duration * 3
        body_end_min = target_duration - 1

        key_claims = "\n".join(f"- {c}" for c in pack_data.get("key_claims", []))
        ranked_chunks = "\n\n".join(
            f"[Chunk {i+1}] (score={c['composite_score']:.2f}) source={c['chunk']['source_id']}\n{c['chunk']['text'][:300]}"
            for i, c in enumerate(pack_data.get("ranked_chunks", [])[:15])
        )
        source_meta = "\n".join(
            f"- {m.get('domain', 'unknown')}: {m.get('title', 'N/A')} (reliability={m.get('reliability_score', 0.3)})"
            for m in pack_data.get("source_metadata", [])
        )

        prompt = SCRIPT_GENERATION_PROMPT.format(
            target_duration=target_duration,
            topic=job.topic,
            style=job.style,
            additional_instructions=job.additional_instructions or "없음",
            key_claims=key_claims or "없음",
            ranked_chunks_formatted=ranked_chunks or "없음",
            source_metadata_formatted=source_meta or "없음",
            body_end=f"{body_end_min}:00",
            total=f"{target_duration}:00",
            min_scenes=min_scenes,
            max_scenes=max_scenes,
        )

        # Gemini 호출 (JSON 모드)
        script_dict = _run_async(client.generate_json(
            prompt=prompt,
            system_instruction="당신은 한국 유튜브 콘텐츠 전문 작가입니다. FullScript JSON 스키마를 정확히 따르세요.",
            temperature=0.7,
        ))

        # 메타 정보 분리
        meta = script_dict.pop("_meta", {})

        # FullScript 파싱 (검증)
        try:
            full_script = FullScript.model_validate(script_dict)
        except Exception as parse_err:
            logger.warning("FullScript parse failed, retrying with reinforced prompt: {}", parse_err)
            # 재시도: 더 명확한 지시
            script_dict = _run_async(client.generate_json(
                prompt=prompt + "\n\n위 JSON 스키마를 반드시 정확히 따르세요. 모든 필드를 포함하세요.",
                temperature=0.3,
            ))
            meta = script_dict.pop("_meta", {})
            full_script = FullScript.model_validate(script_dict)

        # S3에 저장
        script_key = f"{job_id}/script.json"
        _run_async(object_store.upload(
            settings.S3_ASSETS_BUCKET,
            script_key,
            full_script.model_dump_json(indent=2).encode("utf-8"),
            content_type="application/json",
        ))

        # CostLog 기록
        _run_async(cost_tracker.record_cost(
            job_id=job_id,
            step_name=step_name,
            provider="gemini",
            model=meta.get("model", settings.GEMINI_MODEL),
            cost_usd=meta.get("cost_usd", 0),
            input_tokens=meta.get("input_tokens", 0),
            output_tokens=meta.get("output_tokens", 0),
        ))

        # output_script_key 갱신
        with SyncSessionLocal() as db:
            db.execute(
                update(VideoJob)
                .where(VideoJob.id == uuid.UUID(job_id))
                .values(output_script_key=script_key)
            )
            db.commit()

        complete_step(
            step_id, job_id, step_name,
            progress_percent=35,
            artifact_keys=[script_key],
            cost_usd=meta.get("cost_usd", 0),
            metadata={"scenes": len(full_script.scenes), "sensitivity": full_script.overall_sensitivity},
        )
        logger.info("Script generated: job={} scenes={} sensitivity={}", job_id, len(full_script.scenes), full_script.overall_sensitivity)
        return job_id

    except Exception as e:
        fail_step(step_id, job_id, step_name, e)
        raise
