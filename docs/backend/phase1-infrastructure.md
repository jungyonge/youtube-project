# Phase 1: 프로젝트 뼈대 + 인프라

## 목표
프로젝트 디렉토리 구조, 의존성, 설정, Docker 인프라, DB 모델, 오브젝트 스토리지 래퍼 등
서비스의 기반을 구축한다.

---

## 저장소 삼분할 원칙

```
Redis    = 휘발성 (큐, 캐시, pub/sub, 실시간 상태)
Postgres = 진실의 원천 (유저, Job, Step, 비용, 에러 로그, 소스 메타)
MinIO/S3 = 산출물 저장 (이미지, 오디오, 영상, 대본 JSON)
```
파일 경로 대신 **object key + presigned URL**로 산출물을 관리한다.
로컬 파일시스템은 **개발 환경 전용**으로만 허용한다.

---

## 구현 항목

### 1. 디렉토리 구조 생성

```
ai-video-pipeline/
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.worker
├── alembic/
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── auth/
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   └── middleware/
│   │       └── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py            # async SQLAlchemy session (API용)
│   │   ├── sync_session.py       # sync SQLAlchemy session (Celery Worker용)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── video_job.py
│   │   │   ├── job_step.py
│   │   │   ├── source.py
│   │   │   ├── asset.py
│   │   │   └── cost_log.py
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── job_repo.py
│   │       ├── user_repo.py
│   │       └── asset_repo.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── object_store.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── steps/
│   │   │   └── __init__.py
│   │   └── models/
│   │       └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   ├── workers/
│   │   └── __init__.py
│   └── utils/
│       └── __init__.py
├── assets/
│   ├── fonts/
│   ├── bgm/
│   └── templates/
└── tests/
    └── __init__.py
```

### 2. requirements.txt

```
# Web Framework
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sse-starlette>=2.0.0

# Database
sqlalchemy[asyncio]>=2.0.25
asyncpg>=0.29.0
psycopg2-binary>=2.9.9    # Celery Worker용 동기 DB 드라이버
alembic>=1.13.0

# Redis / Queue
redis>=5.0.0
celery[redis]>=5.3.0

# Object Storage
boto3>=1.34.0

# AI SDKs
google-genai>=1.0.0
openai>=1.12.0

# Content Extraction
beautifulsoup4>=4.12.0
newspaper3k>=0.2.8
youtube-transcript-api>=0.6.0
yt-dlp>=2024.1.0
playwright>=1.41.0

# Video / Image
moviepy>=1.0.3
Pillow>=10.2.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Resilience
tenacity>=8.2.0

# Observability
loguru>=0.7.0
prometheus-client>=0.20.0

# Config
pydantic-settings>=2.1.0
pydantic>=2.6.0

# NLP (Evidence Pack)
scikit-learn>=1.4.0

# Utils
python-multipart>=0.0.6
httpx>=0.27.0
```

### 3. config.py (pydantic-settings)

**파일**: `app/config.py`

```python
class Settings(BaseSettings):
    # AI API Keys
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str

    # Gemini
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MAX_TOKENS: int = 8192

    # OpenAI
    OPENAI_CHAT_MODEL: str = "gpt-4o"
    OPENAI_TTS_MODEL: str = "tts-1-hd"
    OPENAI_TTS_VOICE: str = "alloy"
    OPENAI_IMAGE_MODEL: str = "dall-e-3"
    OPENAI_IMAGE_SIZE: str = "1792x1024"

    # Database
    DATABASE_URL: str              # postgresql+asyncpg://... (API용)
    SYNC_DATABASE_URL: str         # postgresql+psycopg2://... (Celery Worker용)

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3/MinIO
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_ASSETS_BUCKET: str = "video-pipeline-assets"
    S3_OUTPUTS_BUCKET: str = "video-pipeline-outputs"

    # App
    TEMP_DIR: str = "./temp"
    MAX_CONCURRENT_IMAGE_REQUESTS: int = 5
    LOG_LEVEL: str = "INFO"

    # Storage TTL
    OUTPUT_TTL_HOURS: int = 24
    FAILED_TEMP_TTL_HOURS: int = 6

    # Cost
    DEFAULT_COST_BUDGET_USD: float = 2.0
    DALLE_COST_PER_IMAGE: float = 0.08
    TTS_COST_PER_1K_CHARS: float = 0.03

    # Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # Quota
    DEFAULT_DAILY_QUOTA: int = 5

    model_config = SettingsConfigDict(env_file=".env")
```

### 4. Docker Compose

**파일**: `docker-compose.yml`

