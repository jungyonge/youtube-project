# Phase 1: 프로젝트 뼈대 + 인프라

## 목표
프로젝트 디렉토리 구조, 의존성, 설정, Docker 인프라, DB 모델, 오브젝트 스토리지 래퍼 등
서비스의 기반을 구축한다.

---

## 구현 항목

### 1. 디렉토리 구조 생성

```
ai-video-pipeline/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── docker-compose.yml            # Redis + Postgres + MinIO + API + Worker + Beat
├── Dockerfile.api                # 경량: FastAPI + uvicorn
├── Dockerfile.worker             # 중량: FFmpeg, MoviePy, Playwright
│
├── alembic/                      # DB 마이그레이션
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI 엔트리포인트
│   ├── config.py                 # pydantic-settings
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_handler.py        # JWT 생성/검증
│   │   ├── dependencies.py       # get_current_user, require_admin
│   │   └── password.py           # bcrypt 해싱
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # POST /auth/register, /auth/login
│   │   │   ├── video.py          # POST /api/v1/videos
│   │   │   ├── status.py         # GET /api/v1/videos/{job_id}
│   │   │   ├── stream.py         # GET /api/v1/videos/{job_id}/stream (SSE)
│   │   │   ├── admin.py          # GET /admin/jobs, POST /admin/jobs/{id}/cancel
│   │   │   └── health.py         # GET /health
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── request.py        # VideoGenerationRequest
│   │   │   └── response.py       # JobStatusResponse
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── idempotency.py    # 중복 요청 방지
│   │       ├── rate_limit.py     # 사용자별 요청 제한
│   │       └── trace.py          # 요청별 trace_id 주입
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py            # async SQLAlchemy session (API용)
│   │   ├── sync_session.py       # sync SQLAlchemy session (Celery Worker용)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py           # User
│   │   │   ├── video_job.py      # VideoJob
│   │   │   ├── job_step.py       # JobStepExecution
│   │   │   ├── source.py         # Source, SourceSnapshot
│   │   │   ├── asset.py          # Asset (object key, type, size)
│   │   │   └── cost_log.py       # CostLog (API별 토큰/비용 기록)
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── job_repo.py
│   │       ├── user_repo.py
│   │       └── asset_repo.py
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── object_store.py       # S3/MinIO 래퍼 (upload, download, presigned_url)
│   │   └── artifact_registry.py  # job별 산출물 등록/조회/삭제
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Celery task 체인 오케스트레이션
│   │   ├── steps/
│   │   │   ├── __init__.py
│   │   │   ├── step1_extract.py          # 콘텐츠 추출
│   │   │   ├── step1b_normalize.py       # 소스 정규화 + 중복 제거
│   │   │   ├── step1c_evidence_pack.py   # 청킹 + 랭킹 + 근거팩 생성
│   │   │   ├── step2_research.py         # Gemini 대본 생성
│   │   │   ├── step3_review.py           # ChatGPT 대본 검수
│   │   │   ├── step3b_policy_review.py   # 민감 주제 정책 검수
│   │   │   ├── step3c_human_gate.py      # Human approval 게이트
│   │   │   ├── step4a_tts.py             # ChatGPT TTS
│   │   │   ├── step4b_images.py          # DALL-E + 다양한 asset 생성
│   │   │   ├── step4c_subtitles.py       # SRT 자막
│   │   │   ├── step4d_bgm.py             # BGM
│   │   │   └── step5_assemble.py         # 영상 조립 (sync worker)
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── script.py             # FullScript, ScriptScene, SceneClaim
│   │       ├── assets.py             # AudioAsset, ImageAsset, SceneAssetPlan
│   │       ├── evidence.py           # EvidencePack, SourceChunk, RankedEvidence
│   │       ├── job.py                # JobPhase, JobResult
│   │       └── render_manifest.py    # RenderManifest (씬별 렌더 지시서)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── gemini_client.py
│   │   ├── openai_client.py
│   │   ├── content_extractor.py
│   │   └── cost_tracker.py       # API 호출별 비용 기록 + 예산 초과 감지
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   └── periodic_tasks.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── prompts.py
│       ├── video_utils.py
│       ├── file_manager.py
│       └── retry.py              # tenacity 재시도 데코레이터
│
├── assets/
│   ├── fonts/
│   ├── bgm/
│   └── templates/                # 인트로/아웃트로, quote_card, chart 템플릿
│
└── tests/
    ├── __init__.py
    ├── conftest.py               # fixture: DB, Redis, MinIO mock
    ├── test_extract.py
    ├── test_normalize.py
    ├── test_evidence_pack.py
    ├── test_gemini.py
    ├── test_openai.py
    ├── test_policy_review.py
    ├── test_pipeline.py
    ├── test_render.py
    ├── test_cost_guardrail.py
    └── test_idempotency.py
```

