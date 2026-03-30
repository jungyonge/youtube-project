# AI Video Generation Service - 프로덕션 레벨 구축 요청

## 프로젝트 개요

사용자가 주제(정치, 주식, 기술 등)와 참고 자료(블로그 URL, 뉴스 URL, 유튜브 링크)를 입력하면,
AI가 자동으로 10~15분 분량의 유튜브 영상(MP4)을 생성하는 Python 기반 **서비스**를 구축해줘.

단순 파이프라인이 아니라, 인증/인가, 비용 제어, 정책 검수, 장애 복구, 작업 취소/재시도가
가능한 **운영 가능한 서비스 백엔드**로 설계한다.

## 사용 가능한 AI 서비스

1. **Gemini API** (Google) - 리서치 + 대본 생성 (1M 토큰 컨텍스트 활용)
2. **ChatGPT API** (OpenAI) - 대본 검수, TTS 음성 생성, DALL-E 3 이미지 생성
3. **Claude Code** (Anthropic) - 이 프로젝트 자체를 개발하는 도구 (API 호출 대상 아님)

## 기술 스택

- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **DB (메타데이터 영속 저장)**: PostgreSQL + SQLAlchemy 2.0 (async) + Alembic (마이그레이션)
- **Cache / Queue / PubSub**: Redis (Celery 브로커, 휘발성 상태, SSE pub/sub 전용)
- **Object Storage (산출물)**: MinIO (S3 호환, 로컬 개발) → 프로덕션 시 AWS S3 교체
- **Task Queue**: Celery + Redis (큐 2개 분리: default + render)
- **Realtime**: sse-starlette (진행 상태 실시간 푸시)
- **Sync DB (Worker 전용)**: psycopg2 (Celery 워커는 동기 DB 커넥션 사용)
- **Video Processing**: MoviePy, FFmpeg
- **Content Extraction**: BeautifulSoup4, newspaper3k, youtube-transcript-api, yt-dlp (fallback), Playwright (동적 페이지)
- **AI SDKs**: google-genai (Gemini), openai (ChatGPT/DALL-E/TTS)
- **Image Processing**: Pillow
- **Resilience**: tenacity (재시도/백오프)
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Observability**: loguru (구조화 로그) + prometheus-client (메트릭)
- **Config**: pydantic-settings + .env

### 저장소 삼분할 원칙
```
Redis    = 휘발성 (큐, 캐시, pub/sub, 실시간 상태)
Postgres = 진실의 원천 (유저, Job, Step, 비용, 에러 로그, 소스 메타)
MinIO/S3 = 산출물 저장 (이미지, 오디오, 영상, 대본 JSON)
```
파일 경로 대신 **object key + presigned URL**로 산출물을 관리한다.
로컬 파일시스템은 **개발 환경 전용**으로만 허용한다.

---

## DB 세션 분리 전략 (치명적 호환성 문제 방지)

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

## 프로젝트 구조

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

---

## 데이터 모델 상세 설계

### DB 모델 (PostgreSQL)

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

### 파이프라인 모델 (Pydantic - 파이프라인 내부 통신용)

