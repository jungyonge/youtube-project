"""파이프라인 오케스트레이터 — Celery task 체인 구성."""
from __future__ import annotations

from celery import chain, chord
from loguru import logger

from app.pipeline.steps.step1_extract import extract_task
from app.pipeline.steps.step1b_normalize import normalize_task
from app.pipeline.steps.step1c_evidence_pack import evidence_pack_task
from app.pipeline.steps.step2_research import research_task
from app.pipeline.steps.step3_review import review_task
from app.pipeline.steps.step3b_policy_review import policy_review_task
from app.pipeline.steps.step3c_human_gate import human_gate_task
from app.pipeline.steps.step4a_tts import tts_task
from app.pipeline.steps.step4b_images import images_task
from app.pipeline.steps.step4c_subtitles import subtitle_task
from app.pipeline.steps.step4d_bgm import bgm_task
from app.pipeline.steps.step5_assemble import assemble_task

# Step 이름 → task 매핑 (순서 보장)
STEP_ORDER = [
    ("extract", extract_task),
    ("normalize", normalize_task),
    ("evidence_pack", evidence_pack_task),
    ("research", research_task),
    ("review", review_task),
    ("policy_review", policy_review_task),
    ("human_gate", human_gate_task),
    ("tts", tts_task),
    ("images", images_task),
    ("bgm", bgm_task),
    ("subtitles", subtitle_task),
    ("assemble", assemble_task),
]


def start_pipeline(job_id: str):
    """전체 파이프라인 체인 시작."""
    pipeline = chain(
        extract_task.s(job_id),
        normalize_task.s(),
        evidence_pack_task.s(),
        research_task.s(),
        review_task.s(),
        policy_review_task.s(),
        human_gate_task.s(),
        tts_task.s(),
        images_task.s(),
        bgm_task.s(),
        subtitle_task.s(),
        assemble_task.s(),
    )
    logger.info("Starting pipeline for job={}", job_id)
    return pipeline.apply_async()


def resume_pipeline(job_id: str, from_step: str = "tts"):
    """특정 step부터 파이프라인 재개 (human gate 승인 후 등)."""
    step_names = [name for name, _ in STEP_ORDER]

    if from_step not in step_names:
        raise ValueError(f"Unknown step: {from_step}. Available: {step_names}")

    start_idx = step_names.index(from_step)
    remaining_tasks = [task for _, task in STEP_ORDER[start_idx:]]

    if not remaining_tasks:
        raise ValueError(f"No tasks to run from step: {from_step}")

    # 체인 구성: 첫 task에 job_id 전달, 이후는 이전 결과(job_id)를 받음
    pipeline = chain(
        remaining_tasks[0].s(job_id),
        *[t.s() for t in remaining_tasks[1:]],
    )
    logger.info("Resuming pipeline for job={} from_step={}", job_id, from_step)
    return pipeline.apply_async()
