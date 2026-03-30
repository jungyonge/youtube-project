# Phase 7: 관리자

## 목표
관리자 전용 페이지를 구현한다. 통계 카드, 일별 비용 차트, 전체 Job 테이블을 포함한다.
백엔드 관리자 API 응답 형태와 권한 체크를 확인한다.

---

## 구현 항목

### 프론트엔드

#### 56. hooks/use-admin-stats.ts

#### 57. components/admin/admin-stats-cards.tsx
- 오늘 생성 / 성공률 / 일 비용 / 활성 작업

#### 58. components/admin/admin-cost-chart.tsx
- Recharts AreaChart, 최근 30일

#### 59. components/admin/admin-job-table.tsx
- 필터 + 페이지네이션

#### 60. pages/admin-page.tsx
```
URL: /admin (admin role만)

통계 카드: 오늘 생성 / 성공률 / 일 비용 / 활성 작업
일별 비용 차트 (Recharts, 최근 30일)
전체 Job 테이블 (필터: 상태, 사용자, 날짜)
액션: 상세보기, 강제취소
```

---

### 백엔드 수정

#### 61. 관리자 API 응답 형태 확인 (확정 API 계약 참조)
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

#### 62. 관리자 권한 체크 확인
```python
"""
admin 라우트에 require_admin dependency가 걸려있는지 확인.
role != "admin"이면 403 반환.

프론트에서도 이중 체크하지만, 백엔드 가드가 본질.
"""
```