```python
# pipeline/models/evidence.py

class SourceChunk(BaseModel):
    """소스를 문단/구간 단위로 청킹한 결과"""
    source_id: str
    chunk_index: int
    text: str
    timestamp_start: float | None = None  # YouTube용
    timestamp_end: float | None = None

class RankedEvidence(BaseModel):
    """랭킹된 근거 조각"""
    chunk: SourceChunk
    relevance_score: float        # 주제 관련성 (0~1)
    recency_score: float          # 최신성 (0~1)
    reliability_score: float      # 출처 신뢰도 (0~1)
    composite_score: float        # 종합 점수
    is_duplicate: bool = False

class EvidencePack(BaseModel):
    """
    대본 생성 모델에 전달할 근거 팩.
    '모든 ExtractedContent를 한 번에 밀어넣기' 대신,
    정규화 → 중복 제거 → 청킹 → 랭킹을 거친 압축 결과물.
    """
    topic: str
    total_sources: int
    deduplicated_sources: int
    ranked_chunks: list[RankedEvidence]   # 점수 순 정렬
    key_claims: list[str]                 # 핵심 주장 요약 (모델 전처리)
    source_metadata: list[dict]           # 출처별 메타 (domain, date, author)


# pipeline/models/script.py

class SceneClaim(BaseModel):
    """씬 내 개별 주장과 근거 매핑"""
    claim_text: str
    claim_type: Literal["fact", "inference", "opinion"]
    evidence_source_id: str       # 근거 출처 Source.id
    evidence_quote: str | None    # 직접 인용 (있을 경우)
    confidence: float             # 근거 확신도 (0~1)

class SceneCitation(BaseModel):
    """화면에 표시할 출처 정보"""
    source_domain: str
    source_title: str
    display_text: str             # "출처: 조선일보 (2026.03.28)"

class SceneAssetPlan(BaseModel):
    """
    씬별 최적 에셋 전략. DALL-E 이미지만이 아니라 다양한 유형 혼합.
    """
    asset_type: Literal[
        "generated_image",    # DALL-E 생성 이미지
        "quote_card",         # 인용문 카드 (템플릿 기반)
        "data_chart",         # 차트/그래프 (matplotlib/Pillow)
        "timeline_card",      # 타임라인 카드
        "title_card",         # 제목/섹션 구분 카드
        "web_capture",        # 원본 웹페이지 스크린샷 (Playwright)
        "text_overlay",       # 핵심 키워드 강조 화면
        "split_screen",       # 비교 화면 (좌/우)
    ]
    generation_prompt: str | None = None  # generated_image 전용
    template_id: str | None = None        # 카드 템플릿 ID
    template_data: dict | None = None     # 템플릿에 채울 데이터
    fallback_strategy: Literal["placeholder", "text_overlay", "skip"] = "placeholder"
    priority: int = 1                     # 예산 부족 시 낮은 priority부터 생략

class ScriptScene(BaseModel):
    scene_id: int
    section: str                          # "hook", "intro", "body_1", ..., "conclusion"
    purpose: str                          # 이 씬의 목적 (한 줄)
    duration_target_sec: int
    duration_actual_sec: int | None = None  # TTS 실측 후 업데이트
    narration: str
    subtitle_chunks: list[str] = []       # 자막 분절 (20자 단위)
    
    # 에셋 계획 (다양한 유형)
    asset_plan: list[SceneAssetPlan]
    
    # 전환 효과
    transition_in: str | None = None      # 이 씬으로 들어올 때
    transition_out: str | None = None     # 이 씬에서 나갈 때
    
    # 근거/정책
    claims: list[SceneClaim] = []
    citations: list[SceneCitation] = []
    policy_flags: list[str] = []          # ["contains_stock_prediction", "mentions_politician"]
    
    # 키워드
    keywords: list[str] = []

class FullScript(BaseModel):
    title: str
    subtitle: str
    total_duration_sec: int
    thumbnail_prompt: str
    scenes: list[ScriptScene]
    tags: list[str]
    description: str
    
    # 정책 메타
    overall_sensitivity: Literal["low", "medium", "high"] = "low"
    requires_human_approval: bool = False
    policy_warnings: list[str] = []


# pipeline/models/render_manifest.py

class RenderManifest(BaseModel):
    """
    영상 조립기(step5)에 전달하는 최종 렌더 지시서.
    대본 모델과 렌더 모델을 분리하여 관심사를 격리.
    """
    job_id: str
    total_scenes: int
    resolution: str = "1920x1080"
    fps: int = 30
    codec: str = "libx264"
    crf: int = 23
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    
    scenes: list["RenderSceneInstruction"]
    bgm_object_key: str | None
    bgm_volume_db: float = -20.0
    subtitle_srt_key: str | None
    burn_subtitles: bool = True
    intro_template_key: str | None = None
    outro_template_key: str | None = None

class RenderSceneInstruction(BaseModel):
    scene_id: int
    audio_object_key: str
    audio_duration_sec: float
    image_object_key: str
    ken_burns_effect: Literal["zoom_in", "zoom_out", "pan_left", "pan_right"] 
    transition_in: str | None
    transition_out: str | None
    silence_after_sec: float = 0.5
```

### 요청/응답 스키마 (API)

```python
# api/schemas/request.py
class VideoGenerationRequest(BaseModel):
    topic: str
    sources: list[SourceInput]            # 최소 1개, 최대 10개
    style: VideoStyle = VideoStyle.INFORMATIVE
    target_duration_minutes: int = 12     # 10~15
    language: str = "ko"
    tts_voice: str = "alloy"
    include_subtitles: bool = True
    include_bgm: bool = True
    additional_instructions: str | None = None
    cost_budget_usd: float | None = None  # 사용자 지정 예산 (기본값 $2)
    auto_approve: bool = True             # False면 대본 단계에서 승인 대기
    idempotency_key: str | None = None    # 중복 요청 방지 키

# api/schemas/response.py
class JobStatusResponse(BaseModel):
    job_id: str
    phase: str
    progress_percent: int
    current_step_detail: str
    is_cancelled: bool
    requires_human_approval: bool
    human_approved: bool | None
    total_cost_usd: float
    cost_budget_usd: float
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    download_url: str | None = None       # presigned URL (완료 시)
    script_preview_url: str | None = None # 대본 미리보기 presigned URL
```

---

## 파이프라인 Step 상세 명세

### Step 1: 콘텐츠 추출 (step1_extract.py)