### 2. requirements.txt 작성

기술 스택에 명시된 모든 의존성 포함:
- FastAPI, uvicorn, SQLAlchemy 2.0 (async), Alembic
- Redis, Celery, sse-starlette
- psycopg2-binary (Celery Worker용 동기 DB 드라이버)
- MoviePy, FFmpeg
- BeautifulSoup4, newspaper3k, youtube-transcript-api, yt-dlp, Playwright
- google-genai (Gemini), openai (ChatGPT/DALL-E/TTS)
- Pillow, tenacity, python-jose, passlib[bcrypt]
- loguru, prometheus-client
- pydantic-settings

### 3. config.py + .env.example

```python
# app/config.py
"""
pydantic-settings 기반 설정 관리.
.env 파일에서 환경변수 로드.
"""
```

**`.env.example`** 포함 항목:
- AI API Keys (GEMINI_API_KEY, OPENAI_API_KEY)
- Gemini/OpenAI 모델 설정
- DATABASE_URL (asyncpg), SYNC_DATABASE_URL (psycopg2)
- REDIS_URL
- S3/MinIO 설정
- App 설정 (TEMP_DIR, LOG_LEVEL 등)
- Storage TTL, Cost 단가
- Auth (JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES)
- Quota (DEFAULT_DAILY_QUOTA)

### 4. Docker Compose

```yaml
"""
서비스 컨테이너 7개 (렌더 워커 분리):

  postgres:
    image: postgres:16-alpine
    포트: 5432
    볼륨: postgres_data

  redis:
    image: redis:7-alpine
    포트: 6379

  minio:
    image: minio/minio
    포트: 9000 (API), 9001 (Console)
    볼륨: minio_data
    초기 버킷: video-pipeline-assets, video-pipeline-outputs

  api:
    Dockerfile.api (경량)
    포트: 8000
    resources: cpus 1.0, memory 512M
    의존: postgres, redis, minio

  worker-default:
    Dockerfile.worker
    celery worker --queues=default --concurrency=4
    resources: cpus 2.0, memory 2G
    역할: 콘텐츠 추출, AI API 호출, 텍스트 처리 등 경량 task
    의존: postgres, redis, minio

  worker-render:
    Dockerfile.worker
    celery worker --queues=render --concurrency=1
    resources: cpus 4.0, memory 8G
    역할: 오직 Step 5 영상 조립(FFmpeg/MoviePy)만 전담
    concurrency=1로 제한하여 OOM 방어
    (8GB RAM을 한 영상이 독점 사용)
    의존: postgres, redis, minio

  beat:
    Dockerfile.worker 재사용
    celery beat
    resources: cpus 0.5, memory 256M

워커 큐 분리 이유:
  텍스트 추출이나 대본 생성은 메모리를 적게 쓰지만,
  MoviePy/FFmpeg 렌더링은 메모리를 극도로 많이 사용한다.
  concurrency=2인 워커에서 영상 2개를 동시에 렌더링하면
  8GB RAM으로는 OOM으로 컨테이너가 뻗는다.
  따라서 렌더 전용 큐를 concurrency=1로 분리하여
  한 번에 한 영상만 렌더링하도록 강제한다.
"""
```

### 5. Dockerfile.api + Dockerfile.worker

- **Dockerfile.api**: 경량 이미지 (FastAPI + uvicorn)
- **Dockerfile.worker**: 중량 이미지 (FFmpeg, MoviePy, Playwright 포함)

### 6. SQLAlchemy 모델 전체

