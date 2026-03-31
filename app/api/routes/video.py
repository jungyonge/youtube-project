import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.request import VideoGenerationRequest
from app.api.schemas.response import JobCreateResponse, JobStatusResponse, PaginatedResponse
from app.auth.dependencies import get_current_user
from app.config import settings
from app.db.models.user import User
from app.db.repositories.job_repo import JobRepository
from app.db.repositories.user_repo import UserRepository
from app.db.session import get_db
from app.storage.object_store import object_store

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])


@router.get("", response_model=PaginatedResponse)
async def list_videos(
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse:
    repo = JobRepository(db)
    skip = (page - 1) * size
    jobs = await repo.list_by_user(current_user.id, skip=skip, limit=size)
    total = await repo.count_by_user(current_user.id)

    items = []
    for job in jobs:
        download_url = None
        script_preview_url = None
        if job.output_video_key and job.phase == "completed":
            download_url = await object_store.presigned_url(
                settings.S3_OUTPUTS_BUCKET, job.output_video_key
            )
        if job.output_script_key:
            script_preview_url = await object_store.presigned_url(
                settings.S3_ASSETS_BUCKET, job.output_script_key
            )
        items.append(
            JobStatusResponse(
                job_id=str(job.id),
                phase=job.phase,
                progress_percent=job.progress_percent,
                current_step_detail=job.current_step_detail,
                is_cancelled=job.is_cancelled,
                requires_human_approval=job.requires_human_approval,
                human_approved=job.human_approved,
                total_cost_usd=job.total_cost_usd,
                cost_budget_usd=job.cost_budget_usd,
                attempt_count=job.attempt_count,
                created_at=job.created_at,
                updated_at=job.updated_at,
                download_url=download_url,
                script_preview_url=script_preview_url,
            )
        )

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        has_next=(skip + size) < total,
    )


@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_video(
    body: VideoGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobCreateResponse:
    job_repo = JobRepository(db)
    user_repo = UserRepository(db)

    # Idempotency check (DB level)
    if body.idempotency_key:
        existing = await job_repo.get_by_idempotency_key(body.idempotency_key)
        if existing:
            logger.info("Idempotent request returned existing job={}", existing.id)
            return JobCreateResponse(
                job_id=str(existing.id),
                phase=existing.phase,
                created_at=existing.created_at,
            )

    # Daily quota check
    daily_count = await user_repo.get_daily_job_count(current_user.id)
    if daily_count >= current_user.daily_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily quota exceeded ({current_user.daily_quota} videos/day)",
        )

    # Determine cost budget
    budget = body.cost_budget_usd or settings.DEFAULT_COST_BUDGET_USD

    # Create job + sources
    sources_data = [{"url": s.url, "source_type": s.source_type} for s in body.sources]
    job = await job_repo.create(
        user_id=current_user.id,
        topic=body.topic,
        style=body.style.value,
        target_duration_minutes=body.target_duration_minutes,
        language=body.language,
        tts_voice=body.tts_voice,
        additional_instructions=body.additional_instructions,
        cost_budget_usd=budget,
        idempotency_key=body.idempotency_key,
        sources=sources_data,
    )

    logger.info("Created video job={} topic='{}' for user={}", job.id, body.topic, current_user.id)

    from app.pipeline.orchestrator import start_pipeline
    start_pipeline(str(job.id))

    return JobCreateResponse(
        job_id=str(job.id),
        phase=job.phase,
        created_at=job.created_at,
    )


@router.post("/{job_id}/approve")
async def approve_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if job.phase != "awaiting_approval":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not awaiting approval (phase={job.phase})")

    await repo.update_phase(
        job_id,
        phase="approved",
        human_approved=True,
        current_step_detail="Human approved, resuming pipeline",
    )

    logger.info("Job approved: job={} by user={}", job_id, current_user.id)

    from app.pipeline.orchestrator import resume_pipeline
    resume_pipeline(str(job_id), from_step="tts")

    return {"job_id": str(job_id), "phase": "approved", "message": "Pipeline resumed"}


@router.post("/{job_id}/reject")
async def reject_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if job.phase != "awaiting_approval":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job is not awaiting approval (phase={job.phase})")

    await repo.update_phase(
        job_id,
        phase="rejected",
        human_approved=False,
        current_step_detail="Rejected by user",
    )

    logger.info("Job rejected: job={} by user={}", job_id, current_user.id)
    return {"job_id": str(job_id), "phase": "rejected", "message": "대본을 수정 후 새로 요청해주세요."}


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if job.phase in ("completed", "cancelled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Job already {job.phase}")

    await repo.cancel(job_id)
    logger.info("Job cancelled: job={} by user={}", job_id, current_user.id)
    return {"job_id": str(job_id), "phase": "cancelled"}


@router.post("/{job_id}/retry")
async def retry_job(
    job_id: uuid.UUID,
    from_step: str = "extract",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if job.attempt_count >= job.max_attempts:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Max retry attempts reached ({job.max_attempts})")

    await repo.update_phase(
        job_id,
        phase="running",
        attempt_count=job.attempt_count + 1,
        current_step_detail=f"Retrying from {from_step}",
    )

    from app.pipeline.orchestrator import resume_pipeline
    resume_pipeline(str(job_id), from_step=from_step)

    logger.info("Job retry: job={} from_step={} attempt={}", job_id, from_step, job.attempt_count + 1)
    return {"job_id": str(job_id), "phase": "running", "attempt_count": job.attempt_count + 1}
