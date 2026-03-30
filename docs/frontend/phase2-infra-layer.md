# Phase 2: 인프라 레이어

## 목표
타입 정의, 상태 관리(Zustand), HTTP 클라이언트(Axios), SSE 유틸리티 등
프론트엔드의 기반 레이어를 구축한다. 백엔드 SSE 쿼리 파라미터 토큰 지원과 목록/Step 조회 API를 확인/추가한다.

---

## 구현 항목

### 프론트엔드

#### 10. types/ 전체 타입 정의
**파일**: `types/api.ts`, `types/job.ts`, `types/user.ts`
- SourceType, VideoStyle, ClaimType, JobPhase
- SourceInput, VideoGenerationRequest, JobStatusResponse, JobStepDetail
- SSE 이벤트 타입들 (SSEProgressEvent, SSECompletedEvent, SSEApprovalEvent, SSEFailedEvent)
- SceneClaim, SceneAssetPlan, ScriptScene, FullScript
- AdminStats, AdminJobItem, AuthResponse
- PaginatedResponse<T>, DailyStatsItem

#### 11. lib/utils.ts
- `cn` (clsx + tailwind-merge)
- `formatDuration`, `formatCost`, `formatDate`

#### 12. stores/auth-store.ts (Zustand)
```typescript
/**
 * interface AuthState {
 *   token: string | null;
 *   refreshToken: string | null;  // MVP에서는 null 가능, 추후 확장
 *   user: User | null;
 *   setAuth: (token: string, user: User, refreshToken?: string) => void;
 *   setToken: (token: string) => void;  // Silent Refresh용
 *   logout: () => void;
 *   isAuthenticated: () => boolean;
 *   isAdmin: () => boolean;
 * }
 *
 * localStorage에 token + refreshToken 영속화
 * 앱 시작 시 localStorage에서 복원
 */
```

#### 13. stores/theme-store.ts
- light/dark/system 모드 지원

#### 14. lib/axios.ts
```typescript
/**
 * 인스턴스:
 * - baseURL: VITE_API_BASE_URL
 *
 * Request interceptor:
 * - auth-store에서 token → Authorization: Bearer {token}
 * - X-Idempotency-Key 헤더 (있으면)
 *
 * Response interceptor:
 * - 401 → Refresh Token으로 Access Token 재발급 시도 (Silent Refresh)
 *     성공 → 실패했던 원래 요청을 새 토큰으로 재시도
 *     실패 → logout() → /login redirect
 *   (Refresh Token이 없는 MVP 단계라면:
 *     401 → logout() → /login redirect 로 단순 처리.
 *     단, Axios interceptor에 Refresh 로직 끼울 자리는 미리 만들어둘 것)
 * - 429 → "요청 제한 초과" toast
 * - 409 → 기존 job_id 반환 처리
 * - 5xx → "서버 오류" toast
 *
 * 타입 안전 API 함수:
 *   api.auth.login(email, password): Promise<AuthResponse>
 *   api.auth.register(email, password): Promise<AuthResponse>
 *   api.auth.me(): Promise<User>
 *   api.jobs.create(req): Promise<{ job_id: string }>
 *   api.jobs.list(params?): Promise<PaginatedResponse<JobStatusResponse>>
 *   api.jobs.getStatus(jobId): Promise<JobStatusResponse>
 *   api.jobs.getSteps(jobId): Promise<JobStepDetail[]>
 *   api.jobs.getScript(jobId): Promise<FullScript>
 *   api.jobs.getPlaybackUrl(jobId): Promise<{ url: string }>
 *   api.jobs.cancel(jobId): Promise<{ status: string }>
 *   api.jobs.retry(jobId, opts?): Promise<{ job_id: string, parent_job_id: string }>
 *   api.jobs.approve(jobId): Promise<{ status: string }>
 *   api.jobs.reject(jobId, reason?): Promise<{ status: string }>
 *   api.admin.getStats(): Promise<AdminStats>
 *   api.admin.getDailyStats(days): Promise<DailyStatsItem[]>
 *   api.admin.getJobs(filters): Promise<PaginatedResponse<AdminJobItem>>
 *   api.admin.forceCancel(jobId): Promise<void>
 */
```

#### 15. lib/sse.ts
```typescript
/**
 * EventSource는 커스텀 헤더 불가 → 쿼리 파라미터로 JWT 전달:
 *   /api/v1/videos/{jobId}/stream?token={jwt}
 *
 * createJobSSE(jobId, token, handlers): SSEConnection
 *
 * handlers: {
 *   onProgress, onApprovalRequired, onCostWarning,
 *   onCompleted, onFailed, onCancelled, onConnectionChange
 * }
 *
 * 재연결: 끊김 → 3초 후 (최대 5회)
 * ★ 재연결 성공 시 반드시 api.jobs.getStatus(jobId)를 1회 호출하여
 *   누락된 상태 변화를 동기화(State Reconciliation)한다.
 *   (끊긴 사이에 completed/failed 이벤트가 지나갔을 수 있음.
 *    이걸 안 하면 "99% 렌더링 중"에서 영원히 멈추는 유령 상태 발생)
 * 5회 실패 → onConnectionChange(false)
 */
```

---

### 백엔드 수정

#### 16. SSE 쿼리 파라미터 토큰 허용
**파일**: `stream.py`
```python
"""
현재: Authorization 헤더에서만 JWT 추출
수정: 헤더 없으면 query param 'token'에서도 추출

@router.get("/api/v1/videos/{job_id}/stream")
async def stream_job_status(
    job_id: str,
    token: str | None = Query(default=None),  # ← 추가
    authorization: str | None = Header(default=None),
):
    # 1. Authorization 헤더에서 토큰 추출 시도
    # 2. 없으면 query param token 사용
    # 3. 둘 다 없으면 401
    # 4. 토큰 검증 후 user_id 추출
    # 5. job의 소유자인지 확인
"""
```

#### 17. Job 목록 조회 API 확인/추가
```python
"""
GET /api/v1/videos → 현재 인증된 사용자의 job 목록 반환
이미 있으면 확인만, 없으면 추가.

응답: list[JobStatusResponse]
정렬: created_at DESC
"""
```

#### 18. Step 실행 기록 조회 API 확인/추가
```python
"""
GET /api/v1/videos/{job_id}/steps → JobStepExecution 목록 반환
프론트의 '진행 상세' 탭에서 사용.

응답:
[
  {
    "step_name": "extract",
    "status": "completed",
    "started_at": "...",
    "completed_at": "...",
    "duration_sec": 12.5,
    "cost_usd": 0.0,
    "error_message": null
  },
  ...
]
"""
```
