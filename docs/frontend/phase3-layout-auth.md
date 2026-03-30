# Phase 3: 레이아웃 + 인증

## 목표
앱 전체 레이아웃(사이드바, 헤더), 라우팅, 로그인/회원가입 페이지를 구현한다.
백엔드 인증 응답에 user + today_usage 포함을 확인한다.

---

## 구현 항목

### 프론트엔드

#### 19. layout/root-layout.tsx
- sidebar + main area 구조

#### 20. layout/sidebar.tsx
```
좌측 (w-64, 접기 가능):
  로고: "AI Video Studio"
  네비: 📊 대시보드, 📋 내 영상
  관리자 섹션 (admin만): ⚙️ 관리
  하단: 다크모드 토글, 유저 이름, 로그아웃
```

#### 21. layout/header.tsx
- 유저 정보, quota 잔여 표시

#### 22. layout/protected-route.tsx
- token 없으면 /login redirect

#### 23. App.tsx (라우터)
```
/login, /register → 비인증
/ → ProtectedRoute → RootLayout
  /dashboard → DashboardPage
  /jobs/:jobId → JobDetailPage
  /jobs/:jobId/approval → ApprovalPage
  /admin → AdminPage (admin만)
```

#### 24. pages/login-page.tsx + components/auth/login-form.tsx

#### 25. pages/register-page.tsx + components/auth/register-form.tsx

#### 26. hooks/use-auth.ts (TanStack Query mutation)

---

### 백엔드 수정

#### 27. 인증 응답에 user + today_usage 포함 확인
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
