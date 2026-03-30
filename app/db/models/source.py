import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    original_url: Mapped[str] = mapped_column(Text)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(20))
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    word_count: Mapped[int | None] = mapped_column(nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content_snapshot_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(default=False)
    reliability_score: Mapped[float | None] = mapped_column(nullable=True)
    relevance_score: Mapped[float | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    job: Mapped["VideoJob"] = relationship(back_populates="sources", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Source {self.source_type} url={self.original_url[:50]}>"
