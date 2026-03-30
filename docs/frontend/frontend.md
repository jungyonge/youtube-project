# AI Video Pipeline - Frontend 구축 + Backend 연동 수정

## 상황

백엔드(FastAPI + Celery + PostgreSQL + Redis + MinIO)는 이미 구현 완료된 상태다.
이제 프론트엔드를 구축하면서, **백엔드에서 프론트 연동에 필요한 부분을 함께 수정**한다.

각 Phase에서 프론트엔드 코드를 작성한 뒤,
해당 Phase가 제대로 동작하려면 백엔드에서 고쳐야 할 부분이 있으면 **같이 수정**한다.

**핵심 원칙: 기존 백엔드 구조를 존중한다.**
기존 코드와 충돌하는 경우, 새 구조를 밀어넣지 말고 기존 구조에 맞춰 확장한다.
모르는 기존 구조는 추정하지 말고 먼저 확인한 뒤 반영한다.

## 기술 스택

- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **Routing**: React Router v6
- **State**: Zustand (전역) + TanStack Query v5 (서버 상태)
- **Styling**: Tailwind CSS v3
- **UI Components**: shadcn/ui (Radix 기반)
- **Icons**: Lucide React
- **Form**: React Hook Form + Zod validation
- **SSE**: EventSource API (네이티브)
- **HTTP**: Axios
- **Toast/Alert**: sonner
- **Date**: date-fns
- **Chart**: Recharts (관리자 통계)

---

## 프로젝트 구조

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── .env.example                    # VITE_API_BASE_URL=http://localhost:8000
│
├── public/
│   └── favicon.svg
│
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    │
    ├── config/
    │   └── env.ts
    │
    ├── lib/
    │   ├── axios.ts
    │   ├── sse.ts
    │   └── utils.ts
    │
    ├── stores/
    │   ├── auth-store.ts
    │   └── theme-store.ts
    │
    ├── hooks/
    │   ├── use-auth.ts
    │   ├── use-jobs.ts
    │   ├── use-job-stream.ts
    │   ├── use-job-actions.ts
    │   └── use-admin-stats.ts
    │
    ├── types/
    │   ├── api.ts
    │   ├── job.ts
    │   └── user.ts
    │
    ├── components/
    │   ├── ui/                     # shadcn/ui
    │   │
    │   ├── layout/
    │   │   ├── root-layout.tsx
    │   │   ├── sidebar.tsx
    │   │   ├── header.tsx
    │   │   └── protected-route.tsx
    │   │
    │   ├── auth/
    │   │   ├── login-form.tsx
    │   │   └── register-form.tsx
    │   │
    │   ├── jobs/
    │   │   ├── job-create-form.tsx
    │   │   ├── job-list.tsx
    │   │   ├── job-card.tsx
    │   │   ├── job-detail-panel.tsx
    │   │   ├── job-progress.tsx
    │   │   ├── job-progress-steps.tsx
    │   │   ├── job-cost-badge.tsx
    │   │   ├── job-actions.tsx
    │   │   └── source-input-list.tsx
    │   │
    │   ├── approval/
    │   │   ├── script-preview.tsx
    │   │   ├── script-scene-card.tsx
    │   │   ├── claim-badge.tsx
    │   │   ├── policy-flag-alert.tsx
    │   │   └── approval-actions.tsx
    │   │
    │   └── admin/
    │       ├── admin-job-table.tsx
    │       ├── admin-stats-cards.tsx
    │       └── admin-cost-chart.tsx
    │
    └── pages/
        ├── login-page.tsx
        ├── register-page.tsx
        ├── dashboard-page.tsx
        ├── job-detail-page.tsx
        ├── approval-page.tsx
        └── admin-page.tsx
```

---

## 핵심 타입 정의 (types/api.ts)

```typescript
export type SourceType = "blog" | "news" | "youtube" | "custom_text";
export type VideoStyle = "informative" | "storytelling" | "tutorial" | "opinion";
export type ClaimType = "fact" | "inference" | "opinion";

export type JobPhase =
  | "queued"
  | "extracting"
  | "normalizing"
  | "building_evidence"
  | "generating_script"
  | "reviewing_script"
  | "policy_review"
  | "awaiting_approval"
  | "generating_assets"
  | "assembling_video"
  | "completed"
  | "failed"
  | "cancelled"
  | "rejected";

export interface SourceInput {
  url?: string;
  source_type: SourceType;
  custom_text?: string;
}

export interface VideoGenerationRequest {
  topic: string;
  sources: SourceInput[];
  style: VideoStyle;
  target_duration_minutes: number;
  language: string;
  tts_voice: string;
  include_subtitles: boolean;
  include_bgm: boolean;
  additional_instructions?: string;
  cost_budget_usd?: number;
  auto_approve: boolean;
  idempotency_key: string;
}

export interface JobStatusResponse {
  job_id: string;
  phase: JobPhase;
  progress_percent: number;
  current_step_detail: string;
  is_cancelled: boolean;
  requires_human_approval: boolean;
  human_approved: boolean | null;
  total_cost_usd: number;
  cost_budget_usd: number;
  attempt_count: number;
  parent_job_id: string | null;     // retry로 생성된 경우 원본 job
  created_at: string;
  updated_at: string;               // 상태 동기화 우선순위 판단에 사용
  // download_url 없음 — /download, /playback 엔드포인트를 경유할 것
}

export interface JobStepDetail {
  step_name: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  started_at: string | null;
  completed_at: string | null;
  duration_sec: number | null;
  cost_usd: number;
  error_message: string | null;
}

// SSE 이벤트
export type SSEEventType =
  | "progress"
  | "approval_required"
  | "cost_warning"
  | "completed"
  | "failed"
  | "cancelled";

export interface SSEProgressEvent {
  type: "progress";
  phase: JobPhase;
  progress_percent: number;
  current_step_detail: string;
  cost_usd: number;
}

export interface SSECompletedEvent {
  type: "completed";
  download_url: string;
  thumbnail_url: string;
  duration_sec: number;
  total_cost: number;
}

export interface SSEApprovalEvent {
  type: "approval_required";
  script_preview_url: string;
  sensitivity_level: "low" | "medium" | "high";
}

export interface SSEFailedEvent {
  type: "failed";
  error_message: string;
  last_completed_step: string;
  can_retry: boolean;
}

// 대본
export interface SceneClaim {
  claim_text: string;
  claim_type: ClaimType;
  evidence_source_id: string;
  evidence_quote: string | null;
  confidence: number;
}

export interface SceneAssetPlan {
  asset_type: string;
  generation_prompt: string | null;
  template_id: string | null;
  fallback_strategy: string;
  priority: number;
}

