"""Step 3b: 민감 주제 정책 검수 — 주식/정치/의료 표현 완화 + disclaimer."""
from __future__ import annotations

import asyncio
import json
import uuid

from loguru import logger
from sqlalchemy import update

from app.config import settings
from app.db.models.video_job import VideoJob
from app.db.sync_session import SyncSessionLocal
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.services.cost_tracker import cost_tracker
from app.services.openai_client import OpenAIClient
from app.storage.object_store import object_store
from app.utils.prompts import POLICY_REVIEW_PROMPT
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


@celery_app.task(name="pipeline.policy_review", bind=True, max_retries=0)
def policy_review_task(self, job_id: str) -> str:
    step_name = "policy_review"
    step_id = begin_step(job_id, step_name)

    try:
        if check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # S3에서 FullScript 로드
        script_key = f"{job_id}/script.json"
        script_bytes = _run_async(object_store.download(settings.S3_ASSETS_BUCKET, script_key))
        script_json = script_bytes.decode("utf-8")
        script = FullScript.model_validate(json.loads(script_json))

        # policy_flags가 있는 씬 확인
        flagged_scenes = [s for s in script.scenes if s.policy_flags]

        if not flagged_scenes:
            logger.info("No policy flags found, skipping policy review: job={}", job_id)
            complete_step(
                step_id, job_id, step_name,
                progress_percent=50,
                metadata={"flagged_scenes": 0, "skipped": True},
            )
            return job_id

        # GPT-4o 정책 검수
        client = OpenAIClient()
        prompt = POLICY_REVIEW_PROMPT.format(script_json=script_json)

        resp = _run_async(client.chat(
            messages=[
                {"role": "system", "content": "당신은 미디어 콘텐츠 정책 검수 전문가입니다. 수정된 JSON만 반환하세요."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        ))

        # JSON 파싱
        review_text = resp.text.strip()
        if review_text.startswith("```"):
            lines = review_text.split("\n")
            review_text = "\n".join(lines[1:-1]) if len(lines) > 2 else review_text

        try:
            reviewed_dict = json.loads(review_text)
            reviewed_script = FullScript.model_validate(reviewed_dict)
        except Exception as parse_err:
            logger.warning("Policy review parse failed, keeping reviewed script: {}", parse_err)
            reviewed_script = script

        # S3 업데이트
        _run_async(object_store.upload(
            settings.S3_ASSETS_BUCKET,
            script_key,
            reviewed_script.model_dump_json(indent=2).encode("utf-8"),
            content_type="application/json",
        ))

        # is_sensitive_topic 갱신
        is_sensitive = reviewed_script.overall_sensitivity in ("medium", "high")
        with SyncSessionLocal() as db:
            db.execute(
                update(VideoJob)
                .where(VideoJob.id == uuid.UUID(job_id))
                .values(is_sensitive_topic=is_sensitive)
            )
            db.commit()

        # CostLog
        _run_async(cost_tracker.record_cost(
            job_id=job_id,
            step_name=step_name,
            provider="openai_chat",
            model=resp.model,
            cost_usd=resp.cost_usd,
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
        ))

        complete_step(
            step_id, job_id, step_name,
            progress_percent=50,
            artifact_keys=[script_key],
            cost_usd=resp.cost_usd,
            metadata={
                "flagged_scenes": len(flagged_scenes),
                "sensitivity": reviewed_script.overall_sensitivity,
                "policy_warnings": reviewed_script.policy_warnings,
            },
        )
        logger.info(
            "Policy review done: job={} flagged={} sensitivity={}",
            job_id, len(flagged_scenes), reviewed_script.overall_sensitivity,
        )
        return job_id

    except Exception as e:
        fail_step(step_id, job_id, step_name, e)
        raise