Strategy 패턴, 기존과 동일.
youtube-transcript-api 실패 시 yt-dlp fallback 포함.

### Step 1b: 소스 정규화 + 중복 제거 (step1b_normalize.py)

```python
"""
추출된 소스를 그대로 모델에 넣지 않는다.
정규화 → 중복 제거 → 메타데이터 보강을 거친다.

1. canonical URL 생성
   - UTM 파라미터 제거
   - www/non-www 통일
   - URL fragment 제거
   
2. content_hash 생성
   - 본문 텍스트의 simhash 또는 md5
   - 같은 hash = 같은 기사의 재배포 → is_duplicate=True 마킹

3. 메타 보강
   - domain 추출 → 도메인 기반 reliability_score 부여
     (주요 언론사 0.9, 블로그 0.5, 알 수 없음 0.3)
   - published_at 파싱 및 정규화
   - 오래된 기사(30일 이상) 페널티

4. 광고성/홍보성 필터
   - 광고 키워드 비율이 20% 이상이면 warning flag

결과: Source 테이블에 정규화 정보 저장
"""
```

### Step 1c: 근거팩 생성 (step1c_evidence_pack.py)

```python
"""
'모든 소스를 한 번에 모델에 밀어넣기' 대신,
핵심 근거만 추출하여 EvidencePack을 만든다.

1. 청킹 (Chunking)
   - 블로그/뉴스: 문단 단위 (300~500자)
   - YouTube: 타임스탬프 구간 단위 (30초~1분)
   
2. 랭킹 (Ranking)
   각 청크에 아래 점수 부여:
   - relevance_score: topic과의 코사인 유사도 (TF-IDF 기반, 라이브러리: scikit-learn)
   - recency_score: 최신일수록 높음 (exp decay, 반감기 7일)
   - reliability_score: 출처 도메인 신뢰도
   - composite_score = 0.5*relevance + 0.3*recency + 0.2*reliability
   
3. 상위 N개 청크 선택
   - 기본값: 상위 30개 청크
   - Gemini 컨텍스트에 여유가 있어도 노이즈 줄이기 위해 제한

4. 핵심 주장 요약
   - Gemini flash로 빠르게 "이 소스들의 핵심 주장 5~10개" 추출
   - 대본 생성 시 구조 잡는 데 활용

결과: EvidencePack 생성 → step2로 전달
"""
```

### Step 2: Gemini 대본 생성 (step2_research.py)

```python
SCRIPT_GENERATION_PROMPT = """
당신은 한국 유튜브 콘텐츠 전문 작가입니다.
아래 '근거팩(Evidence Pack)'을 분석하여 {target_duration}분 분량의 영상 대본을 작성하세요.

## 입력 정보
- 주제: {topic}
- 영상 스타일: {style}
- 추가 지시사항: {additional_instructions}

## 근거팩
### 핵심 주장 요약
{key_claims}

### 상위 근거 청크 (중요도 순)
{ranked_chunks_formatted}

### 출처 메타데이터
{source_metadata_formatted}

## 대본 작성 규칙

1. **구조**
   - Hook (0:00~0:30): 강렬한 오프닝
   - Intro (0:30~1:00): 주제 소개
   - Body (1:00~{body_end}): 3~5개 핵심 포인트
   - Conclusion ({body_end}~{total}): 요약 + CTA

2. **나레이션 톤**
   - 자연스러운 한국어 구어체
   - 번역체 절대 금지
   - 한 문장 40자 이내 권장 (TTS 최적화)

3. **씬 분할**
   - 씬당 30~60초, 총 {min_scenes}~{max_scenes}개

4. **에셋 전략 (중요)**
   모든 씬을 이미지 생성으로 채우지 말 것.
   씬의 내용에 따라 최적 asset_type을 선택:
   - 수치/통계 → "data_chart"
   - 인용/발언 → "quote_card"  
   - 시간 순서 → "timeline_card"
   - 비교/대조 → "split_screen"
   - 분위기/장면 묘사 → "generated_image"
   - 섹션 전환 → "title_card"
   전체 씬 중 generated_image는 최대 50%.
   나머지는 카드/차트/텍스트 오버레이로 다양하게 구성.

5. **근거 매핑 (claims)**
   각 씬의 모든 주장에 대해:
   - claim_text: 주장 내용
   - claim_type: "fact" | "inference" | "opinion" 반드시 구분
   - evidence_source_id: 근거 출처 ID
   - confidence: 근거 확신도 (0~1)

6. **정책 플래그**
   아래에 해당하면 policy_flags에 추가:
   - 주식/투자 예측 → "contains_stock_prediction"
   - 특정 정치인 언급 → "mentions_politician"  
   - 건강/의료 조언 → "contains_medical_advice"
   - 논란성 주장 → "controversial_claim"

7. **민감도 판정**
   전체 대본의 overall_sensitivity 판정:
   - "low": 기술, 교육, 일반 정보
   - "medium": 경제 전망, 사회 이슈
   - "high": 정치 논쟁, 투자 조언, 의료
   "high"이면 requires_human_approval = true

8. **팩트 체크**
   근거팩에 없는 내용 창작 금지.
   추정은 반드시 claim_type="inference"로 표시.

## 출력 형식
FullScript JSON 스키마를 정확히 따를 것.
"""
```

