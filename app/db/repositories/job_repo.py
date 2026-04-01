import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.job_step import JobStepExecution
from app.db.models.source import Source
from app.db.models.video_job import VideoJob


class JobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        user_id: uuid.UUID,
        topic: str,
        style: str,
        target_duration_minutes: int,
        language: str,
        tts_voice: str,
        additional_instructions: str | None,
        cost_budget_usd: float,
        idempotency_key: str | None,
        sources: list[dict],
    ) -> VideoJob:
        job = VideoJob(
            user_id=user_id,
            topic=topic,
            style=style,
            target_duration_minutes=target_duration_minutes,
            language=language,
            tts_voice=tts_voice,
            additional_instructions=additional_instructions,
            cost_budget_usd=cost_budget_usd,
            idempotency_key=idempotency_key,
            phase="queued",
        )
        self._db.add(job)
        await self._db.flush()

        for src in sources:
            source = Source(
                job_id=job.id,
                original_url=src["url"],
                source_type=src["source_type"],
            )
            self._db.add(source)

        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> VideoJob | None:
        result = await self._db.execute(select(VideoJob).where(VideoJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> VideoJob | None:
        result = await self._db.execute(
            select(VideoJob).where(VideoJob.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def update_phase(self, job_id: uuid.UUID, phase: str, **kwargs) -> None:
        values = {"phase": phase, "updated_at": datetime.utcnow(), **kwargs}
        await self._db.execute(
            update(VideoJob).where(VideoJob.id == job_id).values(**values)
        )
        await self._db.flush()

    async def list_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[VideoJob]:
        result = await self._db.execute(
            select(VideoJob)
            .where(VideoJob.user_id == user_id)
            .order_by(VideoJob.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        result = await self._db.execute(
            select(func.count(VideoJob.id)).where(VideoJob.user_id == user_id)
        )
        return result.scalar_one()

    async def get_steps(self, job_id: uuid.UUID) -> list[JobStepExecution]:
        result = await self._db.execute(
            select(JobStepExecution)
            .where(JobStepExecution.job_id == job_id)
            .order_by(JobStepExecution.created_at)
        )
        return list(result.scalars().all())

    async def cancel(self, job_id: uuid.UUID) -> None:
        await self.update_phase(job_id, "cancelled", is_cancelled=True)
