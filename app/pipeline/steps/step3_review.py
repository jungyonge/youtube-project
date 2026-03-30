"""Step 3: ChatGPT 대본 검수 — claim_type, policy_flags, sensitivity 재판정."""
from __future__ import annotations

import asyncio
import json
import uuid

from loguru import logger

from app.config import settings
from app.pipeline.models.script import FullScript
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.services.cost_tracker import cost_tracker
from app.services.openai_client import OpenAIClient
from app.storage.object_store import object_store
from app.utils.prompts import SCRIPT_REVIEW_PROMPT
from app.workers.celery_app import celery_app


@celery_app.task(name="pipeline.review", bind=True, max_retries=0)
def review_task(self, job_id: str) -> str:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_review(job_id))


async def _review(job_id: str) -> str:
    step_name = "review"
    step_id = await begin_step(job_id, step_name)

    try:
        if await check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # S3에서 FullScript 로드
        script_key = f"{job_id}/script.json"
        script_bytes = await object_store.download(settings.S3_ASSETS_BUCKET, script_key)
        script_json = script_bytes.decode("utf-8")

        # ChatGPT 검수
        client = OpenAIClient()
        prompt = SCRIPT_REVIEW_PROMPT.format(script_json=script_json)

        resp = await client.chat(
            messages=[
                {"role": "system", "content": "당신은 유튜브 영상 대본 검수 전문가입니다. 수정된 JSON만 반환하세요."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        # JSON 파싱
        review_text = resp.text.strip()
        if review_text.startswith("```"):
            lines = review_text.split("\n")
            review_text = "\n".join(lines[1:-1]) if len(lines) > 2 else review_text

        try:
            reviewed_dict = json.loads(review_text)
            reviewed_script = FullScript.model_validate(reviewed_dict)
        except Exception as parse_err:
            logger.warning("Review parse failed, keeping original script: {}", parse_err)
            reviewed_script = FullScript.model_validate(json.loads(script_json))

        # S3에 덮어쓰기
        await object_store.upload(
            settings.S3_ASSETS_BUCKET,
            script_key,
            reviewed_script.model_dump_json(indent=2).encode("utf-8"),
            content_type="application/json",
        )

        # CostLog 기록
        await cost_tracker.record_cost(
            job_id=job_id,
            step_name=step_name,
            provider="openai_chat",
            model=resp.model,
            cost_usd=resp.cost_usd,
            input_tokens=resp.input_tokens,
            output_tokens=resp.output_tokens,
        )

        await complete_step(
            step_id, job_id, step_name,
            progress_percent=45,
            artifact_keys=[script_key],
            cost_usd=resp.cost_usd,
            metadata={"sensitivity": reviewed_script.overall_sensitivity},
        )
        logger.info("Script reviewed: job={} sensitivity={}", job_id, reviewed_script.overall_sensitivity)
        return job_id

    except Exception as e:
        await fail_step(step_id, job_id, step_name, e)
        raise