### Step 3: ChatGPT 대본 검수 (step3_review.py)

기존과 동일 + 아래 추가:

```
추가 검수 항목:
- claims의 claim_type이 적절한지 (fact인데 근거 없으면 inference로 수정)
- policy_flags 누락 확인
- overall_sensitivity 재판정
- 투자 조언처럼 보이는 표현 → "이 영상은 투자 권유가 아닙니다" disclaimer 씬 자동 추가
```

### Step 3b: 정책 검수 (step3b_policy_review.py)

```python
"""
정치, 주식, 시사 이슈는 별도 compliance review를 거친다.

검수 대상:
1. policy_flags가 1개 이상인 모든 씬

검수 내용:
- 주식: "~할 것이다", "반드시 오른다" 같은 단정적 투자 표현 → 
  "~할 가능성이 있습니다" 등 완화 표현으로 수정
  + 영상 시작에 투자 면책 조항(disclaimer) 씬 삽입

- 정치: 특정 정치인/정당에 대한 일방적 지지/비난 → 
  반대 관점도 포함하도록 씬 추가 요청
  + 명예훼손 소지 표현 제거

- 의료: "~하면 낫는다" 같은 의료 조언 → 
  "전문가와 상담하세요" disclaimer 추가

- 모든 민감 씬: fact/inference/opinion 라벨이 나레이션에 반영되는지 확인
  (예: "전문가들은 ~로 분석합니다" vs "확실히 ~입니다")

구현:
- GPT-4o에게 policy review 전용 프롬프트로 검수 요청
- 수정된 대본 + 삽입된 disclaimer 씬 반환
- policy_flags 기반 자동 처리 + 로깅
"""
```

### Step 3c: Human Approval 게이트 (step3c_human_gate.py)

```python
"""
overall_sensitivity == "high" 이거나,
사용자가 auto_approve=False로 요청한 경우:

1. 대본 JSON을 S3에 저장하고 presigned URL 생성
2. job.phase = "awaiting_approval"로 변경
3. SSE로 "승인 필요" 이벤트 전송
4. 파이프라인 일시 중지 (Celery task 종료)
5. 사용자가 POST /api/v1/videos/{job_id}/approve 호출 시 재개
6. 사용자가 POST /api/v1/videos/{job_id}/reject 호출 시 종료

timeout: 24시간 내 미승인 → 자동 취소
"""
```

### Step 4a~4d: 자산 생성

기존과 동일 + 아래 변경:

**Step 4b 이미지 생성 확장:**
```python
"""
SceneAssetPlan의 asset_type에 따라 분기:

- "generated_image": DALL-E 3 API 호출 (기존)
- "quote_card": Pillow + 템플릿으로 인용문 카드 생성
    - assets/templates/quote_card.json 기반
    - 배경색, 폰트, 레이아웃 자동 적용
- "data_chart": matplotlib로 차트 이미지 생성
    - template_data에서 데이터 파싱
    - 한글 폰트 적용 (NanumGothic)
- "timeline_card": Pillow + 템플릿으로 타임라인 카드
- "title_card": Pillow로 제목 카드
- "web_capture": Playwright screenshot (원본 URL)
- "text_overlay": Pillow로 키워드 강조 화면
- "split_screen": Pillow로 좌/우 비교 이미지 합성

모든 결과는 1920x1080으로 리사이즈.
생성된 이미지는 S3 업로드 후 Asset 테이블에 등록.
"""
```

### Step 5: 영상 조립 (step5_assemble.py)

