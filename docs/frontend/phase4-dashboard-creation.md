# Phase 4: 대시보드 + 영상 생성

## 목표
대시보드 메인 페이지와 영상 생성 폼, Job 목록을 구현한다.
백엔드 POST/GET /api/v1/videos 응답 형태를 확인/수정한다.

---

## 구현 항목

### 프론트엔드

#### 29. hooks/use-jobs.ts
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

#### 30. components/jobs/source-input-list.tsx
- 동적 URL 입력 리스트

#### 31. components/jobs/job-create-form.tsx
- Zod + React Hook Form
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

#### 32. components/jobs/job-card.tsx

#### 33. components/jobs/job-list.tsx

#### 34. pages/dashboard-page.tsx
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

---

### 백엔드 수정

#### 35. POST /api/v1/videos 응답 형태 확인
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

#### 36. GET /api/v1/videos 목록 응답 확인 (확정: 페이지네이션)
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
