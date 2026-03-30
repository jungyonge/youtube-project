import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CostLog(Base):
    __tablename__ = "cost_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    step_name: Mapped[str] = mapped_column(String(50))
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    input_tokens: Mapped[int | None] = mapped_column(nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(nullable=True)
    image_count: Mapped[int | None] = mapped_column(nullable=True)
    audio_seconds: Mapped[float | None] = mapped_column(nullable=True)
    cost_usd: Mapped[float] = mapped_column(default=0.0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped["VideoJob"] = relationship(back_populates="cost_logs", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<CostLog {self.provider}/{self.model} ${self.cost_usd:.4f}>"
