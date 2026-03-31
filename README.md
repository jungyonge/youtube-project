# AI 유튜브 영상 자동 생성 서비스

사용자가 입력한 주제와 소스 URL을 기반으로 AI가 자동으로 유튜브 영상을 생성하는 풀스택 플랫폼입니다. 콘텐츠 추출, 스크립트 작성, TTS 음성 생성, 이미지 생성, 자막/배경음악 추가, 최종 영상 조립까지 12단계 파이프라인으로 자동화됩니다.

## 기술 스택

### 백엔드
- **프레임워크:** Python 3.11 + FastAPI
- **데이터베이스:** PostgreSQL 16 (SQLAlchemy 2.0 + asyncpg)
- **작업 큐:** Celery 5 + Redis 7
- **오브젝트 스토리지:** MinIO (S3 호환)
- **AI/ML:** Google Gemini, OpenAI (GPT-4, DALL-E, TTS)
- **콘텐츠 추출:** BeautifulSoup4, newspaper3k, youtube-transcript-api, Playwright
- **영상 처리:** MoviePy, FFmpeg, Pillow
- **인증:** JWT (HS256) + bcrypt

### 프론트엔드
- **프레임워크:** React 18 + TypeScript
- **빌드 도구:** Vite 6
- **상태 관리:** Zustand
- **데이터 페칭:** TanStack Query, Axios
- **UI:** Shadcn/ui (Radix) + Tailwind CSS
- **실시간 업데이트:** Server-Sent Events (SSE)

## 프로젝트 구조

```
├── app/                          # 백엔드 애플리케이션
│   ├── api/
│   │   ├── routes/              # API 라우터 (auth, video, status, stream, admin, health)
│   │   ├── schemas/             # Pydantic 요청/응답 스키마
│   │   └── middleware/          # 트레이스, 속도 제한, 멱등성
│   ├── auth/                    # JWT 인증
│   ├── db/
│   │   ├── models/              # ORM 모델 (User, VideoJob, Source, JobStep, Asset, CostLog)
│   │   └── repositories/       # 리포지토리 패턴
│   ├── pipeline/
│   │   ├── orchestrator.py      # 12단계 Celery 체인 구성
│   │   └── steps/               # 개별 파이프라인 태스크
│   ├── services/                # 비즈니스 로직 (ContentExtractor, Gemini, OpenAI, CostTracker)
│   ├── storage/                 # S3/MinIO 래퍼
│   └── workers/                 # Celery 설정, 주기적 태스크
├── frontend/                     # React/TypeScript 프론트엔드
│   └── src/
│       ├── pages/               # 페이지 컴포넌트
│       ├── components/          # 재사용 가능한 컴포넌트
│       ├── hooks/               # 커스텀 훅
│       ├── stores/              # Zustand 스토어
│       ├── lib/                 # 유틸리티
│       └── types/               # TypeScript 타입 정의
├── tests/                       # 테스트
├── alembic/                     # DB 마이그레이션
├── docker-compose.yml           # Docker 컨테이너 오케스트레이션
├── Dockerfile.api               # API 컨테이너
└── Dockerfile.worker            # Celery 워커 컨테이너
```

## 영상 생성 파이프라인 (12단계)

| 단계 | 이름 | 설명 |
|------|------|------|
| 1 | Extract | 블로그, 뉴스, 유튜브 등에서 콘텐츠 추출 |
| 2 | Normalize | 추출된 콘텐츠 정제 및 표준화 |
| 3 | Evidence Pack | 근거 자료 구조화 (주장 + 출처) |
| 4 | Research | Gemini AI로 영상 스크립트 생성 |
| 5 | Review | 스크립트 품질 및 구조 검증 |
| 6 | Policy Review | 정책 위반 및 민감도 검토 |
| 7 | Human Gate | 사용자 승인 대기 (선택사항) |
| 8 | TTS | OpenAI TTS로 나레이션 음성 생성 |
| 9 | Images | DALL-E로 이미지 생성 |
| 10 | BGM | 배경음악 선택/생성 |
| 11 | Subtitles | SRT 자막 파일 생성 |
| 12 | Assemble | MoviePy + FFmpeg로 최종 영상 조립 |

## 주요 기능

