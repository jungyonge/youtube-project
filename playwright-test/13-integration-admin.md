# 13. 통합 테스트: 관리자 워크플로우

## 목적
관리자가 전체 작업을 모니터링하고, 필터링/검색/강제 취소를 수행하며,
일반 사용자와의 권한 경계를 E2E로 테스트합니다.

---

## 통합 시나리오 1: 관리자 모니터링 및 강제 취소 플로우

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Phase 1: 일반 사용자로 작업 생성
1. test@example.com / testpassword123 로 로그인
2. 영상 생성:
   - 주제: "관리자 테스트용 영상 - AI 윤리와 규제"
   - 소스 URL: "https://example.com/ai-ethics"
   - "영상 생성 시작" 클릭
3. 작업 생성 확인, 작업 ID 기록
4. 작업 상세 페이지 확인

### Phase 2: 관리자 계정 전환
5. Sidebar "로그아웃" 클릭 → /login 이동
6. admin@example.com / adminpassword123 로 로그인
7. Sidebar에 "관리" 메뉴가 보이는지 확인
8. "관리" 클릭 → /admin 이동

### Phase 3: 관리자 통계 확인
9. 통계 카드 4개 확인:
   - "오늘 생성" 건수 > 0
   - "활성 작업" 건수 확인
   - "일 비용" 확인
   - "성공률" 확인
10. 비용 차트 렌더링 확인

### Phase 4: 작업 검색 및 필터링
11. 이메일 검색: "test@example.com" 입력
12. 테이블에 해당 사용자의 작업만 표시되는지 확인
13. Phase 1에서 생성한 작업이 목록에 있는지 확인
14. 상태 필터를 변경하며 결과 확인

### Phase 5: 강제 취소
15. Phase 1 작업이 아직 진행 중이면:
    - Ban 아이콘 버튼 클릭
    - "강제 취소되었습니다." 토스트 확인
    - 상태가 "취소됨"으로 변경 확인
16. 이미 terminal이면: Ban 버튼이 없는 것 확인

### Phase 6: 작업 상세 확인
17. Eye 아이콘 클릭 → 작업 상세 페이지 이동
18. 관리자도 다른 사용자의 작업 상세를 볼 수 있는지 확인
19. 뒤로가기로 /admin 복귀

각 단계의 결과를 리포트 형태로 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Phase | 기대 결과 |
|-------|-----------|
| 1 | 일반 사용자 작업 생성 |
| 2 | 관리자로 전환 |
| 3 | 통계 데이터 확인 |
| 4 | 필터/검색 동작 |
| 5 | 강제 취소 |
| 6 | 타 사용자 작업 상세 열람 |

---

## 통합 시나리오 2: 권한 경계 테스트 (API 레벨)

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 일반 사용자로 관리자 API 직접 호출
1. test@example.com으로 로그인
2. browser_evaluate로 관리자 API 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const token = data.state.token;
   const res = await fetch('http://localhost:8000/admin/stats', {
     headers: { 'Authorization': 'Bearer ' + token }
   });
   return { status: res.status };
   ```
3. 403 Forbidden 확인

### Step 2: 일반 사용자로 관리자 강제 취소 API 호출
4. browser_evaluate로:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const token = data.state.token;
   const res = await fetch('http://localhost:8000/admin/jobs/{someJobId}/force-cancel', {
     method: 'POST',
     headers: { 'Authorization': 'Bearer ' + token }
   });
   return { status: res.status };
   ```
5. 403 Forbidden 확인

### Step 3: 일반 사용자로 타인 작업 접근 시도
6. browser_evaluate로 다른 사용자의 작업 상태 조회:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const token = data.state.token;
   const res = await fetch('http://localhost:8000/api/v1/videos/{otherUserJobId}', {
     headers: { 'Authorization': 'Bearer ' + token }
   });
   return { status: res.status };
   ```
7. 403 Forbidden 확인

### Step 4: 일반 사용자로 /admin 페이지 접근
8. browser_navigate로 http://localhost:5173/admin 접속
9. /dashboard로 리다이렉트 확인 (ProtectedRoute requireAdmin)

### Step 5: 관리자로 같은 작업 접근
10. admin@example.com으로 로그인
11. browser_evaluate로 같은 API 호출 → 200 OK 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 1 | 일반 사용자 → admin API: 403 |
| 2 | 일반 사용자 → admin force-cancel: 403 |
| 3 | 일반 사용자 → 타인 작업: 403 |
| 4 | /admin → /dashboard 리다이렉트 |
| 5 | 관리자 → 같은 API: 200 |

---

## 통합 시나리오 3: 관리자 강제 취소 후 사용자 화면 반영

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Phase 1: 일반 사용자 작업 생성 및 상세 확인
1. test@example.com 으로 로그인
2. 영상 생성: 주제 "관리자 취소 반영 테스트"
3. 작업 상세 페이지에서 작업 ID 기록
4. 현재 상태 Badge 확인 (예: extracting)

### Phase 2: 관리자로 강제 취소
5. 로그아웃 → admin@example.com 로그인
6. /admin 이동 → 이메일 검색 "test@example.com"
7. Phase 1에서 생성한 작업의 강제 취소 버튼(Ban) 클릭
8. "강제 취소되었습니다." 토스트 확인

### Phase 3: 일반 사용자로 재확인
9. 로그아웃 → test@example.com 재로그인
10. /jobs/{jobId} 상세 페이지 접속
11. browser_snapshot으로 확인:
    - 상태가 "취소됨"으로 반영되었는지
    - "재시도" 버튼이 보이는지
    - "취소" 버튼은 사라졌는지

### Phase 4: 대시보드 목록 확인
12. 대시보드에서 해당 작업이 "취소됨" 상태로 표시되는지 확인

각 단계의 결과를 리포트 형태로 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Phase | 기대 결과 |
|-------|-----------|
| 1 | 작업 생성 성공 |
| 2 | 관리자 강제 취소 성공 |
| 3 | 일반 사용자 화면에 취소 상태 반영 |
| 4 | 대시보드 목록에도 반영 |

---

## 통합 시나리오 4: 관리자 JWT 조작 방지

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 일반 사용자 토큰으로 role 조작 시도
1. test@example.com 으로 로그인
2. browser_evaluate로 JWT 토큰 확인:
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   return data.state.token;
3. JWT payload를 디코딩하여 role 필드 확인 (role: "user")

### Step 2: 프론트엔드 레벨 role 조작
4. browser_evaluate로 localStorage의 user.role을 "admin"으로 변경:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   data.state.user.role = 'admin';
   localStorage.setItem('auth-storage', JSON.stringify(data));
   ```
5. 페이지 새로고침
6. browser_snapshot으로 확인:
   - Sidebar에 "관리" 메뉴가 보이는지 (프론트엔드 레벨)
   - /admin 접속 시도

### Step 3: 서버 레벨 검증
7. /admin 페이지에서 API 호출 시:
   - 실제 JWT의 role은 "user"이므로 서버가 403 반환하는지
   - 통계 데이터 로드 실패하는지
8. browser_console_messages에서 403 에러 확인
9. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 프론트엔드에서 role 변경 가능 (클라이언트 조작) |
| 3 | 서버가 JWT 기반으로 403 반환 → 실질적 접근 차단 |

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(13-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