```python
"""
RenderManifest를 입력받아 최종 영상을 조립한다.
이 Step은 CPU 바운드이므로 render 큐의 sync worker task로 실행.
concurrency=1이므로 한 번에 한 영상만 렌더링.

@celery_app.task(queue='render', bind=True)
def assemble_video_task(self, ...):

조립 순서:
1. S3에서 모든 asset 다운로드 → 로컬 temp
2. MoviePy로 씬별 클립 생성
3. Ken Burns 효과 적용 (RenderSceneInstruction 기반)
4. 전환 효과 적용
5. 나레이션 오디오 합성
6. BGM 믹싱 (-20dB)
7. 자막 burn-in
8. 인트로/아웃트로
9. FFmpeg 최종 인코딩: H.264 1080p 30fps
10. 최종 MP4를 S3 업로드
11. 로컬 temp 즉시 삭제
12. 중간 산출물 S3 정리 (아래 참조)

FFmpeg 실시간 진행률 추적 (중요):
  MoviePy/FFmpeg가 동기적으로 렌더링하는 동안
  코드가 블로킹되어 Redis에 진행률을 업데이트할 수 없다.
  프론트에서 15분 동안 "렌더링 중..." 에서 멈추는 문제 발생.

  해결:
  - FFmpeg을 subprocess.Popen으로 직접 실행하고
    -progress pipe:1 옵션으로 진행 상황을 stdout으로 출력
  - 또는 MoviePy의 logger='bar' 대신 커스텀 proglog 콜백 연결
  - 별도 스레드에서 stdout을 읽으면서 10초마다 Redis PUBLISH
  - progress_percent 계산: (처리된_프레임 / 총_프레임) * 100
  
  구현 패턴:
    import subprocess, threading

    def run_ffmpeg_with_progress(cmd, job_id, total_duration_sec):
        proc = subprocess.Popen(
            cmd + ['-progress', 'pipe:1', '-nostats'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        
        def read_progress():
            current_time = 0
            for line in proc.stdout:
                line = line.decode().strip()
                if line.startswith('out_time_ms='):
                    current_time = int(line.split('=')[1]) / 1_000_000
                    percent = min(int(current_time / total_duration_sec * 100), 99)
                    # 10초마다 Redis PUBLISH
                    redis.publish(f'job:{job_id}:progress', json.dumps({
                        'phase': 'assembling_video',
                        'progress_percent': 80 + (percent * 0.2),  # 전체의 80~100% 구간
                        'current_step_detail': f'렌더링 {percent}% ({int(current_time)}초/{total_duration_sec}초)'
                    }))
        
        t = threading.Thread(target=read_progress, daemon=True)
        t.start()
        proc.wait()
        t.join(timeout=5)

중간 산출물 S3 정리 (스토리지 비용 최적화):
  최종 MP4가 S3에 성공적으로 업로드된 후,
  이 영상을 만드는 데 사용된 중간 산출물을 정리한다.

  즉시 삭제 대상:
  - tts_audio (씬별 mp3 파일 ~18개)
  - scene_image (씬별 이미지 파일 ~18개)
  - subtitle (SRT 파일)
  - bgm (선택된 BGM 파일)

  유지 대상:
  - video (최종 MP4) → output TTL(24시간) 후 삭제
  - thumbnail (썸네일) → output TTL 후 삭제
  - script JSON → output TTL 후 삭제

  구현:
  - Asset 테이블에서 해당 job_id의 중간 산출물 조회
  - S3 batch delete 실행
  - Asset 레코드의 is_deleted 플래그 업데이트
  - 삭제된 용량 로깅

  실패 시:
  - 중간 산출물 삭제 실패는 영상 생성 실패로 처리하지 않음
  - periodic_tasks의 cleanup에서 재시도
"""
```

---

## 오케스트레이터 (orchestrator.py)

```python
"""
Celery task 체인으로 파이프라인을 구성한다.
하나의 거대한 async orchestrator가 아니라, step 단위로 task를 분리.

큐 라우팅:
  - default 큐: extract, normalize, evidence_pack, research, review,
                policy_review, human_gate, tts, images, subtitles, bgm,
                render_manifest
  - render 큐: assemble (Step 5만 전용 큐)

  체인 내 라우팅 예시:
    extract_task.s(job_id)
    | normalize_task.s()
    | evidence_pack_task.s()
    | research_task.s()
    | review_task.s()
    | policy_review_task.s()
    | human_gate_task.s()
    | asset_generation_group       # group()으로 4a,4b,4d 병렬
    | subtitle_task.s()
    | render_manifest_task.s()
    | assemble_task.s().set(queue='render')  # render 큐로 라우팅

각 task는:
1. 시작 시 JobStepExecution 레코드 생성 (status=running)
2. 완료 시 status=completed, 산출물 S3 업로드, Asset 등록
3. 실패 시 status=failed, error 기록
4. Redis PUBLISH로 SSE 상태 전송
5. job.is_cancelled 체크 → True면 즉시 중단
6. DB 접근 시 반드시 sync_session 사용 (Celery 내 async 금지)

비동기/동기 분리:
- API 계층: async (FastAPI + asyncpg)
- Celery task 내 AI API 호출: sync 래퍼 사용
  (openai, google-genai SDK 자체가 sync이므로 그대로 사용 가능)
  (async SDK 사용 시 asgiref.sync.async_to_sync 래퍼 필수)
- 렌더/FFmpeg/MoviePy: sync worker task (render 큐, concurrency=1)

Cost Guardrail:
- 각 AI API 호출 후 cost_tracker로 비용 기록
- 누적 비용이 cost_budget_usd 초과 시:
  1. 이미지 생성 → priority 낮은 씬부터 placeholder로 대체
  2. 고가 모델 → flash 모델로 자동 다운그레이드
  3. 그래도 초과 → 나머지 이미지 전부 text_overlay로 대체
  4. 최종 초과 → job 실패 처리 + 사용자에게 예산 부족 알림
"""
```