export interface ScriptScene {
  scene_id: number;
  section: string;
  purpose: string;
  duration_target_sec: number;
  duration_actual_sec: number | null;
  narration: string;
  asset_plan: SceneAssetPlan[];
  claims: SceneClaim[];
  policy_flags: string[];
  keywords: string[];
}

export interface FullScript {
  title: string;
  subtitle: string;
  total_duration_sec: number;
  scenes: ScriptScene[];
  tags: string[];
  description: string;
  overall_sensitivity: "low" | "medium" | "high";
  requires_human_approval: boolean;
  policy_warnings: string[];
}

// 관리자
export interface AdminStats {
  today_jobs: number;
  success_rate: number;
  daily_cost_usd: number;
  active_jobs: number;
}

export interface AdminJobItem {
  job_id: string;
  user_email: string;
  topic: string;
  phase: JobPhase;
  total_cost_usd: number;
  created_at: string;
}

// 인증
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    role: string;
    daily_quota: number;
    today_usage: number;
  };
}

// 페이지네이션 (사용자/관리자 통일)
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  has_next: boolean;
}

// 관리자 일별 통계 (차트용)
export interface DailyStatsItem {
  date: string;
  jobs: number;
  cost_usd: number;
  success_count: number;
  fail_count: number;
}
```

---

## 확정 API 계약 (Appendix)

```
선택형 구현을 금지한다. 아래가 공식 스펙이다.
프론트와 백엔드가 서로 다른 선택지를 동시에 구현하지 않도록 한다.
Phase 0에서 기존 백엔드와 충돌이 발견되면 기존 구조를 따르되,
아래 스펙에서 빠진 필드가 있으면 추가한다.

POST /auth/login
  응답: { access_token, token_type, user: { id, email, role, daily_quota, today_usage } }
  refresh token이 기존에 있으면 그대로 사용, 없으면 MVP에서는 access_token만.

GET /auth/me
  응답: { id, email, role, daily_quota, today_usage }
  프론트 헤더에서 quota 잔여 표시에 사용.

POST /api/v1/videos
  응답 (201): { job_id: "uuid" }
  idempotency 중복 (409): { detail: "...", job_id: "기존-uuid" }

GET /api/v1/videos
  응답 (페이지네이션, 사용자/관리자 통일):
  { items: JobStatusResponse[], total: int, page: int, size: int, has_next: bool }
  query params: ?page=1&size=20&status=completed

GET /api/v1/videos/{job_id}
  응답: JobStatusResponse
  download_url 필드 제거. 대신 아래 엔드포인트 사용.

GET /api/v1/videos/{job_id}/steps
  응답: JobStepDetail[]

GET /api/v1/videos/{job_id}/script
  응답: FullScript JSON 직접 반환 (presigned URL 아님)

GET /api/v1/videos/{job_id}/download
  동작: 호출 시점에 1시간짜리 presigned URL 신규 발급 → 307 Redirect
  프론트: <a href="/api/v1/videos/{jobId}/download">다운로드</a>

GET /api/v1/videos/{job_id}/thumbnail
  동작: 같은 방식. presigned URL → 307 Redirect

GET /api/v1/videos/{job_id}/playback
  동작: 같은 방식. 비디오 재생용 presigned URL → JSON { url: "..." }
  프론트: <video src={playbackUrl}> (이 URL은 임시용, 캐시/저장 금지)

GET /api/v1/videos/{job_id}/stream?token={jwt}
  SSE 엔드포인트. 쿼리 파라미터 토큰 허용.

POST /api/v1/videos/{job_id}/cancel
  응답 (200): { status: "cancelled" }
  허용 상태: queued ~ assembling_video (terminal 제외)

POST /api/v1/videos/{job_id}/approve
  응답 (200): { status: "approved" }
  허용 상태: awaiting_approval만

POST /api/v1/videos/{job_id}/reject
  body: { reason?: string }
  응답 (200): { status: "rejected" }
  허용 상태: awaiting_approval만

POST /api/v1/videos/{job_id}/retry
  body: { from_step?: string, cost_budget_usd?: float }
  동작: 새 job을 생성한다 (기존 job은 그대로 유지).
        새 job에 parent_job_id로 기존 job 연결.
        from_step이 있고 재사용 가능한 산출물이 있으면 복사하여 재사용.
        비용은 새 job에서 0부터 시작.
  응답 (201): { job_id: "새-uuid", parent_job_id: "기존-uuid" }

GET /admin/jobs
  응답: { items: AdminJobItem[], total, page, size, has_next }
  AdminJobItem에 user_email 포함 (join 필요)

GET /admin/stats
  응답: { today_jobs, success_rate, daily_cost_usd, active_jobs }

GET /admin/stats/daily?days=30
  응답: [ { date, jobs, cost_usd, success_count, fail_count }, ... ]
```

---

## Job 상태 전이표 (State Machine)

```
프론트의 버튼 활성화/비활성화, 백엔드의 action guard가 이 표를 따른다.

| 현재 상태            | cancel | approve | reject | retry    |
|---------------------|--------|---------|--------|----------|
| queued              | ✅     | -       | -      | -        |
| extracting          | ✅     | -       | -      | -        |
| normalizing         | ✅     | -       | -      | -        |
| building_evidence   | ✅     | -       | -      | -        |
| generating_script   | ✅     | -       | -      | -        |
| reviewing_script    | ✅     | -       | -      | -        |
| policy_review       | ✅     | -       | -      | -        |
| awaiting_approval   | ✅     | ✅      | ✅     | -        |
| generating_assets   | ✅     | -       | -      | -        |
| assembling_video    | ✅     | -       | -      | -        |
| completed           | -      | -       | -      | ✅ (새 job) |
| failed              | -      | -       | -      | ✅ (새 job) |
| cancelled           | -      | -       | -      | ✅ (새 job) |
| rejected            | -      | -       | -      | ✅ (새 job) |

retry는 항상 새 job을 생성한다. 기존 job은 변경되지 않는다.
cancel은 terminal state에서 불가.
approve/reject는 awaiting_approval에서만 가능.

프론트 job-actions.tsx에서 이 표 기반으로 버튼 표시:
  const canCancel = !TERMINAL_STATES.includes(phase) && phase !== 'completed';
  const canApprove = phase === 'awaiting_approval';
  const canRetry = TERMINAL_STATES.includes(phase);
  const TERMINAL_STATES = ['completed', 'failed', 'cancelled', 'rejected'];
```

---

## 상태 동기화 우선순위 규칙

```
SSE, Polling, Optimistic Update, BroadcastChannel 등 여러 상태 소스가
동시에 존재하므로, "누가 최종 진실인가" 규칙이 필요하다.