**7개 서비스** (렌더 워커 분리):
| 서비스 | 이미지 | 포트 | 리소스 | 역할 |
|--------|--------|------|--------|------|
| postgres | postgres:16-alpine | 5432 | - | DB |
| redis | redis:7-alpine | 6379 | - | 큐/캐시/PubSub |
| minio | minio/minio | 9000, 9001 | - | Object Storage |
| api | Dockerfile.api | 8000 | CPU 1.0, Mem 512M | FastAPI 서버 |
| worker-default | Dockerfile.worker | - | CPU 2.0, Mem 2G | 경량 task (추출, AI API, 텍스트) |
| worker-render | Dockerfile.worker | - | CPU 4.0, Mem 8G | Step 5 영상 조립 전용 |
| beat | Dockerfile.worker | - | CPU 0.5, Mem 256M | 주기 작업 스케줄러 |

```
worker-default: celery worker --queues=default --concurrency=4
worker-render:  celery worker --queues=render  --concurrency=1
```

**워커 큐 분리 이유:**
MoviePy/FFmpeg 렌더링은 메모리를 극도로 많이 사용한다.
concurrency=2인 워커에서 영상 2개를 동시에 렌더링하면 OOM으로 컨테이너가 뻗는다.
따라서 렌더 전용 큐를 **concurrency=1**로 분리하여 한 번에 한 영상만 렌더링하도록 강제한다.

- MinIO 초기 버킷: `video-pipeline-assets`, `video-pipeline-outputs`
- 볼륨: `postgres_data`, `minio_data`

### 5. Dockerfile.api (경량)

- Python 3.11-slim 기반
- FastAPI + uvicorn만 포함
- 포트 8000 노출

### 6. Dockerfile.worker (중량)

- Python 3.11 기반
- FFmpeg, MoviePy, Playwright 포함
- Celery worker 실행

### 7. SQLAlchemy 모델 전체

**파일 6개**:

#### `app/db/models/user.py` — User
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID]          # PK
    email: Mapped[str]             # unique, indexed
    hashed_password: Mapped[str]
    role: Mapped[str]              # "user" | "admin", default="user"
    daily_quota: Mapped[int]       # default=5
    created_at: Mapped[datetime]
    # relationship: jobs → VideoJob[]
```

#### `app/db/models/video_job.py` — VideoJob
```python
class VideoJob(Base):
    __tablename__ = "video_jobs"
    id: Mapped[uuid.UUID]                  # PK
    user_id: Mapped[uuid.UUID]             # FK → users.id
    idempotency_key: Mapped[str | None]    # unique, indexed

    # 요청 원본
    topic: Mapped[str]
    style: Mapped[str]
    target_duration_minutes: Mapped[int]
    language: Mapped[str]                  # default="ko"
    tts_voice: Mapped[str]                 # default="alloy"
    additional_instructions: Mapped[str | None]

    # 상태
    phase: Mapped[str]                     # default="queued"
    progress_percent: Mapped[int]          # default=0
    current_step_detail: Mapped[str]
    is_cancelled: Mapped[bool]
    is_sensitive_topic: Mapped[bool]
    requires_human_approval: Mapped[bool]
    human_approved: Mapped[bool | None]
    attempt_count: Mapped[int]
    max_attempts: Mapped[int]              # default=3
    last_completed_step: Mapped[str | None]

    # 비용
    total_cost_usd: Mapped[float]          # default=0.0
    cost_budget_usd: Mapped[float]         # default=2.0

    # 결과
    output_video_key: Mapped[str | None]
    output_thumbnail_key: Mapped[str | None]
    output_script_key: Mapped[str | None]
    total_duration_sec: Mapped[int | None]
    generation_time_sec: Mapped[int | None]

    # 타임스탬프
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]

    # relationships: user, steps, sources, assets, cost_logs
```

#### `app/db/models/job_step.py` — JobStepExecution
```python
class JobStepExecution(Base):
    __tablename__ = "job_steps"
    id: Mapped[uuid.UUID]
    job_id: Mapped[uuid.UUID]              # FK → video_jobs.id
    step_name: Mapped[str]
    status: Mapped[str]                    # pending|running|completed|failed|skipped
    attempt_number: Mapped[int]
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    duration_sec: Mapped[float | None]
    error_message: Mapped[str | None]
    error_traceback: Mapped[str | None]
    output_artifact_keys: Mapped[list[str]]  # JSON, S3 keys
    cost_usd: Mapped[float]
    metadata_json: Mapped[dict | None]       # JSON
```

#### `app/db/models/source.py` — Source
```python
class Source(Base):
    __tablename__ = "sources"
    id: Mapped[uuid.UUID]
    job_id: Mapped[uuid.UUID]
    original_url: Mapped[str]
    canonical_url: Mapped[str | None]
    source_type: Mapped[str]               # blog|news|youtube|custom_text
    domain: Mapped[str | None]
    title: Mapped[str | None]
    author: Mapped[str | None]
    published_at: Mapped[datetime | None]
    content_hash: Mapped[str | None]
    word_count: Mapped[int | None]
    extraction_method: Mapped[str | None]
    content_snapshot_key: Mapped[str | None]
    is_duplicate: Mapped[bool]
    reliability_score: Mapped[float | None]
    relevance_score: Mapped[float | None]
