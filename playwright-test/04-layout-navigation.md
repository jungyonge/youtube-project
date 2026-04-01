# 04. 레이아웃 및 네비게이션 테스트 (단위) [신규]

## 목적
Sidebar, Header, 테마 전환, 로그아웃 등 공통 레이아웃 컴포넌트를 테스트합니다.

## 사전 조건
- 로그인 완료 상태

---

## 테스트 케이스 1: RootLayout 구조 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. test@example.com / testpassword123 으로 로그인
2. 대시보드에서 browser_snapshot으로 전체 레이아웃 캡처
3. 다음 레이아웃 구조가 존재하는지 확인:
   - 좌측 Sidebar:
     - "AI Video Studio" 로고 텍스트
     - "대시보드" 네비게이션 링크 (LayoutDashboard 아이콘)
     - "내 영상" 네비게이션 링크 (Film 아이콘)
     - 하단에 테마 토글 버튼 (Moon/Sun 아이콘)
     - 사용자 이메일 텍스트
     - "로그아웃" 버튼 (LogOut 아이콘)
   - 상단 Header:
     - 할당량 배지: "오늘 N/M" 형태 (daily_quota - today_usage)
     - 사용자 이메일
   - 메인 콘텐츠 영역
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Sidebar + Header + Main 3단 구조

---

## 테스트 케이스 2: Sidebar 네비게이션 링크 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서)

1. 대시보드에서 Sidebar의 "내 영상" 링크를 클릭
2. browser_snapshot으로 /jobs 페이지로 이동했는지 확인
3. "내 영상" 링크가 active 상태(하이라이트)인지 확인
4. Sidebar의 "대시보드" 링크를 클릭
5. browser_snapshot으로 /dashboard 페이지로 이동했는지 확인
6. "대시보드" 링크가 active 상태인지 확인
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- NavLink의 isActive에 따라 bg-accent 클래스 적용
- 페이지 전환 정상 동작

---

## 테스트 케이스 3: Sidebar 접기/펼치기

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서)

1. browser_snapshot으로 Sidebar 펼친 상태 확인 (w-64)
   - "AI Video Studio" 텍스트 보이는지
   - 네비게이션 라벨("대시보드", "내 영상") 보이는지
   - 로그아웃 텍스트 보이는지
2. Sidebar의 접기 버튼 (PanelLeftClose 아이콘) 을 클릭
3. browser_snapshot으로 접힌 상태 확인 (w-16)
   - "AI Video Studio" 텍스트가 숨겨졌는지
   - 네비게이션 라벨이 숨겨지고 아이콘만 보이는지
   - 이메일, 로그아웃 텍스트가 숨겨졌는지
4. 다시 펼치기 버튼 (PanelLeft 아이콘) 을 클릭
5. browser_snapshot으로 펼쳐진 상태 복원 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 접기: w-16, 아이콘만 표시
- 펼치기: w-64, 전체 라벨 표시

---

## 테스트 케이스 4: 다크/라이트 테마 전환

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서)

1. browser_snapshot으로 현재 테마 확인
2. Sidebar 하단의 테마 토글 버튼을 클릭
   - 현재 "다크 모드" 텍스트이면 → 다크로 전환
   - 현재 "라이트 모드" 텍스트이면 → 라이트로 전환
3. browser_snapshot으로 테마 변경 확인:
   - 배경색이 변경되었는지
   - 아이콘이 Sun ↔ Moon 으로 전환되었는지
   - 버튼 텍스트가 "라이트 모드" ↔ "다크 모드"로 변경되었는지
4. 다시 토글하여 원래 테마로 복원
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 테마 전환이 즉시 반영
- themeStore에 persist됨

---

## 테스트 케이스 5: Header 할당량 배지 표시

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서)

1. browser_snapshot으로 Header 영역 캡처
2. 다음을 확인:
   - "오늘 N/M" 형태의 할당량 배지가 보이는지
     (user.today_usage / user.daily_quota)
   - 남은 할당량(remaining = daily_quota - today_usage)이 0보다 크면 "secondary" 색상
   - 남은 할당량이 0이면 "destructive" (빨간색) 색상
   - 사용자 이메일이 표시되는지
3. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 할당량 정보가 실시간으로 표시
- 할당량 초과 시 빨간색 배지

---

## 테스트 케이스 6: 로그아웃 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. test@example.com으로 로그인
2. 대시보드에서 browser_snapshot으로 로그인 상태 확인
3. Sidebar 하단의 "로그아웃" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. 다음을 확인:
   - /login 페이지로 이동했는지
   - browser_evaluate로 localStorage 확인: auth-storage에서 token이 null인지
6. /dashboard로 다시 접속 시도
7. /login으로 리다이렉트되는지 확인
8. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 로그아웃 → token/user 클리어 → `/login` 이동
- 이후 보호 페이지 접근 불가

---

## 테스트 케이스 7: 관리자 Sidebar 메뉴 노출

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

### 일반 사용자로 확인
1. test@example.com으로 로그인
2. browser_snapshot으로 Sidebar 확인
3. "관리" 메뉴가 보이지 않는지 확인 (isAdmin() === false)

### 관리자로 확인
4. 로그아웃
5. admin@example.com / adminpassword123 으로 로그인
6. browser_snapshot으로 Sidebar 확인
7. "관리" 메뉴(Shield 아이콘)가 Separator 아래에 보이는지 확인
8. "관리" 메뉴 클릭하여 /admin 이동 확인

결과를 정리해서 알려줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 일반 사용자: "관리" 메뉴 숨김
- 관리자: "관리" 메뉴 표시 + 클릭 시 /admin 이동

---

## 테스트 케이스 8: 테마 설정 새로고침 후 유지 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서)

1. 현재 테마 확인 (라이트 또는 다크)
2. 테마 토글 클릭 → 테마 변경
3. browser_snapshot으로 변경 확인
4. browser_evaluate로 localStorage 확인:
   JSON.parse(localStorage.getItem('theme-storage'))
5. browser_navigate로 http://localhost:5173/dashboard 재접속 (새로고침)
6. browser_snapshot으로 테마가 유지되는지 확인
7. 로그아웃 → 재로그인
8. 테마가 여전히 유지되는지 확인 (themeStore persist)
9. 원래 테마로 복원
10. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 테마 설정이 새로고침, 재로그인 후에도 유지

---

## 테스트 케이스 9: Sidebar 현재 경로 하이라이트 정확성

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(로그인된 상태에서)

1. /dashboard 에서 "대시보드" 메뉴가 active(하이라이트) 상태인지 확인
2. "내 영상" 메뉴가 비활성 상태인지 확인
3. /jobs 로 이동
4. "내 영상" 메뉴가 active, "대시보드"가 비활성인지 확인
5. /jobs/{jobId} (작업 상세)로 이동
6. "내 영상" 메뉴가 여전히 active인지 확인 (하위 경로)
7. /admin 로 이동 (관리자인 경우)
8. "관리" 메뉴가 active인지 확인
9. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 현재 경로에 맞는 메뉴만 하이라이트

---

## 테스트 케이스 10: Header 이메일 표시 정확성

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. test@example.com 으로 로그인
2. Header에 "test@example.com" 이메일이 정확히 표시되는지 확인
3. 로그아웃 → admin@example.com 로그인
4. Header에 "admin@example.com"으로 변경되었는지 확인
5. 이메일이 길 경우 (예: very-long-email-address@subdomain.example.com)
   잘림(truncate) 처리 또는 전체 표시 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 현재 로그인한 사용자 이메일 정확히 표시

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(04-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
