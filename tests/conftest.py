"""pytest fixture 모음 — DB, Redis mock, S3 mock, API client, factories."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.jwt_handler import create_access_token
from app.auth.password import hash_password
from app.db.base import Base
from app.db.models import Asset, CostLog, JobStepExecution, Source, User, VideoJob
from app.pipeline.models.evidence import EvidencePack, RankedEvidence, SourceChunk
from app.pipeline.models.script import FullScript, SceneAssetPlan, ScriptScene

# ---------------------------------------------------------------------------
# DB fixtures (SQLite async for testing)
# ---------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///test.db"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def override_db(db_session):
    """Override the get_db dependency for FastAPI."""
    from app.db.session import get_db

    async def _override():
        yield db_session

    return _override


# ---------------------------------------------------------------------------
# Sync DB session (Celery task 테스트용)
# ---------------------------------------------------------------------------
@pytest.fixture
def sync_db_session(test_engine):
    """Celery task 테스트를 위한 동기 DB 세션.

    SyncSessionLocal을 mock하여 테스트용 동기 세션을 주입한다.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    sync_engine = create_engine("sqlite:///test.db", echo=False)
    SyncTestSession = sessionmaker(bind=sync_engine, class_=Session, expire_on_commit=False)
    session = SyncTestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def override_sync_session(sync_db_session):
    """Override SyncSessionLocal for pipeline step tests."""
    from unittest.mock import patch

    class MockSessionLocal:
        def __enter__(self):
            return sync_db_session

        def __exit__(self, *args):
            pass

        def __call__(self):
            return self

    with patch("app.db.sync_session.SyncSessionLocal", MockSessionLocal):
        yield sync_db_session


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client(override_db):
    from app.main import app
    from app.db.session import get_db

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        role="user",
        daily_quota=5,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        daily_quota=100,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    token = create_access_token({"sub": str(test_user.id), "email": test_user.email, "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    token = create_access_token({"sub": str(admin_user.id), "email": admin_user.email, "role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Factory fixtures
# ---------------------------------------------------------------------------
def make_evidence_pack(topic: str = "테스트 주제") -> EvidencePack:
    chunk = SourceChunk(source_id="src-1", chunk_index=0, text="테스트 근거 텍스트입니다.")
    ranked = RankedEvidence(
        chunk=chunk,
        relevance_score=0.8,
        recency_score=0.9,
        reliability_score=0.7,
        composite_score=0.8,
    )
    return EvidencePack(
        topic=topic,
        total_sources=1,
        deduplicated_sources=1,
        ranked_chunks=[ranked],
        key_claims=["핵심 주장 1", "핵심 주장 2"],
        source_metadata=[{"domain": "example.com", "title": "테스트 소스"}],
    )


def make_full_script(scenes_count: int = 3) -> FullScript:
    scenes = []
    for i in range(scenes_count):
        scenes.append(ScriptScene(
            scene_id=i + 1,
            section=["hook", "body_1", "conclusion"][i % 3],
            purpose=f"테스트 씬 {i+1}",
            duration_target_sec=30,
            narration=f"이것은 테스트 나레이션 {i+1}입니다. 충분한 길이로 작성합니다.",
            asset_plan=[SceneAssetPlan(asset_type="text_overlay")],
            keywords=[f"키워드{i+1}"],
        ))
    return FullScript(
        title="테스트 영상",
        subtitle="서브타이틀",
        total_duration_sec=scenes_count * 30,
        thumbnail_prompt="test thumbnail",
        scenes=scenes,
    )


# ---------------------------------------------------------------------------
# External API mocks
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_object_store():
    """In-memory S3 mock."""
    storage: dict[str, bytes] = {}

    async def upload(bucket, key, data, content_type=""):
        storage[f"{bucket}/{key}"] = data
        return key

    async def download(bucket, key):
        k = f"{bucket}/{key}"
        if k not in storage:
            raise FileNotFoundError(k)
        return storage[k]

    async def presigned_url(bucket, key, expires_in=3600):
        return f"http://mock-s3/{bucket}/{key}"

    async def delete(bucket, key):
        storage.pop(f"{bucket}/{key}", None)

    async def exists(bucket, key):
        return f"{bucket}/{key}" in storage

    async def ensure_bucket(bucket):
        pass

    mock = MagicMock()
    mock.upload = AsyncMock(side_effect=upload)
    mock.download = AsyncMock(side_effect=download)
    mock.presigned_url = AsyncMock(side_effect=presigned_url)
    mock.delete = AsyncMock(side_effect=delete)
    mock.exists = AsyncMock(side_effect=exists)
    mock.ensure_bucket = AsyncMock(side_effect=ensure_bucket)
    mock._storage = storage

    return mock