---

## Job 생명주기 관리

### 작업 취소 (Cancel)

```python
"""
POST /api/v1/videos/{job_id}/cancel

1. job.is_cancelled = True (DB 업데이트)
2. 현재 실행 중인 Celery task revoke
3. 이미 생성된 asset은 유지 (24시간 TTL 후 자동 삭제)
4. SSE로 "cancelled" 이벤트 전송
5. 진행 중이던 step의 JobStepExecution.status = "cancelled"
"""
```

### 특정 Step부터 재실행 (Retry from Step)

```python
"""
POST /api/v1/videos/{job_id}/retry?from_step=review

1. job.last_completed_step 확인
2. 해당 step 이후의 JobStepExecution 레코드 초기화
3. 해당 step 이후의 Asset 삭제 (S3 + DB)
4. attempt_count 증가
5. 해당 step부터 Celery 체인 재시작
6. 이전 step의 산출물은 재사용 (S3에서 다시 다운로드)

사용 사례:
- policy_review에서 수정 후 다시 asset 생성
- 이미지 품질이 마음에 안 들어서 step4b만 재실행
"""
```

### Human Approval

```python
"""
POST /api/v1/videos/{job_id}/approve
POST /api/v1/videos/{job_id}/reject

approve:
1. job.human_approved = True
2. 대기 중이던 파이프라인 재개 (Celery task 트리거)

reject:
1. job.human_approved = False
2. job.phase = "rejected"
3. 사용자에게 대본 수정 후 재요청 안내
"""
```

---

## SSE 실시간 상태 스트리밍

```python
"""
GET /api/v1/videos/{job_id}/stream

인증 필요: JWT Bearer token (해당 job의 소유자만 구독 가능)

이벤트 타입:
- progress: { phase, progress_percent, current_step_detail, cost_usd }
- approval_required: { script_preview_url, sensitivity_level }
- cost_warning: { current_cost, budget, message }
- completed: { download_url, thumbnail_url, duration_sec, total_cost }
- failed: { error_message, last_completed_step, can_retry }
- cancelled: {}

구현: Redis Pub/Sub → sse-starlette EventSourceResponse
fallback: GET /api/v1/videos/{job_id} polling (SSE 미지원 클라이언트)
"""
```

---

## Cost Guardrail (cost_tracker.py)

```python
"""
API 호출별 비용을 실시간 추적하고 예산 초과를 방지.

비용 단가 (2026년 3월 기준, 설정에서 변경 가능):
- Gemini 2.5 Flash: ~$0.15/1M input, ~$0.60/1M output
- Gemini 2.5 Pro: ~$1.25/1M input, ~$10/1M output
- GPT-4o: ~$2.50/1M input, ~$10/1M output
- DALL-E 3 (1792x1024): ~$0.08/장
- TTS-1-HD: ~$0.03/1,000자

12분 영상 예상 비용:
- Gemini 대본 생성: ~$0.05
- GPT-4o 검수: ~$0.03
- GPT-4o 정책 검수: ~$0.02
- DALL-E 이미지 8장: ~$0.64
- 카드/차트 10장: $0 (로컬 생성)
- TTS 2,500자: ~$0.08
- 총 예상: ~$0.82

예산 초과 시 자동 Degrade:
1단계: DALL-E 이미지 수 50% 감소 (나머지 text_overlay)
2단계: Gemini Pro → Flash 다운그레이드
3단계: 이미지 전부 text_overlay
4단계: job 실패 + 사용자 알림
"""
```

---

## Observability

```python
"""
모든 로그에 아래 컨텍스트 포함:
- trace_id: 요청별 고유 ID (middleware에서 주입)
- job_id: 파이프라인 작업 ID
- step_name: 현재 실행 중인 step
- user_id: 요청 사용자

loguru 포맷:
  {time} | {level} | trace={trace_id} job={job_id} step={step_name} | {message}

prometheus 메트릭:
- video_jobs_total (counter, labels: status)
- video_job_duration_seconds (histogram)
- api_call_duration_seconds (histogram, labels: provider, model)
- api_call_cost_usd (counter, labels: provider)
- active_celery_tasks (gauge)
- storage_usage_bytes (gauge, labels: bucket)
"""
```

---

## Docker 구성

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

---

## API 엔드포인트 전체

### 인증
- POST /auth/register
- POST /auth/login → JWT 반환