규칙:
1. 모든 job 상태 응답에는 updated_at 필드가 포함된다.
2. 프론트는 현재 캐시의 updated_at보다 더 최신인 상태만 반영한다.
3. Optimistic update는 임시 상태이며, 서버 응답(SSE/polling)이
   도착하면 서버 상태로 덮어쓴다.
4. Terminal state(completed, failed, cancelled, rejected)는
   더 오래된 running/progress 이벤트로 절대 덮어쓰지 않는다.
5. BroadcastChannel로 다른 탭에서 온 상태도 updated_at 비교 후 반영.

구현:
  function shouldUpdateJobState(current: JobState, incoming: JobState): boolean {
    // terminal은 non-terminal로 되돌리지 않음
    if (TERMINAL_STATES.includes(current.phase) && !TERMINAL_STATES.includes(incoming.phase)) {
      return false;
    }
    // updated_at 비교
    return new Date(incoming.updated_at) > new Date(current.updated_at);
  }

  이 함수를 SSE 핸들러, polling 핸들러, BroadcastChannel 핸들러,
  optimistic update의 onSettled에서 모두 사용한다.
```

---

## 보안 모델

```
MVP(개발 환경):
- Access Token: Zustand + localStorage 저장
- SSE: ?token= 쿼리 파라미터로 전달
- 이 방식은 개발 편의를 위한 것으로, 프로덕션에서는 사용하지 않는다.

프로덕션 전환 시:
- Access Token: 메모리(Zustand)만, localStorage 저장 금지
- Refresh Token: HttpOnly Secure SameSite=Strict 쿠키
- SSE: same-origin 쿠키 인증, 또는 short-lived stream token 방식
  (GET /api/v1/videos/{job_id}/stream-token → 30초 TTL 1회용 토큰)
- 코드에 TODO: PRODUCTION_SECURITY 주석으로 전환 필요 지점 표시

현재 구현에서는 MVP 방식으로 작성하되,
auth-store와 axios interceptor에 프로덕션 전환 자리를 미리 만들어둔다.
```

---

## 페이지별 상세 설계

### 1. 로그인 / 회원가입

```
- 중앙 정렬 카드 레이아웃
- React Hook Form + Zod
- 로그인: email + password → POST /auth/login → JWT → Zustand + localStorage
- 회원가입: email + password + confirm → POST /auth/register → 자동 로그인
- 에러: sonner toast
- 로그인 상태 → /dashboard redirect
```

### 2. 대시보드 (메인)

```
2-column:
┌──────────────────────┬──────────────────────────────┐
│  영상 생성 폼         │  내 영상 목록                  │
│  (job-create-form)   │  (job-list)                  │
│                      │                              │
│  - 주제 입력          │  카드 나열                    │
│  - URL 소스 추가      │  - 상태 뱃지                  │
│  - 스타일 선택        │  - 진행률 바                   │
│  - 고급 설정 접이식    │  - 비용                       │
│  - 생성 버튼          │  - 클릭 → 상세 페이지          │
└──────────────────────┴──────────────────────────────┘

모바일: 단일 컬럼, 탭 전환
```

### 3. 영상 생성 폼 (job-create-form.tsx)

```tsx
/**
 * 필드:
 * 
 * 1. topic (필수): textarea, min 5자, max 200자
 * 
 * 2. sources (필수, 1~10개): 동적 입력 리스트
 *    각 행: [URL 입력 | 타입 Select | 삭제 버튼]
 *    custom_text 선택 시 textarea 표시
 *    "소스 추가" 버튼 (+ 아이콘)
 * 
 * 3. style: 카드 선택 UI (4가지, 아이콘 + 설명)
 * 
 * 4. 고급 설정 (접이식):
 *    - target_duration_minutes: Slider 10~15
 *    - tts_voice: Select (한글 설명 포함)
 *    - language: Select (ko, en, ja)
 *    - include_subtitles: Switch
 *    - include_bgm: Switch
 *    - cost_budget_usd: NumberInput (기본 $2, step $0.50)
 *    - auto_approve: Switch (off 시 안내 문구)
 *    - additional_instructions: textarea
 *    - idempotency_key: 자동 UUID, hidden
 * 
 * 5. 제출 → POST /api/v1/videos → navigate to /jobs/:jobId
 * 
 * Zod schema:
 *   topic: string().min(5).max(200)
 *   sources: array().min(1).max(10)
 *   sources[].url: custom_text가 아니면 url()
 *   target_duration_minutes: number().min(10).max(15)
 *   cost_budget_usd: number().min(0.5).max(10)
 */
```

### 4. Job 상세 페이지

```
URL: /jobs/:jobId

┌─────────────────────────────────────────────────────┐
│  제목 | 상태 뱃지 | 비용 | 생성일 | 액션 버튼          │
├─────────────────────────────────────────────────────┤
│  실시간 진행 (job-progress.tsx)                       │
│  ● 추출 → ● 정규화 → ● 대본 → ◐ 검수 → ○ ...       │
│  [████████████████░░░░░░░] 67%                      │
│  "씬 5/16 이미지 생성 중..."                          │
│  $0.52 / $2.00                                      │
├─────────────────────────────────────────────────────┤
│  탭: [진행 상세] [대본] [결과]                         │
│                                                     │
│  진행 상세: 각 Step 실행 기록 테이블                    │
│  대본: 씬별 카드 + claim 뱃지 + 정책 플래그             │
│  결과: 비디오 플레이어 + 다운로드 + 유튜브 메타 복사      │
└─────────────────────────────────────────────────────┘
```

### 5. SSE 실시간 진행 (use-job-stream.ts)

```tsx
/**
 * const { status, isConnected } = useJobStream(jobId);
 * 
 * 1. SSE 연결: GET /api/v1/videos/{jobId}/stream?token={jwt}
 *    (EventSource는 커스텀 헤더 불가 → 쿼리 파라미터 토큰)
 * 
 * 2. 이벤트 핸들링:
 *    "progress" → 상태 업데이트
 *    "approval_required" → 승인 페이지 링크 표시
 *    "cost_warning" → toast 경고
 *    "completed" → download_url 저장, SSE 종료
 *    "failed" → error 표시, SSE 종료
 *    "cancelled" → 취소 표시, SSE 종료
 * 
 * 3. 재연결: 끊김 시 3초 후 자동 (최대 5회)
 *    ★ 재연결 성공 직후 api.jobs.getStatus(jobId) 호출하여 상태 동기화
 *    (끊긴 사이에 completed/failed가 지나갔을 수 있음 → 유령 상태 방지)
 * 4. Page Visibility API 연동:
 *    탭이 hidden → SSE 끊기 (브라우저 커넥션 6개 제한 방어)
 *    탭이 visible → SSE 재연결 + getStatus() 동기화
 * 5. fallback: 5회 실패 → polling (GET /status 5초 간격)
 * 5. cleanup: 언마운트 시 SSE 닫기
 */