```

#### `app/db/models/asset.py` — Asset
```python
class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[uuid.UUID]
    job_id: Mapped[uuid.UUID]
    asset_type: Mapped[str]    # tts_audio|scene_image|subtitle|bgm|video|thumbnail
    scene_id: Mapped[int | None]
    object_key: Mapped[str]
    file_size_bytes: Mapped[int | None]
    mime_type: Mapped[str | None]
    duration_sec: Mapped[float | None]
    is_fallback: Mapped[bool]
    is_deleted: Mapped[bool]           # default=False, S3에서 삭제된 중간 산출물
    created_at: Mapped[datetime]
```

#### `app/db/models/cost_log.py` — CostLog
```python
class CostLog(Base):
    __tablename__ = "cost_logs"
    id: Mapped[uuid.UUID]
    job_id: Mapped[uuid.UUID]
    step_name: Mapped[str]
    provider: Mapped[str]          # gemini|openai_chat|openai_tts|openai_dalle
    model: Mapped[str]
    input_tokens: Mapped[int | None]
    output_tokens: Mapped[int | None]
    image_count: Mapped[int | None]
    audio_seconds: Mapped[float | None]
    cost_usd: Mapped[float]
    created_at: Mapped[datetime]
```

### 8. Alembic 초기 마이그레이션

- `alembic init alembic`
- `alembic.ini` — DATABASE_URL 연결
- `alembic/env.py` — async 지원 설정
- 초기 마이그레이션 생성: 6개 테이블 (`users`, `video_jobs`, `job_steps`, `sources`, `assets`, `cost_logs`)

### 9. FastAPI main.py + health endpoint

**파일**: `app/main.py`
- FastAPI 앱 생성
- lifespan 이벤트 (DB 연결, Redis 연결)
- CORS 미들웨어
- 라우터 등록
- 구조화 로그 초기화

**파일**: `app/api/routes/health.py`
```
GET /health
→ 서버 + DB + Redis + MinIO + API 키 유효성 + 디스크 체크
→ { status: "healthy", components: { db, redis, minio, ... } }
```

### 10. object_store.py (S3/MinIO 래퍼)

**파일**: `app/storage/object_store.py`

```python
class ObjectStore:
    async def upload(bucket, key, data, content_type) → str
    async def download(bucket, key) → bytes
    async def presigned_url(bucket, key, expires_in=3600) → str
    async def delete(bucket, key) → None
    async def exists(bucket, key) → bool
    async def list_objects(bucket, prefix) → list[str]
```

### 11. DB 세션 관리 (async/sync 분리 — 치명적 호환성 문제 방지)

```python
"""
FastAPI(API 계층)와 Celery(Worker 계층)는 DB 접근 방식이 달라야 한다.

문제:
  Celery는 태생적으로 동기(Synchronous) 워커다.
  Celery Task 안에서 비동기 SQLAlchemy 세션(asyncpg)을 호출하면
  Event Loop 충돌이 발생하거나 Deadlock에 빠진다.

해결: 세션을 두 벌 준비한다.
"""
```

**파일**: `app/db/session.py` (API 계층 전용 - async)
- AsyncSession + asyncpg 드라이버
- FastAPI의 `Depends()`로 주입
- `DATABASE_URL = "postgresql+asyncpg://..."`

```python
# session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

**파일**: `app/db/sync_session.py` (Celery Worker 전용 - sync)
- Session + psycopg2 드라이버
- Celery task 함수 내부에서 직접 사용
- `SYNC_DATABASE_URL = "postgresql+psycopg2://..."`

```python
# sync_session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

sync_engine = create_engine(settings.SYNC_DATABASE_URL)
SyncSessionLocal = sessionmaker(sync_engine)

def get_sync_db() -> Generator[Session, None, None]:
    with SyncSessionLocal() as session:
        yield session
```

**절대 규칙:**
- API 라우트 → `session.py`의 AsyncSession만 사용
- Celery task → `sync_session.py`의 SyncSession만 사용
- **절대로 Celery task 안에서 AsyncSession을 import하지 말 것**

---

## 선행 조건
- 없음 (첫 번째 Phase)

## 완료 기준
- [ ] 전체 디렉토리 구조 생성 완료
- [ ] `requirements.txt` 작성 및 의존성 설치 가능
- [ ] `.env.example` 작성, `config.py`에서 설정 로드 가능
- [ ] `docker-compose up`으로 Postgres + Redis + MinIO 기동 가능
- [ ] SQLAlchemy 모델 6개 정의 완료
- [ ] Alembic 초기 마이그레이션 생성 및 실행 가능
- [ ] `GET /health` 정상 응답
- [ ] `ObjectStore` S3/MinIO 업로드/다운로드/presigned URL 동작