### 영상 생성
- POST /api/v1/videos (인증 필수, idempotency_key 지원, quota 체크)
- GET /api/v1/videos/{job_id} (소유자만)
- GET /api/v1/videos/{job_id}/stream (SSE, 소유자만)
- GET /api/v1/videos/{job_id}/download (presigned URL redirect, 소유자만)
- GET /api/v1/videos/{job_id}/script (대본 조회, 소유자만)
- POST /api/v1/videos/{job_id}/approve (human gate 승인)
- POST /api/v1/videos/{job_id}/reject (human gate 거부)
- POST /api/v1/videos/{job_id}/cancel (작업 취소)
- POST /api/v1/videos/{job_id}/retry (재실행, from_step 파라미터)

### 관리자
- GET /admin/jobs (전체 job 목록, 필터링)
- POST /admin/jobs/{job_id}/force-cancel (강제 취소)
- GET /admin/stats (일일 생성수, 비용 합계, 실패율)

### 시스템
- GET /health (서버 + DB + Redis + MinIO + API 키 유효성 + 디스크)
- GET /metrics (Prometheus 메트릭)

---

## 프론트엔드 연동 필수 사항

### CORS 설정
```python
"""
main.py에 CORSMiddleware 추가:

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Vite 개발 서버
        "http://localhost:3000",      # 대체 포트
        # 프로덕션 시 실제 도메인 추가
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
```

### SSE 엔드포인트 토큰 처리
```python
"""
EventSource API는 커스텀 헤더를 지원하지 않으므로,
SSE 엔드포인트는 쿼리 파라미터로도 JWT를 받을 수 있어야 한다.

GET /api/v1/videos/{job_id}/stream?token={jwt}

stream.py에서:
1. Authorization 헤더에서 토큰 추출 시도
2. 없으면 query parameter 'token'에서 추출
3. 둘 다 없으면 401 반환
"""
```

---

## 설정 파일

### .env.example
```
# AI API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_TOKENS=8192

# OpenAI
OPENAI_CHAT_MODEL=gpt-4o
OPENAI_TTS_MODEL=tts-1-hd
OPENAI_TTS_VOICE=alloy
OPENAI_IMAGE_MODEL=dall-e-3
OPENAI_IMAGE_SIZE=1792x1024

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/video_pipeline
SYNC_DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/video_pipeline

# Redis
REDIS_URL=redis://localhost:6379/0

# Object Storage (MinIO / S3)
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_ASSETS_BUCKET=video-pipeline-assets
S3_OUTPUTS_BUCKET=video-pipeline-outputs

# App
TEMP_DIR=./temp
MAX_CONCURRENT_IMAGE_REQUESTS=5
LOG_LEVEL=INFO

# Storage TTL
OUTPUT_TTL_HOURS=24
FAILED_TEMP_TTL_HOURS=6

# Cost
DEFAULT_COST_BUDGET_USD=2.0
DALLE_COST_PER_IMAGE=0.08
TTS_COST_PER_1K_CHARS=0.03

# Auth
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Quota
DEFAULT_DAILY_QUOTA=5
```

---

## 구현 순서 (반드시 이 순서대로)

### Phase 1: 프로젝트 뼈대 + 인프라
1. 디렉토리 구조 생성
2. requirements.txt 작성
3. config.py + .env.example
4. Docker Compose (Postgres + Redis + MinIO + API + Worker + Beat)
5. Dockerfile.api + Dockerfile.worker
6. SQLAlchemy 모델 전체 (User, VideoJob, JobStepExecution, Source, Asset, CostLog)
7. Alembic 초기 마이그레이션
8. FastAPI main.py + health endpoint
9. object_store.py (S3/MinIO 래퍼)

### Phase 2: 인증 + API 기본
10. JWT auth (register, login, get_current_user)
11. idempotency middleware
12. rate_limit middleware
13. trace middleware (trace_id 주입)
14. POST /api/v1/videos + GET /status 라우트
15. Pydantic 요청/응답 스키마

### Phase 3: 소스 처리 파이프라인
16. retry.py (tenacity 공통 모듈)
17. content_extractor.py (Blog, News, YouTube + yt-dlp fallback)
18. step1_extract.py
19. step1b_normalize.py (정규화, 중복 제거, 신뢰도 점수)
20. step1c_evidence_pack.py (청킹, 랭킹, 근거팩 생성)

### Phase 4: 대본 생성 + 정책 검수
21. gemini_client.py + retry 적용
22. prompts.py (대본 생성 + 검수 + 정책 프롬프트)
23. step2_research.py (Gemini 대본 생성)
24. openai_client.py + retry 적용
25. step3_review.py (ChatGPT 검수)
26. step3b_policy_review.py (민감 주제 정책 검수)
27. step3c_human_gate.py (승인 게이트)
28. approve/reject API 라우트

