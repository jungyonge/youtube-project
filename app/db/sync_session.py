"""
Celery Worker 전용 동기 DB 세션.

FastAPI(API 계층)는 async session(asyncpg)을 사용하지만,
Celery는 태생적으로 동기 워커이므로 async session을 사용하면
Event Loop 충돌 또는 Deadlock이 발생한다.

규칙:
  - API 라우트 → session.py의 AsyncSession만 사용
  - Celery task → 이 파일의 SyncSession만 사용
  - 절대로 Celery task 안에서 AsyncSession을 import하지 말 것
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
)


def get_sync_db() -> Generator[Session, None, None]:
    """Celery task 내부에서 사용하는 동기 DB 세션."""
    with SyncSessionLocal() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
