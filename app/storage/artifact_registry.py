"""Job별 산출물 관리 (S3 + DB 연동)."""
from __future__ import annotations

import uuid

from loguru import logger
from sqlalchemy import select

from app.config import settings
from app.db.models.asset import Asset
from app.db.session import async_session_factory
from app.storage.object_store import object_store


class ArtifactRegistry:
    async def register(
        self,
        job_id: str,
        asset_type: str,
        object_key: str,
        data: bytes,
        mime_type: str,
        scene_id: int | None = None,
        duration_sec: float | None = None,
        is_fallback: bool = False,
    ) -> Asset:
        # S3 업로드
        bucket = settings.S3_OUTPUTS_BUCKET if asset_type == "video" else settings.S3_ASSETS_BUCKET
        await object_store.upload(bucket, object_key, data, content_type=mime_type)

        # DB 등록
        async with async_session_factory() as db:
            asset = Asset(
                job_id=uuid.UUID(job_id),
                asset_type=asset_type,
                scene_id=scene_id,
                object_key=object_key,
                file_size_bytes=len(data),
                mime_type=mime_type,
                duration_sec=duration_sec,
                is_fallback=is_fallback,
            )
            db.add(asset)
            await db.commit()
            await db.refresh(asset)

        logger.debug("Artifact registered: job={} type={} key={}", job_id, asset_type, object_key)
        return asset

    async def get_assets(
        self, job_id: str, asset_type: str | None = None
    ) -> list[Asset]:
        async with async_session_factory() as db:
            stmt = select(Asset).where(Asset.job_id == uuid.UUID(job_id))
            if asset_type:
                stmt = stmt.where(Asset.asset_type == asset_type)
            result = await db.execute(stmt.order_by(Asset.scene_id))
            return list(result.scalars().all())

    async def get_presigned_url(self, asset: Asset, expires_in: int = 3600) -> str:
        bucket = settings.S3_OUTPUTS_BUCKET if asset.asset_type == "video" else settings.S3_ASSETS_BUCKET
        return await object_store.presigned_url(bucket, asset.object_key, expires_in)

    async def delete_job_assets(
        self, job_id: str, after_step: str | None = None
    ) -> int:
        assets = await self.get_assets(job_id)
        count = 0
        for asset in assets:
            bucket = settings.S3_OUTPUTS_BUCKET if asset.asset_type == "video" else settings.S3_ASSETS_BUCKET
            try:
                await object_store.delete(bucket, asset.object_key)
                count += 1
            except Exception as e:
                logger.warning("Failed to delete asset {}: {}", asset.object_key, e)

        async with async_session_factory() as db:
            for asset in assets:
                await db.delete(asset)
            await db.commit()

        logger.info("Deleted {} assets for job={}", count, job_id)
        return count

    async def cleanup_expired(self, ttl_hours: int) -> int:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(hours=ttl_hours)

        async with async_session_factory() as db:
            result = await db.execute(
                select(Asset).where(Asset.created_at < cutoff)
            )
            expired = list(result.scalars().all())

        count = 0
        for asset in expired:
            bucket = settings.S3_OUTPUTS_BUCKET if asset.asset_type == "video" else settings.S3_ASSETS_BUCKET
            try:
                await object_store.delete(bucket, asset.object_key)
                count += 1
            except Exception:
                pass

        async with async_session_factory() as db:
            for asset in expired:
                await db.delete(asset)
            await db.commit()

        if count:
            logger.info("Cleaned up {} expired assets", count)
        return count


artifact_registry = ArtifactRegistry()
