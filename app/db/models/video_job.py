import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)

    # 요청 원본
    topic: Mapped[str] = mapped_column(Text)
    style: Mapped[str] = mapped_column(String(50), default="informative")
    target_duration_minutes: Mapped[int] = mapped_column(default=12)
    language: Mapped[str] = mapped_column(String(10), default="ko")
    tts_voice: Mapped[str] = mapped_column(String(50), default="alloy")
    additional_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 상태
    phase: Mapped[str] = mapped_column(String(50), default="queued")
    progress_percent: Mapped[int] = mapped_column(default=0)
    current_step_detail: Mapped[str] = mapped_column(String(255), default="")
    is_cancelled: Mapped[bool] = mapped_column(default=False)
    is_sensitive_topic: Mapped[bool] = mapped_column(default=False)
    requires_human_approval: Mapped[bool] = mapped_column(default=False)
    human_approved: Mapped[bool | None] = mapped_column(nullable=True, default=None)
    attempt_count: Mapped[int] = mapped_column(default=0)
    max_attempts: Mapped[int] = mapped_column(default=3)
    last_completed_step: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 비용
    total_cost_usd: Mapped[float] = mapped_column(default=0.0)
    cost_budget_usd: Mapped[float] = mapped_column(default=2.0)

    # 결과
    output_video_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    output_thumbnail_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    output_script_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_duration_sec: Mapped[int | None] = mapped_column(nullable=True)
    generation_time_sec: Mapped[int | None] = mapped_column(nullable=True)

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # 관계
    user: Mapped["User"] = relationship(back_populates="jobs", lazy="selectin")  # noqa: F821
    steps: Mapped[list["JobStepExecution"]] = relationship(back_populates="job", lazy="selectin")  # noqa: F821
    sources: Mapped[list["Source"]] = relationship(back_populates="job", lazy="selectin")  # noqa: F821
    assets: Mapped[list["Asset"]] = relationship(back_populates="job", lazy="selectin")  # noqa: F821
    cost_logs: Mapped[list["CostLog"]] = relationship(back_populates="job", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<VideoJob {self.id} phase={self.phase}>"
