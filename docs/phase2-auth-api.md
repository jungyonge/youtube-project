# Phase 2: 인증 + API 기본

## 목표
JWT 기반 인증/인가, 미들웨어(멱등성, 속도 제한, 트레이스), 영상 생성 요청/상태 조회 API를 구현한다.

---

## 구현 항목

### 10. JWT Auth

**파일**: `app/auth/password.py`
```python
def hash_password(plain: str) -> str        # bcrypt
def verify_password(plain: str, hashed: str) -> bool
```

**파일**: `app/auth/jwt_handler.py`
```python
def create_access_token(data: dict) -> str   # JWT 생성
def decode_access_token(token: str) -> dict  # JWT 검증
```

**파일**: `app/auth/dependencies.py`
```python
async def get_current_user(token, db) -> User      # Bearer token → User
async def require_admin(current_user: User) -> User # role == "admin" 체크
```

**파일**: `app/api/routes/auth.py`
```
POST /auth/register
  Request: { email, password }
  Response: { id, email, role, created_at }
  - 이메일 중복 체크
  - bcrypt 해싱 후 DB 저장

POST /auth/login
  Request: { email, password }
  Response: { access_token, token_type: "bearer" }
  - 비밀번호 검증
  - JWT 발급
```

**파일**: `app/db/repositories/user_repo.py`
```python
class UserRepository:
    async def create(email, hashed_password) -> User
    async def get_by_email(email) -> User | None
    async def get_by_id(user_id) -> User | None
    async def get_daily_job_count(user_id, date) -> int
```

### 11. Idempotency Middleware

**파일**: `app/api/middleware/idempotency.py`

```python
"""
중복 요청 방지:
1. 요청의 Idempotency-Key 헤더 또는 body.idempotency_key 확인
2. Redis에 key 존재 여부 체크 (TTL 24시간)
3. 존재하면 → 기존 응답 반환 (409 또는 cached response)
4. 없으면 → 처리 후 결과를 Redis에 저장
"""
```

### 12. Rate Limit Middleware

**파일**: `app/api/middleware/rate_limit.py`

```python
"""
사용자별 요청 제한:
- 인증된 사용자: Redis sliding window
- user.daily_quota 기반 일일 영상 생성 제한
- 초과 시 429 Too Many Requests
"""
```

### 13. Trace Middleware

**파일**: `app/api/middleware/trace.py`

```python
"""
요청별 trace_id 주입:
1. 요청 시작 시 UUID trace_id 생성
2. 응답 헤더 X-Trace-ID에 포함
3. loguru context에 바인딩 → 모든 로그에 자동 포함
4. ContextVar로 관리 (async-safe)
"""
```

### 14. 영상 생성/상태 API

**파일**: `app/api/routes/video.py`
```
POST /api/v1/videos
  Auth: Bearer JWT (필수)
  Request: VideoGenerationRequest
  Flow:
    1. idempotency_key 중복 체크
    2. daily_quota 체크
    3. VideoJob 레코드 생성 (phase="queued")
    4. Source 레코드들 생성
    5. Celery task 체인 트리거
    6. Response: { job_id, phase, created_at }
```

**파일**: `app/api/routes/status.py`
```
GET /api/v1/videos/{job_id}
  Auth: Bearer JWT (소유자만)
  Response: JobStatusResponse
    - job_id, phase, progress_percent, current_step_detail
    - is_cancelled, requires_human_approval, human_approved
    - total_cost_usd, cost_budget_usd, attempt_count
    - download_url (presigned, 완료 시), script_preview_url
```

**파일**: `app/db/repositories/job_repo.py`
```python
class JobRepository:
    async def create(user_id, request) -> VideoJob
    async def get_by_id(job_id) -> VideoJob | None
    async def get_by_idempotency_key(key) -> VideoJob | None
    async def update_phase(job_id, phase, **kwargs) -> None
    async def list_by_user(user_id, skip, limit) -> list[VideoJob]
    async def cancel(job_id) -> None
```

### 15. Pydantic 요청/응답 스키마

**파일**: `app/api/schemas/request.py`
```python
class SourceInput(BaseModel):
    url: str
    source_type: Literal["blog", "news", "youtube", "custom_text"] = "blog"
    custom_text: str | None = None

class VideoStyle(str, Enum):
    INFORMATIVE = "informative"
    ENTERTAINING = "entertaining"
    EDUCATIONAL = "educational"
    NEWS = "news"

class VideoGenerationRequest(BaseModel):
    topic: str                                    # 1~200자
    sources: list[SourceInput]                    # min 1, max 10
    style: VideoStyle = VideoStyle.INFORMATIVE
    target_duration_minutes: int = 12             # 10~15
    language: str = "ko"
    tts_voice: str = "alloy"
    include_subtitles: bool = True
    include_bgm: bool = True
    additional_instructions: str | None = None
    cost_budget_usd: float | None = None
    auto_approve: bool = True
    idempotency_key: str | None = None
```

**파일**: `app/api/schemas/response.py`
```python
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
    download_url: str | None = None
    script_preview_url: str | None = None

class JobCreateResponse(BaseModel):
    job_id: str
    phase: str
    created_at: datetime

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: datetime
```

---

## 선행 조건
- Phase 1 완료 (DB 모델, config, session)

## 완료 기준
- [ ] `POST /auth/register` — 회원가입 후 사용자 DB 저장
- [ ] `POST /auth/login` — JWT 토큰 발급
- [ ] JWT 인증 데코레이터로 보호된 라우트 접근 가능
- [ ] `POST /api/v1/videos` — Job 생성 및 Celery task 트리거
- [ ] `GET /api/v1/videos/{job_id}` — 소유자만 상태 조회 가능
- [ ] 중복 요청(idempotency_key) 시 기존 Job 반환
- [ ] daily_quota 초과 시 429 에러
- [ ] 모든 응답에 X-Trace-ID 헤더 포함
