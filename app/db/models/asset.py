import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(50))
    scene_id: Mapped[int | None] = mapped_column(nullable=True)
    object_key: Mapped[str] = mapped_column(String(500))
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_sec: Mapped[float | None] = mapped_column(nullable=True)
    is_fallback: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped["VideoJob"] = relationship(back_populates="assets", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Asset {self.asset_type} key={self.object_key}>"
