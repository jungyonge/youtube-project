import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.response import JobStatusResponse, JobStepResponse
from app.auth.dependencies import get_current_user
from app.config import settings
from app.db.models.user import User
from app.db.repositories.job_repo import JobRepository
from app.db.session import get_db
from app.storage.object_store import object_store

router = APIRouter(prefix="/api/v1/videos", tags=["videos"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobStatusResponse:
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Owner check
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Generate presigned URLs for completed jobs
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

    return JobStatusResponse(
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


@router.get("/{job_id}/steps", response_model=list[JobStepResponse])
async def get_job_steps(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JobStepResponse]:
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    steps = await repo.get_steps(job_id)
    return [
        JobStepResponse(
            step_name=s.step_name,
            status=s.status,
            started_at=s.started_at,
            completed_at=s.completed_at,
            duration_sec=s.duration_sec,
            cost_usd=s.cost_usd,
            error_message=s.error_message,
        )
        for s in steps
    ]