### Phase 5: 자산 생성
29. step4a_tts.py + retry
30. step4b_images.py (DALL-E + quote_card + data_chart + 다양한 asset 생성)
31. step4c_subtitles.py
32. step4d_bgm.py
33. cost_tracker.py (비용 추적 + guardrail)
34. artifact_registry.py (산출물 S3 등록/조회)

### Phase 6: 영상 조립
35. video_utils.py
36. render_manifest.py 생성 로직
37. step5_assemble.py (sync worker task)
38. Ken Burns 효과

### Phase 7: 오케스트레이션 + 인프라
39. orchestrator.py (Celery task 체인 + 큐 라우팅)
40. celery_app.py (아래 설정 필수 포함)

```python
"""
celery_app.py 필수 설정:

# 브로커 타임아웃 (치명적 중복 렌더링 방지)
# 15분 영상 렌더링에 10~20분 소요.
# 기본 visibility_timeout(1시간)이 지나면 Redis가
# "워커가 죽었다"고 판단하여 다른 워커에 작업을 재할당한다.
# → 동일 영상을 2번 렌더링 = 비용/자원 2배 폭발
# 따라서 넉넉하게 4시간(14400초)으로 설정.
broker_transport_options = {
    'visibility_timeout': 14400,  # 4시간
}

# 큐 라우팅
task_routes = {
    'app.pipeline.steps.step5_assemble.*': {'queue': 'render'},
    # 나머지는 default 큐 자동
}

# 렌더 큐 prefetch 제한 (한 번에 1개만 가져옴)
worker_prefetch_multiplier = 1  # render worker용

# Task 결과 만료 (24시간)
result_expires = 86400

# 직렬화
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
"""
```

41. periodic_tasks.py (파일 정리, API 헬스체크, stale job 정리)
42. stream.py (SSE)
43. cancel/retry API 라우트
44. admin 라우트

### Phase 8: Observability + 마무리
45. prometheus 메트릭 엔드포인트
46. 구조화 로그 설정 (trace_id, job_id 포함)
47. admin 통계 API

### Phase 9: 테스트
48. conftest.py (DB, Redis, MinIO fixture)
49. 각 step 정상 경로 테스트
50. 각 외부 API step: success / retry / fallback / final failure 4종 테스트
51. render step: 짧은 스크립트, 긴 스크립트, 일부 asset 실패 3종 통합 테스트
52. idempotency 테스트
53. cancel / resume / retry from step 테스트
54. cost budget exceeded 테스트
55. policy review 테스트 (주식, 정치, 의료 각각)
56. README.md 작성

---

## 중요 제약사항

1. **Python 3.11+ 문법** (match-case, type hints, | None 구문)
2. **API 계층은 async(asyncpg)**, Celery Worker는 **sync(psycopg2)** — 절대 혼용 금지
3. **Celery task 안에서 AsyncSession import 금지** — sync_session.py만 사용
4. 각 Step은 독립적으로 테스트 가능 (의존성 주입)
5. 중간 결과물은 S3에 저장하여 재시작/재실행 가능
6. 비용 추적: 모든 AI API 호출 시 CostLog 기록 + cost_budget 체크
7. 한국어 최적화: TTS, 자막, 나레이션
8. Rate Limiting: asyncio.Semaphore + 사용자별 quota
9. 구조화 로그: loguru + trace_id + job_id
10. 타입 힌트: 전체 함수, mypy strict
11. 외부 API 호출은 반드시 retry.py 데코레이터
12. Docker: API(경량) / Worker-default(경량 task) / Worker-render(영상 전용, concurrency=1) 분리
13. 로컬 파일시스템은 temp 전용, 영속 데이터는 Postgres + S3
14. 정치/주식/시사는 별도 policy review, fact/inference/opinion 명시 구분
15. 모든 다운로드 URL은 presigned URL (인증된 사용자만 접근)
16. **Celery 브로커 visibility_timeout = 14400초(4시간)** — 렌더링 중복 실행 방지
17. **Step 5는 render 큐 전용** — assemble_task.s().set(queue='render')
18. **Step 5 FFmpeg 진행률을 10초마다 Redis PUBLISH** — 프론트 멈춤 방지
19. **영상 완성 후 중간 산출물(tts, image) S3 즉시 삭제** — 스토리지 비용 최적화
20. **requirements.txt에 psycopg2-binary 포함** — Celery Worker용 동기 DB 드라이버

---

## 시작 명령

위 설계대로 Phase 1부터 순서대로 구현해줘.
각 Phase 완료 시 간단히 무엇을 구현했는지 알려주고, 다음 Phase로 넘어가줘.
코드 품질은 프로덕션 레벨로, 에러 처리와 로깅을 빠뜨리지 마.