```

### 6. 대본 승인 페이지

```
URL: /jobs/:jobId/approval

┌─────────────────────────────────────────────────────┐
│  ⚠️ 민감 주제 - 승인 필요                              │
│  민감도: [높음] | 경고: 주식 예측, 정치인 언급          │
├─────────────────────────────────────────────────────┤
│  제목 / 길이 / 씬 수 / 예상 비용                       │
├─────────────────────────────────────────────────────┤
│  씬 카드 리스트 (스크롤):                              │
│  ┌─ 씬 1: Hook ─────────────────────────────────┐  │
│  │  에셋: generated_image | ⏱️ 0:00~0:35         │  │
│  │  나레이션: "여러분, 최근 주식시장이..."           │  │
│  │  [fact] "코스피 2800선" (0.95)                  │  │
│  │  [inference] "상승세 지속" (0.6)                │  │
│  │  ⚠️ contains_stock_prediction                  │  │
│  └───────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│  [거부 (사유 입력)]   [수정 요청]   [승인하고 생성 시작]    │
│                                                     │
│  수정 요청 시:                                        │
│  - 추가 지시사항 textarea (예: "3번 씬의 투자 예측 표현 완화") │
│  - POST /api/v1/videos/{job_id}/retry               │
│    body: { from_step: "review", additional_instructions: "..." } │
│  - 새 job 생성 → 대본 재생성부터 재시작                  │
└─────────────────────────────────────────────────────┘
```

### 7. 관리자 페이지

```
URL: /admin (admin role만)

통계 카드: 오늘 생성 / 성공률 / 일 비용 / 활성 작업
일별 비용 차트 (Recharts, 최근 30일)
전체 Job 테이블 (필터: 상태, 사용자, 날짜)
액션: 상세보기, 강제취소
```

---

## 디자인 시스템

### JobPhase별 색상
```typescript
const PHASE_COLORS: Record<JobPhase, string> = {
  queued: "bg-slate-100 text-slate-700",
  extracting: "bg-blue-100 text-blue-700",
  normalizing: "bg-blue-100 text-blue-700",
  building_evidence: "bg-blue-100 text-blue-700",
  generating_script: "bg-indigo-100 text-indigo-700",
  reviewing_script: "bg-indigo-100 text-indigo-700",
  policy_review: "bg-amber-100 text-amber-700",
  awaiting_approval: "bg-yellow-100 text-yellow-800",
  generating_assets: "bg-purple-100 text-purple-700",
  assembling_video: "bg-orange-100 text-orange-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-slate-100 text-slate-500",
  rejected: "bg-red-100 text-red-600",
};
```

### ClaimType 뱃지
```typescript
const CLAIM_BADGES: Record<ClaimType, { color: string; label: string }> = {
  fact: { color: "bg-green-100 text-green-700", label: "사실" },
  inference: { color: "bg-yellow-100 text-yellow-700", label: "추론" },
  opinion: { color: "bg-orange-100 text-orange-700", label: "의견" },
};
```

### 반응형
```
Desktop (≥1024px): 2-column, 사이드바 펼침
Tablet (768~1023px): 사이드바 접힘, 1-column
Mobile (<768px): 하단 탭, 풀스크린 카드
```

---

## 구현 순서 (Phase별 프론트 + 백엔드 수정 포함)

### Phase 0: 기존 코드베이스 분석 (구현 전 필수)

```
구현을 시작하기 전에 현재 백엔드 구조를 먼저 분석한다.
바로 수정하지 말고 다음을 먼저 보고한 뒤에만 Phase 1로 넘어간다:

1. 현재 디렉토리 구조 요약
2. 인증 방식 (JWT 발급/검증, refresh token 유무, 미들웨어 구조)
3. API 라우트 현황 (엔드포인트 목록, 응답 스키마)
4. SSE 구현 방식 (이벤트 포맷, 인증 방식)
5. Celery task chain 구조 (approval/retry/cancel이 어떻게 동작하는지)
6. Object storage 연동 (presigned URL 생성 로직, 내부/외부 URL 분리 여부)
7. DB 모델 현황 (VideoJob, User 등의 실제 컬럼명)
8. 본 설계(아래 확정 API 스펙)와 충돌하는 지점
9. 재사용 가능한 기존 코드
10. 최소 수정 범위 제안

기존 코드와 충돌하는 경우:
- 새 구조를 밀어넣지 말고 기존 구조에 맞춰 확장한다.
- 필드명/엔드포인트 경로가 다르면 기존 것을 따르고, 프론트 타입을 그에 맞춘다.
- 응답 스키마가 다르면 기존 스키마 기준으로 프론트 타입을 수정한다.
```

---

### Phase 1: 프로젝트 셋업

**프론트엔드:**
1. Vite + React + TypeScript 프로젝트 생성 (frontend/ 디렉토리)
2. Tailwind CSS + PostCSS 설정
3. shadcn/ui 초기화
   - 필요 컴포넌트: button, input, card, dialog, select, switch, slider,
     badge, tabs, table, textarea, separator, dropdown-menu, avatar,
     alert, tooltip, label, form, sonner
4. 디렉토리 구조 생성
5. .env.example (VITE_API_BASE_URL=http://localhost:8000)
6. vite.config.ts (proxy: /api → http://localhost:8000)
7. src/config/env.ts
8. src/index.css (Tailwind directives + 다크모드 변수)

**백엔드 수정:**
9. `app/main.py`에 CORSMiddleware 추가 (없으면):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

10. [치명적] MinIO Presigned URL 내부/외부망 분리 (`object_store.py` 수정):
```python
"""
백엔드(Docker 내부)는 MinIO에 http://minio:9000 으로 접근한다.
그래서 생성되는 Presigned URL도 http://minio:9000/... 이 된다.

문제: 브라우저는 사용자 PC에서 실행되므로 'minio:9000' 호스트를
찾을 수 없어 영상 재생/다운로드가 100% 실패한다.
(ERR_NAME_NOT_RESOLVED)

해결: .env에 S3_PUBLIC_URL 환경변수를 추가하고,
클라이언트에 반환하는 URL은 public URL로 치환한다.

.env 추가:
  S3_ENDPOINT_URL=http://minio:9000        # 백엔드 내부 통신용
  S3_PUBLIC_URL=http://localhost:9000       # 브라우저 접근용 (프로덕션은 실제 도메인)

object_store.py 수정:
  def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
      url = self.client.generate_presigned_url(...)  # http://minio:9000/...
      # 내부 URL을 외부 URL로 치환
      if settings.s3_public_url:
          url = url.replace(settings.s3_endpoint_url, settings.s3_public_url)
      return url

config.py에 추가:
  s3_public_url: str = "http://localhost:9000"
"""
```

---

### Phase 2: 인프라 레이어

**프론트엔드:**
10. types/ 전체 타입 정의 (위 api.ts 내용 전부)
11. lib/utils.ts (cn, formatDuration, formatCost, formatDate)
12. stores/auth-store.ts (Zustand)
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
13. stores/theme-store.ts (light/dark/system)
14. lib/axios.ts
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
15. lib/sse.ts
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

**백엔드 수정:**
16. SSE 엔드포인트(`stream.py`)에서 **쿼리 파라미터 토큰도 허용**하도록 수정:
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

17. 백엔드 응답에 **job 소유자의 목록 조회 API** 확인/추가:
```python
"""
GET /api/v1/videos → 현재 인증된 사용자의 job 목록 반환
이미 있으면 확인만, 없으면 추가.

응답: list[JobStatusResponse]
정렬: created_at DESC
"""
```

18. 백엔드 **Step 실행 기록 조회 API** 확인/추가:
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

---

### Phase 3: 레이아웃 + 인증

**프론트엔드:**
19. layout/root-layout.tsx (sidebar + main area)
20. layout/sidebar.tsx
```
좌측 (w-64, 접기 가능):
  로고: "AI Video Studio"
  네비: 📊 대시보드, 📋 내 영상
  관리자 섹션 (admin만): ⚙️ 관리
  하단: 다크모드 토글, 유저 이름, 로그아웃