- **AI 기반 영상 자동 생성** - 주제와 소스만 입력하면 완성된 영상 출력
- **실시간 진행 상태 추적** - SSE를 통한 파이프라인 단계별 실시간 모니터링
- **사용자 승인 워크플로우** - 민감한 콘텐츠에 대한 사람의 검토/승인 단계
- **비용 관리** - 작업별 예산 한도 및 일일 사용자 쿼터 관리
- **멱등성 처리** - 중복 요청 방지
- **관리자 대시보드** - 시스템 통계, 전체 작업 조회, 일일 통계

## 시작하기

### Docker Compose (권장)

```bash
# 환경 변수 파일 복사
cp .env.example .env

# .env 파일에 API 키 설정
# GEMINI_API_KEY, OPENAI_API_KEY, JWT_SECRET_KEY

# 빌드 및 실행
docker-compose up --build
```

실행 후 접속 주소:
- **프론트엔드:** http://localhost:5173
- **API:** http://localhost:8000
- **MinIO 콘솔:** http://localhost:9001

### 로컬 개발

```bash
# 백엔드
pip install -r requirements.txt
uvicorn app.main:app --reload

# Celery 워커 (기본 큐)
celery -A app.workers.celery_app worker --queues=default --concurrency=4

# Celery 워커 (렌더링 큐, 동시성 1)
celery -A app.workers.celery_app worker --queues=render --concurrency=1

# Celery Beat 스케줄러
celery -A app.workers.celery_app beat

# 프론트엔드
cd frontend
npm install
npm run dev
```

### 데이터베이스 마이그레이션

```bash
# 모델 변경 사항으로 마이그레이션 자동 생성
alembic revision --autogenerate -m "설명"

# 마이그레이션 적용
alembic upgrade head
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/auth/register` | 회원가입 |
| `POST` | `/api/v1/auth/login` | 로그인 (JWT 발급) |
| `GET` | `/api/v1/videos` | 내 영상 목록 조회 |
| `POST` | `/api/v1/videos` | 새 영상 생성 요청 |
| `GET` | `/api/v1/videos/{job_id}` | 작업 상태 조회 |
| `POST` | `/api/v1/videos/{job_id}/approve` | 작업 승인 |
| `POST` | `/api/v1/videos/{job_id}/reject` | 작업 거부 |
| `POST` | `/api/v1/videos/{job_id}/cancel` | 작업 취소 |
| `GET` | `/api/v1/stream/{job_id}` | SSE 실시간 스트림 |
| `GET` | `/api/v1/admin/stats` | 시스템 통계 (관리자) |
| `GET` | `/api/v1/admin/jobs` | 전체 작업 조회 (관리자) |
| `GET` | `/health` | 헬스 체크 |

## 환경 변수

| 변수명 | 설명 |
|--------|------|
| `GEMINI_API_KEY` | Google Gemini API 키 |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `DATABASE_URL` | PostgreSQL 비동기 연결 문자열 |
| `SYNC_DATABASE_URL` | PostgreSQL 동기 연결 문자열 (Celery용) |
| `REDIS_URL` | Redis 브로커 URL |
| `S3_ENDPOINT_URL` | MinIO/S3 엔드포인트 |
| `S3_PUBLIC_URL` | 공개 S3 접근 URL |
| `JWT_SECRET_KEY` | JWT 서명 시크릿 키 |
| `DEFAULT_COST_BUDGET_USD` | 작업별 기본 비용 한도 |
| `DEFAULT_DAILY_QUOTA` | 사용자 일일 영상 생성 한도 |
| `OUTPUT_TTL_HOURS` | 출력 영상 보관 시간 |

## 테스트

```bash
pytest
pytest tests/path/test.py::test_name -v
```

## 아키텍처 결정 사항

- **Async/Sync 분리:** FastAPI는 비동기 SQLAlchemy(asyncpg), Celery 워커는 동기 세션(psycopg2) 사용
- **렌더링 큐 격리:** 영상 조립 단계는 전용 `render` 큐에서 `concurrency=1`로 실행
- **SSE 인증:** EventSource는 커스텀 헤더를 지원하지 않으므로 JWT를 쿼리 파라미터로 전달
- **2-버킷 S3 전략:** 임시 에셋(`video-pipeline-assets`)과 최종 출력(`video-pipeline-outputs`) 분리
- **비용 제어:** 각 단계 실행 전 예산 확인, 일일 사용자별 쿼터로 리소스 보호
