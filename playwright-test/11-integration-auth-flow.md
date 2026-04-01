# 11. 통합 테스트: 인증 플로우

## 목적
회원가입 -> 로그인 -> 대시보드 진입 -> 네비게이션 -> 로그아웃의 전체 인증 플로우를 E2E로 테스트합니다.

---

## 통합 시나리오 1: 신규 사용자 전체 인증 플로우

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘.
각 단계마다 browser_snapshot으로 상태를 확인하고 기대 결과와 비교해줘:

### Step 1: 서비스 상태 확인
1. browser_navigate로 http://localhost:8000/health 에 접속
2. 모든 컴포넌트가 healthy인지 확인

### Step 2: 프론트엔드 초기 접속 → 로그인 리다이렉트
3. browser_navigate로 http://localhost:5173 에 접속
4. /login으로 리다이렉트 확인

### Step 3: 로그인 페이지에서 회원가입 링크 이동
5. "회원가입" 링크 클릭 → /register 이동 확인

### Step 4: 회원가입
6. 고유 이메일로 회원가입:
   - 이메일: "integ-auth-{현재시간}@example.com"
   - 비밀번호: "integTestPass123"
   - 비밀번호 확인: "integTestPass123"
7. "회원가입" 버튼 클릭
8. **대시보드(/dashboard)로 직접 이동** 확인 (로그인 페이지가 아님!)
9. "회원가입 완료" 토스트 확인

### Step 5: 대시보드 상태 확인
10. Sidebar의 "AI Video Studio" 로고 확인
11. Sidebar 네비게이션: "대시보드"(active), "내 영상"
12. Header: 할당량 배지 "오늘 0/5", 이메일
13. 본문: "영상 생성" 카드 + "아직 생성된 영상이 없습니다."

### Step 6: Sidebar 네비게이션 테스트
14. "내 영상" 클릭 → /jobs 이동 확인
15. "대시보드" 클릭 → /dashboard 복귀 확인

### Step 7: 인증 상태 유지 확인 (페이지 새로고침)
16. browser_navigate로 http://localhost:5173/dashboard 재접속
17. 여전히 대시보드에 머물러 있는지 확인 (JWT persist)

### Step 8: 로그아웃
18. Sidebar 하단 "로그아웃" 버튼 클릭
19. /login 페이지로 이동 확인
20. browser_evaluate: localStorage의 auth-storage에서 token이 null인지 확인

### Step 9: 로그아웃 후 보호 페이지 차단
21. browser_navigate로 /dashboard 접속 시도
22. /login으로 리다이렉트 확인

### Step 10: 재로그인
23. 방금 가입한 이메일/비밀번호로 로그인
24. 대시보드 정상 진입 확인
25. "로그인 성공" 토스트 확인

각 단계의 성공/실패를 리포트로 작성해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 1 | 헬스체크 healthy |
| 2 | /login 리다이렉트 |
| 3 | /register 이동 |
| 4 | 회원가입 → /dashboard 직접 이동 |
| 5 | 빈 대시보드 정상 렌더링 |
| 6 | Sidebar 네비게이션 동작 |
| 7 | 새로고침 후 인증 유지 |
| 8 | 로그아웃 → /login 이동 |
| 9 | 보호 페이지 접근 차단 |
| 10 | 재로그인 성공 |

---

## 통합 시나리오 2: 토큰 무효화 → 자동 로그아웃 → 재로그인

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 정상 로그인
1. test@example.com / testpassword123 로 로그인
2. 대시보드 진입 확인

### Step 2: 토큰 강제 무효화
3. browser_evaluate로 다음 실행:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   data.state.token = 'invalid_expired_token';
   localStorage.setItem('auth-storage', JSON.stringify(data));
   ```
4. 페이지 새로고침

### Step 3: 자동 로그아웃 확인
5. browser_snapshot으로 결과 확인
6. axios 401 인터셉터 동작:
   - useAuthStore.logout() → token/user 클리어
   - window.location.href = "/login"
7. /login 페이지에 도달했는지 확인

### Step 4: 재로그인 정상 동작
8. test@example.com / testpassword123 로 다시 로그인
9. 대시보드 정상 진입 확인
10. Header에 이메일과 할당량이 표시되는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 토큰 무효화됨 |
| 3 | 401 → 자동 로그아웃 → /login |
| 4 | 재로그인 성공 |

---

## 통합 시나리오 3: 다크 모드에서의 인증 플로우

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 로그인
1. test@example.com으로 로그인

### Step 2: 다크 모드 전환
2. Sidebar 하단 테마 토글 클릭 (다크 모드로)
3. browser_snapshot으로 다크 모드 적용 확인

### Step 3: 로그아웃 후 재로그인
4. 로그아웃
5. 로그인 페이지에서 다크 모드가 유지되는지 확인
6. 재로그인 → 대시보드에서도 다크 모드 유지 확인

### Step 4: 다크 모드 복원
7. 라이트 모드로 복원

결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 테마 설정이 세션 간 유지 (themeStore persist)

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(11-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