```python
# db/models/user.py
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    role: Mapped[str] = mapped_column(default="user")  # "user" | "admin"
    daily_quota: Mapped[int] = mapped_column(default=5)  # 일일 영상 생성 제한
    created_at: Mapped[datetime]
    jobs: Mapped[list["VideoJob"]] = relationship(back_populates="user")


# db/models/video_job.py
class VideoJob(Base):
    """
    서비스의 핵심 엔티티. 파이프라인 상태뿐 아니라 서비스 상태를 표현.
    누가 만들었는지, 몇 번 재시도했는지, 취소 가능한지, 비용은 얼마인지.
    """
    __tablename__ = "video_jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    idempotency_key: Mapped[str | None] = mapped_column(unique=True, index=True)

    # 요청 원본
    topic: Mapped[str]
    style: Mapped[str]
    target_duration_minutes: Mapped[int]
    language: Mapped[str] = mapped_column(default="ko")
    tts_voice: Mapped[str] = mapped_column(default="alloy")
    additional_instructions: Mapped[str | None]

    # 상태
    phase: Mapped[str] = mapped_column(default="queued")
    progress_percent: Mapped[int] = mapped_column(default=0)
    current_step_detail: Mapped[str] = mapped_column(default="")
    is_cancelled: Mapped[bool] = mapped_column(default=False)
    is_sensitive_topic: Mapped[bool] = mapped_column(default=False)
    requires_human_approval: Mapped[bool] = mapped_column(default=False)
    human_approved: Mapped[bool | None] = mapped_column(default=None)
    attempt_count: Mapped[int] = mapped_column(default=0)
    max_attempts: Mapped[int] = mapped_column(default=3)
    last_completed_step: Mapped[str | None]  # resume 시 이 단계 다음부터 재개

    # 비용
    total_cost_usd: Mapped[float] = mapped_column(default=0.0)
    cost_budget_usd: Mapped[float] = mapped_column(default=2.0)  # 기본 예산 $2

    # 결과
    output_video_key: Mapped[str | None]      # S3 object key
    output_thumbnail_key: Mapped[str | None]
    output_script_key: Mapped[str | None]
    total_duration_sec: Mapped[int | None]
    generation_time_sec: Mapped[int | None]

    # 타임스탬프
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]

    # 관계
    user: Mapped["User"] = relationship(back_populates="jobs")
    steps: Mapped[list["JobStepExecution"]] = relationship(back_populates="job")
    sources: Mapped[list["Source"]] = relationship(back_populates="job")
    assets: Mapped[list["Asset"]] = relationship(back_populates="job")
    cost_logs: Mapped[list["CostLog"]] = relationship(back_populates="job")


# db/models/job_step.py
class JobStepExecution(Base):
    """
    각 파이프라인 Step의 실행 기록.
    retry from step, 장애 분석, 성능 추적에 필수.
    """
    __tablename__ = "job_steps"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    step_name: Mapped[str]        # "extract", "normalize", "evidence_pack", "research", "review", "policy_review", etc.
    status: Mapped[str]           # "pending" | "running" | "completed" | "failed" | "skipped"
    attempt_number: Mapped[int] = mapped_column(default=1)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]
    duration_sec: Mapped[float | None]
    error_message: Mapped[str | None]
    error_traceback: Mapped[str | None]
    output_artifact_keys: Mapped[list[str]] = mapped_column(default=list)  # S3 keys
    cost_usd: Mapped[float] = mapped_column(default=0.0)
    metadata_json: Mapped[dict | None]  # step별 추가 정보 (토큰수, 이미지수 등)

    job: Mapped["VideoJob"] = relationship(back_populates="steps")


# db/models/source.py
class Source(Base):
    """소스 URL 메타데이터 + 정규화 정보"""
    __tablename__ = "sources"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    original_url: Mapped[str]
    canonical_url: Mapped[str | None]     # 정규화된 URL
    source_type: Mapped[str]              # blog, news, youtube, custom_text
    domain: Mapped[str | None]
    title: Mapped[str | None]
    author: Mapped[str | None]
    published_at: Mapped[datetime | None]
    content_hash: Mapped[str | None]      # 중복 감지용
    word_count: Mapped[int | None]
    extraction_method: Mapped[str | None]
    content_snapshot_key: Mapped[str | None]  # S3에 원문 스냅샷 저장
    is_duplicate: Mapped[bool] = mapped_column(default=False)
    reliability_score: Mapped[float | None]  # 도메인 기반 신뢰도
    relevance_score: Mapped[float | None]    # 주제 관련성

    job: Mapped["VideoJob"] = relationship(back_populates="sources")


# db/models/asset.py
class Asset(Base):
    """Job에서 생성된 모든 산출물 (이미지, 오디오, 자막, 영상)"""
    __tablename__ = "assets"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    asset_type: Mapped[str]       # "tts_audio", "scene_image", "subtitle", "bgm", "video", "thumbnail"
    scene_id: Mapped[int | None]  # 씬별 asset인 경우
    object_key: Mapped[str]       # S3 key
    file_size_bytes: Mapped[int | None]
    mime_type: Mapped[str | None]
    duration_sec: Mapped[float | None]  # 오디오/영상인 경우
    is_fallback: Mapped[bool] = mapped_column(default=False)  # placeholder로 대체된 경우
    is_deleted: Mapped[bool] = mapped_column(default=False)   # S3에서 삭제됨 (중간 산출물 정리)
    created_at: Mapped[datetime]

    job: Mapped["VideoJob"] = relationship(back_populates="assets")


# db/models/cost_log.py
class CostLog(Base):
    """API 호출별 비용 추적. 예산 초과 감지 + 월별 리포트용."""
    __tablename__ = "cost_logs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_jobs.id"), index=True)
    step_name: Mapped[str]
    provider: Mapped[str]         # "gemini", "openai_chat", "openai_tts", "openai_dalle"
    model: Mapped[str]
    input_tokens: Mapped[int | None]
    output_tokens: Mapped[int | None]
    image_count: Mapped[int | None]
    audio_seconds: Mapped[float | None]
    cost_usd: Mapped[float]
    created_at: Mapped[datetime]

    job: Mapped["VideoJob"] = relationship(back_populates="cost_logs")
```

