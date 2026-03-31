# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 개요

AI 영상 생성 파이프라인 서비스. 사용자가 주제 + 소스 URL을 제출하면, 시스템이 콘텐츠를 추출하고, AI로 스크립트를 생성하고, TTS/이미지/자막을 만들어 최종 영상을 조립합니다. 사람 승인 게이트와 비용 예산 제한 기능을 포함합니다.

## 기술 스택

- **백엔드:** Python 3.11, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 16, Celery 5 + Redis 7, MinIO (S3)
- **프론트엔드:** React 18 + TypeScript, Vite 6, Zustand, TanStack Query, Shadcn/ui + Tailwind CSS
- **AI:** Google Gemini SDK, OpenAI SDK (GPT-4, DALL-E, TTS)
- **영상 처리:** MoviePy, FFmpeg, Pillow

## 명령어

### 백엔드
```bash
# 방법 1: Docker로 전체 서비스 한번에 시작
docker compose up --build

# 방법 2: 로컬 개발 (인프라는 Docker, 앱은 로컬)
docker compose up postgres redis minio minio-init   # 1) 인프라만 먼저 띄우기
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload  # 2) API 서버 실행
celery -A app.workers.celery_app worker --queues=default --concurrency=4  # 3) 기본 워커
celery -A app.workers.celery_app worker --queues=render --concurrency=1   # 4) 렌더 워커

# 데이터베이스 마이그레이션
alembic revision --autogenerate -m "설명"
alembic upgrade head

# 테스트
pytest
pytest tests/path/to/test_file.py -v          # 단일 파일
pytest tests/path/to/test_file.py::test_name   # 단일 테스트
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev          # 개발 서버 :5173
npm run build        # tsc + vite 빌드
npm run lint         # eslint
```

## 아키텍처

### 백엔드 (`app/`)

- **`api/routes/`** — FastAPI 라우터: 인증 (JWT), 영상 작업, SSE 스트리밍, 관리자, 헬스체크
- **`api/schemas/`** — Pydantic 요청/응답 모델
- **`api/middleware/`** — Trace ID, 요청 제한 (Redis, 60회/60초), 멱등성 처리
- **`db/models/`** — SQLAlchemy ORM: User, VideoJob, Source, JobStepExecution, Asset, CostLog (모두 UUID PK, 타임스탬프 믹스인)
- **`db/repositories/`** — Repository 패턴 데이터 접근 (JobRepository, UserRepository)
- **`db/session.py`** — API용 AsyncSession; `sync_session.py`는 Celery 워커용
- **`pipeline/orchestrator.py`** — 12단계 Celery 체인 구성
- **`pipeline/steps/`** — 개별 파이프라인 태스크 (추출 → 정규화 → 근거 추출 → 리서치 → 리뷰 → 정책 검토 → 사람 승인 → TTS → 이미지 → BGM → 자막 → 조립)
- **`services/`** — 비즈니스 로직: 콘텐츠 추출 (BS4, newspaper3k, youtube-transcript-api), Gemini 클라이언트, OpenAI 클라이언트, 비용 추적기
- **`storage/`** — S3/MinIO 비동기 래퍼 (boto3), 사전 서명 URL
- **`auth/`** — JWT HS256 인코딩/디코딩, bcrypt 비밀번호 해싱, FastAPI 의존성
- **`config.py`** — Pydantic BaseSettings, 모든 환경 변수

### 프론트엔드 (`frontend/src/`)

- **`pages/`** — 라우트 컴포넌트 (지연 로딩): 로그인, 회원가입, 대시보드, 작업 목록, 작업 상세, 승인, 관리자
- **`components/ui/`** — Shadcn/Radix UI 기본 컴포넌트
- **`hooks/`** — `use-auth`, `use-jobs`, `use-job-stream` (SSE), `use-job-actions`
- **`stores/`** — Zustand: auth-store (localStorage에 JWT 저장), theme-store
- **`lib/axios.ts`** — 인증 인터셉터 포함 Axios 인스턴스; `lib/sse.ts` — EventSource 래퍼
- **`types/`** — API 응답, 작업, 사용자 TypeScript 인터페이스

### 핵심 설계 결정

- **Async/Sync 분리:** API는 `AsyncSession` (asyncpg) 사용, Celery 워커는 `SyncSessionLocal` (psycopg2) 사용 (Celery가 동기 방식이므로)
- **렌더 큐 격리:** `worker-render`는 동시성 1로 실행, 4시간 가시성 타임아웃으로 중복 영상 렌더링 방지
- **사람 승인 게이트:** Step 3c에서 파이프라인 일시 정지; POST `/api/v1/videos/{job_id}/approve`로 TTS 단계부터 재개
- **SSE 인증:** EventSource는 헤더 설정 불가하므로 JWT를 `?token=` 쿼리 파라미터로 전달
- **비용 추적:** AI API 호출 전 단계별 예산 제한; 일일 사용자당 할당량 (기본 5건/일)
- **S3 버킷 2개:** `video-pipeline-assets` (중간 산출물), `video-pipeline-outputs` (최종 영상)

## 환경 설정

`.env.example`을 `.env`로 복사. 필수 키: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `S3_*` 인증 정보, `JWT_SECRET_KEY`.

## 참고

Alembic 마이그레이션 디렉토리 (`alembic/versions/`)가 현재 비어 있음 — 최초 사용 전 `alembic revision --autogenerate`를 실행하여 초기 스키마를 생성해야 합니다.
