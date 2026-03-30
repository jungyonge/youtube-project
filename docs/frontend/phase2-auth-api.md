# Phase 2: 인증 + API 기본

## 목표
JWT 기반 인증/인가 시스템, 미들웨어(idempotency, rate limit, trace), 핵심 API 라우트,
요청/응답 스키마를 구현한다.

---

## 구현 항목

### 10. JWT auth (register, login, get_current_user)

**파일**: `app/auth/jwt_handler.py`, `app/auth/dependencies.py`, `app/auth/password.py`

- JWT 생성/검증
- `get_current_user`, `require_admin` 의존성
- bcrypt 해싱

**파일**: `app/api/routes/auth.py`
- `POST /auth/register`
- `POST /auth/login` → JWT 반환

### 11. idempotency middleware

**파일**: `app/api/middleware/idempotency.py`
- 중복 요청 방지
- `idempotency_key` 기반

### 12. rate_limit middleware

**파일**: `app/api/middleware/rate_limit.py`
- 사용자별 요청 제한
- asyncio.Semaphore + 사용자별 quota

### 13. trace middleware (trace_id 주입)

**파일**: `app/api/middleware/trace.py`
- 요청별 trace_id 생성 및 주입
- 모든 로그에 trace_id 포함

### 14. POST /api/v1/videos + GET /status 라우트

**파일**: `app/api/routes/video.py`, `app/api/routes/status.py`

- `POST /api/v1/videos` (인증 필수, idempotency_key 지원, quota 체크)
- `GET /api/v1/videos/{job_id}` (소유자만)
- `GET /api/v1/videos/{job_id}/download` (presigned URL redirect, 소유자만)
- `GET /api/v1/videos/{job_id}/script` (대본 조회, 소유자만)

### 15. Pydantic 요청/응답 스키마

**파일**: `app/api/schemas/request.py`, `app/api/schemas/response.py`

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

## 선행 조건
- Phase 1 완료 (DB 모델, 세션, config)

## 완료 기준
- [ ] JWT register/login 동작
- [ ] `get_current_user`, `require_admin` 의존성 동작
- [ ] idempotency middleware 동작 (동일 key 중복 요청 차단)
- [ ] rate_limit middleware 동작 (사용자별 quota 적용)
- [ ] trace middleware 동작 (요청별 trace_id 주입)
- [ ] `POST /api/v1/videos` 정상 동작 (Job 생성)
- [ ] `GET /api/v1/videos/{job_id}` 소유자만 조회 가능
- [ ] 요청/응답 스키마 Validation 동작
- [ ] CORS 설정 완료
- [ ] SSE 엔드포인트 토큰 처리 (헤더 + 쿼리 파라미터) 준비
