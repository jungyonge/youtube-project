# Phase 6: 대본 승인

## 목표
대본 승인 페이지를 구현한다. 씬별 카드, claim 뱃지, 정책 플래그 표시, 승인/거부/수정 요청 기능을 포함한다.
백엔드 approve/reject 엔드포인트 응답과 승인 대기 알림을 확인한다.

---

## 구현 항목

### 프론트엔드

#### 48. components/approval/script-scene-card.tsx

#### 49. components/approval/claim-badge.tsx
- fact=초록, inference=노랑, opinion=주황

#### 50. components/approval/policy-flag-alert.tsx

#### 51. components/approval/script-preview.tsx
- 씬 카드 리스트

#### 52. components/approval/approval-actions.tsx
- 승인/거부 + 거부 사유 입력

#### 53. pages/approval-page.tsx

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

---

### 백엔드 수정

#### 54. approve/reject 엔드포인트 응답 확인
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

#### 55. 승인 대기 중인 job 알림 확인
```python
"""
프론트 대시보드의 job-list에서 awaiting_approval 상태인 job이 있으면
눈에 띄게 표시해야 함.

GET /api/v1/videos 응답의 각 job에 phase가 포함되어 있으면
프론트에서 필터링 가능. 별도 API 불필요.
"""
```
