"""API 호출별 비용 실시간 추적 + 예산 초과 방지."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.cost_log import CostLog
from app.db.models.video_job import VideoJob
from app.db.session import async_session_factory
from app.utils.metrics import api_call_cost_usd


@dataclass
class BudgetStatus:
    total_cost_usd: float
    budget_usd: float
    remaining_usd: float
    percent_used: float
    degrade_level: int  # 0=normal, 1=reduce images, 2=flash model, 3=all text_overlay, 4=fail


class CostTracker:
    async def record_cost(
        self,
        job_id: str,
        step_name: str,
        provider: str,
        model: str,
        cost_usd: float,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        image_count: int | None = None,
        audio_seconds: float | None = None,
    ) -> CostLog:
        async with async_session_factory() as db:
            log = CostLog(
                job_id=uuid.UUID(job_id),
                step_name=step_name,
                provider=provider,
                model=model,
                cost_usd=cost_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                image_count=image_count,
                audio_seconds=audio_seconds,
            )
            db.add(log)

            # VideoJob.total_cost_usd 갱신
            await db.execute(
                update(VideoJob)
                .where(VideoJob.id == uuid.UUID(job_id))
                .values(
                    total_cost_usd=VideoJob.total_cost_usd + cost_usd,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
            await db.refresh(log)

        # Prometheus 메트릭
        api_call_cost_usd.labels(provider=provider).inc(cost_usd)

        logger.debug(
            "Cost recorded: job={} step={} provider={} model={} ${:.4f}",
            job_id, step_name, provider, model, cost_usd,
        )
        return log

    async def check_budget(self, job_id: str) -> BudgetStatus:
        async with async_session_factory() as db:
            result = await db.execute(
                select(VideoJob.total_cost_usd, VideoJob.cost_budget_usd)
                .where(VideoJob.id == uuid.UUID(job_id))
            )
            row = result.one()
            total = row[0]
            budget = row[1]

        remaining = budget - total
        percent = (total / budget * 100) if budget > 0 else 0
        level = self._calc_degrade_level(percent)

        return BudgetStatus(
            total_cost_usd=total,
            budget_usd=budget,
            remaining_usd=max(remaining, 0),
            percent_used=round(percent, 1),
            degrade_level=level,
        )

    @staticmethod
    def _calc_degrade_level(percent_used: float) -> int:
        if percent_used >= 100:
            return 4
        if percent_used >= 95:
            return 3
        if percent_used >= 90:
            return 2
        if percent_used >= 80:
            return 1
        return 0


cost_tracker = CostTracker()
