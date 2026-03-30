import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.asset import Asset


class AssetRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        job_id: uuid.UUID,
        asset_type: str,
        object_key: str,
        scene_id: int | None = None,
        file_size_bytes: int | None = None,
        mime_type: str | None = None,
        duration_sec: float | None = None,
        is_fallback: bool = False,
    ) -> Asset:
        asset = Asset(
            job_id=job_id,
            asset_type=asset_type,
            object_key=object_key,
            scene_id=scene_id,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
            duration_sec=duration_sec,
            is_fallback=is_fallback,
        )
        self._db.add(asset)
        await self._db.flush()
        await self._db.refresh(asset)
        return asset

    async def get_by_job(self, job_id: uuid.UUID, asset_type: str | None = None) -> list[Asset]:
        stmt = select(Asset).where(Asset.job_id == job_id)
        if asset_type:
            stmt = stmt.where(Asset.asset_type == asset_type)
        result = await self._db.execute(stmt.order_by(Asset.scene_id))
        return list(result.scalars().all())

    async def delete_by_job(self, job_id: uuid.UUID) -> int:
        assets = await self.get_by_job(job_id)
        count = len(assets)
        for asset in assets:
            await self._db.delete(asset)
        await self._db.flush()
        return count