```
21. layout/header.tsx (유저 정보, quota 잔여 표시)
22. layout/protected-route.tsx (token 없으면 /login redirect)
23. App.tsx (라우터):
```
/login, /register → 비인증
/ → ProtectedRoute → RootLayout
  /dashboard → DashboardPage
  /jobs/:jobId → JobDetailPage
  /jobs/:jobId/approval → ApprovalPage
  /admin → AdminPage (admin만)
```
24. pages/login-page.tsx + components/auth/login-form.tsx
25. pages/register-page.tsx + components/auth/register-form.tsx
26. hooks/use-auth.ts (TanStack Query mutation)

**백엔드 수정:**
27. 인증 응답에 **user + today_usage 포함** 확인 (확정 API 계약 참조):
```python
"""
POST /auth/login 응답 (확정):
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "user",
    "daily_quota": 5,
    "today_usage": 2
  }
}

today_usage: 오늘 이 사용자가 생성한 job 수.
DB에서 SELECT COUNT(*) FROM video_jobs
WHERE user_id = ? AND created_at >= today() 로 계산.

GET /auth/me도 동일한 user 객체 반환.
없으면 추가.
"""
```

---

### Phase 4: 대시보드 + 영상 생성

**프론트엔드:**
29. hooks/use-jobs.ts
```typescript
/**
 * useJobList(params?): TanStack Query
 *   GET /api/v1/videos?page=1&size=20&status=...
 *   → PaginatedResponse<JobStatusResponse>
 *   무한스크롤 또는 페이지네이션 UI 지원
 * 
 * useJobDetail(jobId): TanStack Query
 *   GET /api/v1/videos/{jobId} → JobStatusResponse
 *   enabled: !!jobId
 * 
 * useJobSteps(jobId): TanStack Query
 *   GET /api/v1/videos/{jobId}/steps → JobStepDetail[]
 * 
 * usePlaybackUrl(jobId): TanStack Query
 *   GET /api/v1/videos/{jobId}/playback → { url: string }
 *   enabled: phase === 'completed'
 *   staleTime: 30분 (presigned URL 유효기간 고려)
 * 
 * useCreateJob(): TanStack Query mutation
 *   POST /api/v1/videos → { job_id }
 *   onSuccess: queryClient.invalidateQueries({ queryKey: ['jobs'] })
 *             + navigate(`/jobs/${data.job_id}`)
 *   onError: toast
 */
```
30. components/jobs/source-input-list.tsx (동적 URL 입력)
31. components/jobs/job-create-form.tsx (Zod + React Hook Form)
32. components/jobs/job-card.tsx
33. components/jobs/job-list.tsx
34. pages/dashboard-page.tsx

**백엔드 수정:**
35. POST /api/v1/videos 응답 형태 확인:
```python
"""
프론트가 기대하는 응답:
  201 Created
  { "job_id": "uuid-string" }

현재 응답이 다른 형태라면 맞춰야 함.

또한 idempotency_key 중복 시:
  409 Conflict
  { "detail": "Duplicate request", "job_id": "기존-uuid" }
프론트에서 409를 받으면 기존 job_id로 navigate.
"""
```

36. GET /api/v1/videos 목록 응답 확인 (확정: 페이지네이션):
```python
"""
응답 (확정):
{
  "items": [ JobStatusResponse, ... ],
  "total": 42,
  "page": 1,
  "size": 20,
  "has_next": true
}

query params: ?page=1&size=20&status=completed

정렬: created_at DESC
필터: 현재 인증된 사용자의 job만
기존이 단순 배열이면 페이지네이션 객체로 감싸도록 수정.
"""
```

---

### Phase 5: 실시간 진행 + 상세

**프론트엔드:**
37. hooks/use-job-stream.ts (SSE + polling fallback)
38. components/jobs/job-progress.tsx
```tsx
/**
 * 시각 요소:
 * 1. 가로 스텝퍼:
 *    완료=초록●, 진행중=파랑◐(pulse), 대기=회색○, 실패=빨강✕, 승인대기=노랑⏸
 * 
 * 2. 프로그레스 바 (shimmer 애니메이션)
 * 
 * 3. 상세 텍스트 + 경과 시간 카운터
 * 
 * 4. 비용 뱃지: "$0.52 / $2.00"
 *    80%이상: yellow, 초과: red
 * 
 * 5. 연결 상태: SSE=초록"실시간", Polling=노랑"폴링", 끊김=빨강
 */
```
39. components/jobs/job-progress-steps.tsx (Step별 테이블)
40. components/jobs/job-cost-badge.tsx
41. components/jobs/job-actions.tsx (취소/재시도/다운로드)
```
버튼 표시 규칙 (상태 전이표 기반):

  const TERMINAL_STATES = ['completed', 'failed', 'cancelled', 'rejected'];
  const canCancel = !TERMINAL_STATES.includes(phase);
  const canApprove = phase === 'awaiting_approval';
  const canReject = phase === 'awaiting_approval';
  const canRetry = TERMINAL_STATES.includes(phase);
  const canDownload = phase === 'completed';

  retry 시 주의:
  - 새 job이 생성됨 (기존 job은 그대로 유지)
  - 응답: { job_id: "새-uuid", parent_job_id: "기존-uuid" }
  - navigate(`/jobs/${newJobId}`)로 새 job 상세로 이동
  - 기존 job 상세에는 "재시도본이 있습니다" 링크 표시

  모든 버튼에 mutation.isPending 동안 disabled + 스피너.
