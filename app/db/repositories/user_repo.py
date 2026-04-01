import uuid
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.video_job import VideoJob


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, email: str, hashed_password: str, role: str = "user", daily_quota: int = 5) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role,
            daily_quota=daily_quota,
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_daily_job_count(self, user_id: uuid.UUID, target_date: date | None = None) -> int:
        if target_date is None:
            target_date = datetime.now(timezone.utc).date()
        start = datetime(target_date.year, target_date.month, target_date.day)
        end = start + __import__("datetime").timedelta(days=1)
        result = await self._db.execute(
            select(func.count(VideoJob.id)).where(
                VideoJob.user_id == user_id,
                VideoJob.created_at >= start,
                VideoJob.created_at < end,
            )
        )
        return result.scalar_one()