### 7. Alembic 초기 마이그레이션

- `alembic init` 설정
- 모델 6개에 대한 초기 마이그레이션 생성

### 8. FastAPI main.py + health endpoint

- FastAPI 엔트리포인트
- `GET /health` (서버 + DB + Redis + MinIO + API 키 유효성 + 디스크)

### 9. object_store.py (S3/MinIO 래퍼)

**파일**: `app/storage/object_store.py`
- upload, download, presigned_url
- S3/MinIO 호환 래퍼

---

## DB 세션 분리 전략

```python
"""
FastAPI(API 계층)와 Celery(Worker 계층)는 DB 접근 방식이 달라야 한다.

문제:
  Celery는 태생적으로 동기(Synchronous) 워커다.
  Celery Task 안에서 비동기 SQLAlchemy 세션(asyncpg)을 호출하면
  Event Loop 충돌이 발생하거나 Deadlock에 빠진다.

해결: 세션을 두 벌 준비한다.

1. session.py (API 계층 전용 - async)
   - AsyncSession + asyncpg 드라이버
   - FastAPI의 Depends()로 주입
   - DATABASE_URL = "postgresql+asyncpg://..."

2. sync_session.py (Celery Worker 전용 - sync)
   - Session + psycopg2 드라이버 (또는 psycopg)
   - Celery task 함수 내부에서 직접 사용
   - SYNC_DATABASE_URL = "postgresql+psycopg2://..."

규칙:
  - API 라우트 → session.py의 AsyncSession만 사용
  - Celery task → sync_session.py의 SyncSession만 사용
  - 절대로 Celery task 안에서 AsyncSession을 import하지 말 것
  - requirements.txt에 psycopg2-binary 추가
"""
```

---

## 선행 조건
- 없음 (첫 번째 Phase)

## 완료 기준
- [ ] 전체 디렉토리 구조 생성 완료
- [ ] `requirements.txt` 작성 및 의존성 설치 가능
- [ ] `.env.example` 작성, `config.py`에서 설정 로드 가능
- [ ] `docker-compose up`으로 Postgres + Redis + MinIO + API + Worker + Beat 기동 가능
- [ ] Dockerfile.api + Dockerfile.worker 빌드 가능
- [ ] SQLAlchemy 모델 6개 정의 완료 (User, VideoJob, JobStepExecution, Source, Asset, CostLog)
- [ ] Alembic 초기 마이그레이션 생성 및 실행 가능
- [ ] `GET /health` 정상 응답
- [ ] `ObjectStore` S3/MinIO 업로드/다운로드/presigned URL 동작
- [ ] DB 세션 분리 (async/sync) 설정 완료
