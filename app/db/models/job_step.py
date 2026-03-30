import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobStepExecution(Base):
    __tablename__ = "job_steps"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    step_name: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    attempt_number: Mapped[int] = mapped_column(default=1)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_artifact_keys: Mapped[list[str]] = mapped_column(JSON, default=list)
    cost_usd: Mapped[float] = mapped_column(default=0.0)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped["VideoJob"] = relationship(back_populates="steps", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<JobStep {self.step_name} status={self.status}>"