```
42. hooks/use-job-actions.ts
```typescript
/**
 * useCancelJob(): mutation → POST /api/v1/videos/{jobId}/cancel
 * useRetryJob(): mutation → POST /api/v1/videos/{jobId}/retry
 * useApproveJob(): mutation → POST /api/v1/videos/{jobId}/approve
 * useRejectJob(): mutation → POST /api/v1/videos/{jobId}/reject
 * 
 * ★ 모든 mutation의 onSuccess에 반드시:
 *   queryClient.invalidateQueries({ queryKey: ['jobs'] })
 *   queryClient.invalidateQueries({ queryKey: ['job', jobId] })
 *   queryClient.invalidateQueries({ queryKey: ['job-steps', jobId] })
 * 캐시 무효화를 안 하면 새로고침 전까지 대시보드/상세가 이전 상태로 남음.
 * 
 * ★ 낙관적 업데이트(Optimistic Updates) 적용:
 *   cancel, approve, reject 등은 API 응답 전에 UI를 먼저 변경한다.
 *   체감 반응 속도를 0ms로 만들기 위함.
 * 
 *   패턴:
 *   useCancelJob = useMutation({
 *     mutationFn: (jobId) => api.jobs.cancel(jobId),
 *     onMutate: async (jobId) => {
 *       await queryClient.cancelQueries({ queryKey: ['job', jobId] });
 *       const previous = queryClient.getQueryData(['job', jobId]);
 *       queryClient.setQueryData(['job', jobId], (old) => ({
 *         ...old, phase: 'cancelled', is_cancelled: true
 *       }));
 *       return { previous };
 *     },
 *     onError: (err, jobId, context) => {
 *       queryClient.setQueryData(['job', jobId], context.previous); // 롤백
 *       toast.error('취소에 실패했습니다');
 *     },
 *     onSettled: (_, __, jobId) => {
 *       queryClient.invalidateQueries({ queryKey: ['jobs'] });
 *       queryClient.invalidateQueries({ queryKey: ['job', jobId] });
 *     },
 *   });
 * 
 *   approve, reject도 동일 패턴 적용.
 */
```
43. components/jobs/job-detail-panel.tsx
44. pages/job-detail-page.tsx (탭: 진행/대본/결과)

```
결과 탭 비디오 플레이어 구현 시 주의:

<video
  src={downloadUrl}
  controls
  preload="metadata"
  playsInline                          // iOS 인라인 재생 (전체화면 강제 방지)
  controlsList="nodownload"            // 브라우저 기본 다운로드 숨김 (커스텀 다운로드 버튼 사용)
  className="w-full rounded-lg"
/>

- iOS Safari: playsInline 필수, 없으면 전체화면으로 강제 전환됨
- 모바일 자동재생: autoPlay를 쓰려면 muted 필수 (브라우저 정책)
  → 우리 영상은 나레이션이 있으므로 autoPlay 사용하지 않음
- 다운로드는 별도 버튼 (GET /download 엔드포인트 경유)

비용 초과 실패 시 에러 UI 세분화:
  job.phase === "failed" 일 때, error_message를 파싱하여:
  - "budget_exceeded" → 일반 에러가 아닌 전용 UI 표시:
    "예산($2.00)을 초과하여 생성이 중단되었습니다.
     예산을 높여서 다시 시도하거나, 이미지 수를 줄여보세요."
    + [예산 높여서 재시도] 버튼 (retry with higher budget)
  - 그 외 에러 → 일반 에러 카드 + [재시도] 버튼
