import uuid
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    daily_quota: Mapped[int] = mapped_column(default=5)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    jobs: Mapped[list["VideoJob"]] = relationship(back_populates="user", lazy="selectin")  # noqa: F821

    def __repr__(self) -> str:
        return f"<User {self.email}>"