```

**백엔드 수정:**
45. SSE 이벤트 **data 포맷** 확인:
```python
"""
프론트의 EventSource는 event.data를 JSON.parse한다.
백엔드 SSE가 보내는 각 이벤트가 아래 형태인지 확인:

event: progress
data: {"phase":"generating_assets","progress_percent":67,"current_step_detail":"씬 5/16 이미지 생성 중...","cost_usd":0.52}

event: completed
data: {"download_url":"https://...presigned...","thumbnail_url":"...","duration_sec":720,"total_cost":0.85}

event: approval_required
data: {"script_preview_url":"https://...presigned...","sensitivity_level":"high"}

event: failed
data: {"error_message":"DALL-E rate limit","last_completed_step":"review","can_retry":true}

event: cost_warning
data: {"current_cost":1.6,"budget":2.0,"message":"예산의 80%를 사용했습니다"}

event: cancelled
data: {}

주의: 
- 각 이벤트에 'event:' 라인과 'data:' 라인이 모두 있어야 함
- 'data:' 값은 유효한 JSON이어야 함
- 이벤트 간 빈 줄(\n\n)으로 구분
- sse-starlette 사용 시 ServerSentEvent(data=json.dumps(...), event="progress")
"""
```

46. [치명적] **비디오 다운로드/재생 URL 전략** 확인:
```python
"""
★ Presigned URL 만료 대응 (핵심):
  사용자가 완료 화면을 띄워둔 채 2시간 뒤 다운로드 클릭 시
  Presigned URL이 만료되어 403 에러 발생.

  해결: SSE completed 이벤트의 download_url을 직접 쓰지 않는다.
  대신 프론트는 항상 아래 엔드포인트를 통해 접근:

  GET /api/v1/videos/{job_id}/download
    → 호출 시점에 1시간짜리 신규 Presigned URL을 발급
    → 307 Redirect로 해당 URL로 보냄
    → 프론트: <a href="/api/v1/videos/{jobId}/download">다운로드</a>

  GET /api/v1/videos/{job_id}/thumbnail
    → 같은 방식으로 썸네일 Presigned URL 신규 발급 + redirect

  이 방식이면 URL 만료 걱정 없음.
  SSE의 download_url은 즉시 재생용으로만 사용하되,
  프론트에서 다운로드 버튼은 반드시 위 엔드포인트를 가리켜야 함.

★ MP4 스트리밍 재생 (Range Request 지원):
  프론트 결과 탭에서 <video src="...">로 15분 영상을 재생한다.
  사용자가 10분 지점으로 Seek하면 브라우저가 Range Request를 보낸다.

  확인 사항:
  1. S3 업로드 시 Content-Type을 "video/mp4"로 명시적 지정
  2. MinIO/S3는 기본적으로 Range Request(HTTP 206) 지원하므로
     별도 설정 불필요. 단, Presigned URL 방식이면 문제없음.
  3. 만약 백엔드가 프록시로 파일을 중계한다면(StreamingResponse),
     Range 헤더를 파싱하여 부분 응답 구현 필요 → 복잡하므로
     Presigned URL redirect 방식을 권장.
  4. [치명적] FFmpeg 인코딩 시 -movflags +faststart 플래그 필수:
     FFmpeg 기본 인코딩은 메타데이터(moov atom)를 파일 맨 끝에 기록한다.
     이 경우 수백MB 파일 다운로드가 100% 끝날 때까지
     브라우저가 영상을 1초도 재생할 수 없고 Seek도 불가능하다.
     -movflags +faststart를 추가하면 moov atom이 파일 앞으로 이동하여
     다운로드 시작 즉시 재생 + Seek이 가능해진다.
     
     백엔드 step5_assemble.py의 FFmpeg 옵션 확인:
       -c:v libx264 -preset medium -crf 23
       -c:a aac -b:a 192k
       -r 30 -s 1920x1080
       -movflags +faststart    ← 이 플래그가 반드시 있어야 함
     
     없으면 추가할 것.

  프론트:
  <video src={downloadUrl} controls preload="metadata" />
  downloadUrl은 Presigned URL (직접 S3/MinIO 접근)

★ MinIO CORS 설정:
  브라우저에서 <video>로 MinIO URL을 직접 재생하려면
  MinIO에도 CORS가 설정되어야 함.

  docker-compose 초기화 스크립트 또는 mc 커맨드:
    mc alias set myminio http://localhost:9000 minioadmin minioadmin
    mc cors set myminio/video-pipeline-outputs --allow-origin "http://localhost:5173"
    mc cors set myminio/video-pipeline-assets --allow-origin "http://localhost:5173"
  
  또는 MinIO 환경변수:
    MINIO_BROWSER_REDIRECT_URL=http://localhost:9001
    MINIO_CORS_ALLOW_ORIGIN=http://localhost:5173
"""
```

47. **GET /api/v1/videos/{job_id}/script** 응답 확인:
```python
"""
프론트 대본 탭과 승인 페이지에서 사용.
FullScript JSON을 직접 반환하거나, presigned URL로 반환하거나.

방법 1 (권장): 직접 JSON 반환
  GET /api/v1/videos/{job_id}/script → FullScript JSON body

방법 2: presigned URL 반환 후 프론트에서 fetch
  GET /api/v1/videos/{job_id}/script → { "url": "https://...presigned..." }
  프론트에서 해당 URL을 다시 fetch

방법 1이 프론트 구현이 간단함. 대본 JSON은 크기가 작으므로 직접 반환 권장.
"""
```

---

### Phase 6: 대본 승인

**프론트엔드:**
48. components/approval/script-scene-card.tsx
49. components/approval/claim-badge.tsx (fact=초록, inference=노랑, opinion=주황)
50. components/approval/policy-flag-alert.tsx
51. components/approval/script-preview.tsx (씬 카드 리스트)
52. components/approval/approval-actions.tsx (승인/거부 + 거부 사유)
53. pages/approval-page.tsx

**백엔드 수정:**
54. approve/reject 엔드포인트 응답 확인:
```python
"""
POST /api/v1/videos/{job_id}/approve
  - 200 OK → 프론트에서 job-detail로 navigate, SSE로 이후 진행 수신
  - 404: job 없음
  - 400: 이미 승인됨 / 승인 대기 상태가 아님
  - 403: 소유자가 아님

POST /api/v1/videos/{job_id}/reject
  body: { "reason": "optional string" }
  - 200 OK → 프론트에서 대시보드로 navigate
  - 같은 에러 처리

approve 후 파이프라인이 자동 재개되는지 확인.
(human_gate step에서 중단 → approve 시 Celery task 체인 트리거)
"""
```

55. **승인 대기 중인 job 알림** 확인:
```python
"""
프론트 대시보드의 job-list에서 awaiting_approval 상태인 job이 있으면
눈에 띄게 표시해야 함.

GET /api/v1/videos 응답의 각 job에 phase가 포함되어 있으면
프론트에서 필터링 가능. 별도 API 불필요.
"""
```

---

### Phase 7: 관리자

**프론트엔드:**
56. hooks/use-admin-stats.ts
57. components/admin/admin-stats-cards.tsx
58. components/admin/admin-cost-chart.tsx (Recharts AreaChart, 최근 30일)
59. components/admin/admin-job-table.tsx (필터 + 페이지네이션)
60. pages/admin-page.tsx

**백엔드 수정:**
61. 관리자 API 응답 형태 확인 (확정 API 계약 참조):
```python
"""
GET /admin/stats 응답 (확정):
{
  "today_jobs": 23,
  "success_rate": 0.87,
  "daily_cost_usd": 18.50,
  "active_jobs": 3
}

GET /admin/jobs 응답 (확정, 페이지네이션):
  query params: ?status=completed&page=1&size=20
  {
    "items": [
      {
        "job_id": "...",
        "user_email": "kim@...",
        "topic": "주식 전망",
        "phase": "completed",
        "total_cost_usd": 0.85,
        "created_at": "2026-03-30T..."
      }
    ],
    "total": 156, "page": 1, "size": 20, "has_next": true
  }
  user_email을 포함하려면 VideoJob → User join 필요. 없으면 추가.

GET /admin/stats/daily?days=30 응답 (확정):
  [
    { "date": "2026-03-01", "jobs": 15, "cost_usd": 12.50, "success_count": 13, "fail_count": 2 },
    ...
  ]
  이 엔드포인트가 없으면 추가.
"""
```

62. **관리자 권한 체크** 확인:
```python
"""
admin 라우트에 require_admin dependency가 걸려있는지 확인.
role != "admin"이면 403 반환.

프론트에서도 이중 체크하지만, 백엔드 가드가 본질.
"""
```

---

### Phase 8: 마무리

**프론트엔드:**
63. 다크모드 전체 검증
    - shadcn/ui는 기본 다크모드 지원
    - 커스텀 컴포넌트의 dark: 클래스 확인
64. 반응형 전체 검증
    - 모바일: 사이드바 → 하단 탭, 폼/목록 단일 컬럼
    - 태블릿: 사이드바 접힘
65. 에러 상태 UI
    - 빈 목록: "아직 생성한 영상이 없습니다" + CTA 버튼
    - 네트워크 에러: retry 버튼이 있는 에러 카드
    - 404: "영상을 찾을 수 없습니다"
66. 로딩 스켈레톤
    - job-list: 카드 스켈레톤 3개
    - job-detail: 프로그레스 바 스켈레톤
    - admin-table: 행 스켈레톤
67. ErrorBoundary 래핑 (각 페이지)
68. README.md

**백엔드 수정:**
69. 백엔드 에러 응답 **일관성** 확인:
```python
"""
프론트 axios interceptor가 에러를 파싱하려면
백엔드 에러 응답이 일관된 형태여야 함:

{
  "detail": "에러 메시지 (한글)"
}

또는 validation error:
{
  "detail": [
    {
      "loc": ["body", "topic"],
      "msg": "주제를 입력해주세요",
      "type": "value_error"
    }
  ]
}

FastAPI 기본 HTTPException은 이 형태를 따르지만,
커스텀 에러 핸들러가 있으면 형태가 다를 수 있으니 확인.

특히:
- 401: { "detail": "인증이 필요합니다" }
- 403: { "detail": "권한이 없습니다" }
- 404: { "detail": "영상을 찾을 수 없습니다" }
- 409: { "detail": "이미 처리된 요청입니다", "job_id": "..." }
- 429: { "detail": "요청 제한을 초과했습니다" }
"""
```

70. **docker-compose.yml**에 프론트엔드 서비스 추가 (선택):
```yaml
"""
개발 환경 + 프로덕션 환경 모두 대응.

  frontend-dev:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/src:/app/src
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    depends_on:
      - api

Dockerfile.dev (개발용):
  FROM node:20-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm install
  COPY . .
  CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

Dockerfile (프로덕션 - Multi-stage Build):
  # Stage 1: 빌드
  FROM node:20-alpine AS builder
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci
  COPY . .
  RUN npm run build

  # Stage 2: Nginx로 서빙
  FROM nginx:alpine
  COPY --from=builder /app/dist /usr/share/nginx/html
  COPY nginx.conf /etc/nginx/conf.d/default.conf
  EXPOSE 80
  CMD ["nginx", "-g", "daemon off;"]

nginx.conf:
  server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # SPA fallback (React Router)
    location / {
      try_files $uri $uri/ /index.html;
    }

    # API 프록시 (프로덕션)
    location /api/ {
      proxy_pass http://api:8000;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE 프록시 (buffering 끄기 필수)
    location ~* /api/v1/videos/.*/stream {
      proxy_pass http://api:8000;
      proxy_set_header Host $host;
      proxy_buffering off;          # SSE 스트리밍 필수
      proxy_cache off;
      proxy_read_timeout 86400s;    # 긴 연결 유지
    }

    # 정적 자산 캐싱
    location ~* \.(js|css|png|jpg|svg|ico|woff2)$ {
      expires 1y;
      add_header Cache-Control "public, immutable";
    }
  }
"""
```

---

## 중요 제약사항

1. **TypeScript strict mode** 필수. any 금지.
2. **shadcn/ui 컴포넌트 우선**. 직접 HTML보다 shadcn.
3. **HTTP 데이터 fetching/mutation은 TanStack Query 사용**. 단, SSE/EventSource, BroadcastChannel, Page Visibility API, DOM 이벤트 처리에는 useEffect 허용.
4. **폼은 Zod schema + React Hook Form**. 인라인 validation 금지.
5. **SSE는 use-job-stream 훅으로만**. 컴포넌트에서 직접 EventSource 금지.
6. **다크모드 필수**. 모든 컴포넌트 dark: 확인.
7. **한국어 UI**. 모든 라벨, 메시지, placeholder.
8. **접근성**: 키보드 네비게이션, aria-label, focus ring.
9. **ErrorBoundary**: 각 페이지에 래핑.
10. **컴포넌트는 가급적 200줄 이하** 유지. 초과 시 시각 블록, 훅, 하위 컴포넌트로 분리하되 가독성을 우선한다.
11. **백엔드 수정 시**: 기존 로직을 깨뜨리지 말 것. 추가/확장만.
12. **백엔드 수정 시**: 기존 테스트가 있으면 수정 후 테스트 통과 확인.
13. **다운로드/썸네일/재생 URL은 항상 엔드포인트 경유** (/download, /thumbnail, /playback). presigned URL 직접 저장 금지.
14. **Mutation 후 캐시 무효화 필수**. invalidateQueries 빠뜨리지 말 것.
15. **SSE 재연결 시 getStatus() 동기화 필수**. 유령 상태 방지.
16. **Page Visibility API 연동 필수**. 탭 hidden 시 SSE 끊기. 브라우저 커넥션 6개 제한 방어.
17. **cancel/approve/reject에 낙관적 업데이트(Optimistic Updates) 적용**. onMutate에서 캐시 먼저 변경, onError에서 롤백.
18. **백엔드 FFmpeg에 -movflags +faststart 필수**. 없으면 브라우저 스트리밍 재생 불가.
19. **Action 버튼(생성, 취소, 승인, 거부)에 Loading 상태 필수**. mutation.isPending 동안 disabled + 스피너 표시. 연타 방지.
20. **폼 제출 버튼은 isSubmitting 상태 체크**. React Hook Form의 formState.isSubmitting 사용.
21. **다중 탭 동기화**: BroadcastChannel로 job 상태 변경을 탭 간 전파.
22. **비디오 플레이어**: playsInline, controlsList="nodownload" 필수. 모바일 정책 대응.
23. **비용 초과 실패는 전용 에러 UI** 표시. 일반 에러와 구분하여 예산 상향 재시도 유도.
24. **프로덕션 Dockerfile은 Multi-stage Build**: npm run build → Nginx alpine으로 /dist 서빙.
25. **상태 동기화 규칙 준수**: updated_at 비교, terminal state 보호. 위 '상태 동기화 우선순위 규칙' 참조.
26. **상태 전이표 준수**: 위 'Job 상태 전이표' 기반으로 버튼 활성화/비활성화 처리.
27. **API 계약 확정 스펙 준수**: 위 '확정 API 계약' 외의 선택형 구현 금지.
28. **외부 의존이나 미확정 사항은 추정하지 말고 TODO 주석**으로 명시. 허위 완성도보다 정확한 완성도 우선.

---

## 시작 명령

**Phase 0부터 시작한다.**
먼저 기존 백엔드 코드베이스를 분석하고 보고한 뒤, 승인을 받고 Phase 1로 넘어간다.
각 Phase 완료 시 무엇을 구현/수정했는지 알려주고 다음 Phase로 넘어가줘.
실제 동작하는 코드를 작성하되, 외부 의존이나 미확정 사항은 추정하지 말고 TODO 주석으로 명시한다.
기존 백엔드 구조와 충돌하면 기존 구조를 따르고, 프론트 타입을 그에 맞춘다.