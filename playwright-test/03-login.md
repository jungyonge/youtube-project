# 03. 로그인 테스트 (단위)

## 목적
로그인 폼의 입력 검증, 인증 성공/실패 시나리오를 테스트합니다.

### 핵심 동작 (use-auth.ts 기준)
- 성공 시: `setAuth(token, user)` → `toast.success("로그인 성공")` → `navigate("/dashboard")`
- 실패 시: `toast.error("이메일 또는 비밀번호가 올바르지 않습니다.")`

---

## 테스트 케이스 1: 로그인 페이지 렌더링 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. browser_snapshot으로 페이지 상태 캡처
3. 다음 요소가 존재하는지 확인:
   - "로그인" 제목 텍스트 (CardTitle, text-2xl)
   - "AI Video Studio에 로그인하세요" 설명 텍스트 (CardDescription)
   - "이메일" 라벨 + 입력 필드 (type: email, placeholder: "you@example.com")
   - "비밀번호" 라벨 + 입력 필드 (type: password, placeholder: "••••••••")
   - "로그인" 제출 버튼 (w-full)
   - "계정이 없으신가요? 회원가입" 링크 (/register로 이동)
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 모든 폼 요소가 정상 렌더링

---

## 테스트 케이스 2: 빈 폼 제출 시 유효성 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. 아무것도 입력하지 않고 "로그인" 버튼을 클릭
3. browser_snapshot으로 결과 확인
4. 유효성 검증 에러 메시지가 표시되는지 확인:
   - 이메일: "올바른 이메일을 입력하세요" (z.string().email())
   - 비밀번호: "비밀번호를 입력하세요" (z.string().min(1))
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 클라이언트 검증만 실행, API 호출 없음

---

## 테스트 케이스 3: 잘못된 비밀번호로 로그인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. 다음을 입력:
   - 이메일: "test@example.com"
   - 비밀번호: "wrongpassword"
3. "로그인" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. 다음을 확인:
   - "이메일 또는 비밀번호가 올바르지 않습니다." 토스트 에러가 표시되는지
     (useLogin의 onError 토스트, sonner Toaster 우측 상단)
   - 로그인 페이지에 머물러 있는지
   - 버튼이 다시 "로그인" 텍스트로 복원되었는지 (isPending 해제)
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 401 → 토스트 에러, 페이지 유지

---

## 테스트 케이스 4: 존재하지 않는 계정으로 로그인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. 다음을 입력:
   - 이메일: "nonexistent@example.com"
   - 비밀번호: "anypassword123"
3. "로그인" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. "이메일 또는 비밀번호가 올바르지 않습니다." 토스트 에러가 표시되는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 같은 에러 메시지 (계정 존재 여부를 구분하지 않음 — 보안)

---

## 테스트 케이스 5: 정상 로그인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. browser_snapshot으로 현재 상태 확인
3. 다음을 입력:
   - 이메일: "test@example.com"
   - 비밀번호: "testpassword123"
4. "로그인" 버튼을 browser_click으로 클릭
5. 잠시 대기 후 browser_snapshot으로 결과 확인
6. 다음을 확인:
   - 대시보드(/dashboard)로 이동했는지
   - "로그인 성공" 토스트가 표시되는지
   - Sidebar가 보이는지 (대시보드, 내 영상 메뉴)
   - Header에 할당량 배지 "오늘 N/M"가 표시되는지
   - Header에 사용자 이메일 "test@example.com"이 표시되는지
7. browser_evaluate로 localStorage 확인:
   - JSON.parse(localStorage.getItem('auth-storage'))에 token과 user가 저장되었는지
8. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 로그인 성공 → 대시보드 이동
- JWT 토큰이 Zustand persist → localStorage에 저장
- Header에 할당량 + 이메일 표시

---

## 테스트 케이스 6: 회원가입 페이지 링크 이동

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. "회원가입" 링크를 클릭
3. browser_snapshot으로 결과 확인
4. 회원가입 페이지(/register)로 정상 이동했는지 확인
5. "회원가입" 제목과 "새 계정을 만들어 시작하세요" 텍스트가 보이는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- `/register` 페이지로 이동

---

## 테스트 케이스 7: 미인증 상태에서 보호 페이지 접근

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 먼저 로그아웃 상태를 확보:
   browser_evaluate로 localStorage.removeItem('auth-storage') 실행
2. browser_navigate로 http://localhost:5173/dashboard 에 접속
3. browser_snapshot으로 결과 확인
4. /login으로 리다이렉트되는지 확인
   (ProtectedRoute: token 없으면 Navigate to="/login" replace)
5. 같은 방식으로 /jobs, /admin 접근도 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 인증되지 않은 상태에서 모든 보호 페이지 → `/login` 리다이렉트

---

## 테스트 케이스 8: 로그인 버튼 로딩 상태 (isPending)

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. 이메일: "test@example.com", 비밀번호: "testpassword123" 입력
3. "로그인" 버튼 클릭 직후 빠르게 browser_snapshot
4. 버튼 텍스트가 "로그인 중..."으로 변경되었는지 확인
5. 버튼이 disabled 상태인지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 요청 중 "로그인 중..." 텍스트 + disabled 상태

---

## 테스트 케이스 9: 401 자동 로그아웃 처리

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 정상 로그인 후 대시보드 진입
2. browser_evaluate로 localStorage의 토큰을 무효화:
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   data.state.token = 'expired_invalid_token';
   localStorage.setItem('auth-storage', JSON.stringify(data));
3. 페이지 새로고침 (browser_navigate로 현재 URL 재접속)
4. browser_snapshot으로 결과 확인
5. axios 인터셉터의 401 처리에 의해:
   - useAuthStore.logout() 호출 → token/user 클리어
   - window.location.href = "/login" 으로 리다이렉트
6. /login 페이지에 도달했는지 확인
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 무효 토큰으로 API 요청 → 401 → 자동 로그아웃 → `/login` 리다이렉트

---

## 테스트 케이스 10: Enter 키로 로그인 폼 제출

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. 이메일: "test@example.com" 입력
3. 비밀번호: "testpassword123" 입력
4. 비밀번호 필드에 포커스가 있는 상태에서 browser_press_key로 "Enter" 키 입력
5. browser_snapshot으로 결과 확인
6. 버튼 클릭 없이도 대시보드(/dashboard)로 이동했는지 확인
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Enter 키로 폼 제출 → 로그인 성공

---

## 테스트 케이스 11: 비밀번호 필드 마스킹 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. 비밀번호 필드에 "testpassword123" 입력
3. browser_snapshot으로 비밀번호 필드의 type 속성 확인
4. type="password"로 마스킹 처리되어 평문이 보이지 않는지 확인
5. browser_evaluate로 확인:
   document.querySelector('input[type="password"]').value
   → 실제 값은 "testpassword123"이지만 UI에는 "••••••••"으로 표시
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 비밀번호가 마스킹 처리됨 (type="password")

---

## 테스트 케이스 12: 로그인 후 /login 재접근 시 리다이렉트

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. test@example.com / testpassword123 으로 로그인
2. 대시보드 진입 확인
3. browser_navigate로 http://localhost:5173/login 에 강제 접속
4. browser_snapshot으로 결과 확인
5. 이미 인증된 상태이므로 /dashboard로 리다이렉트되는지 확인
   (또는 로그인 페이지가 그대로 보이는지 — 앱 구현에 따라 다름)
6. 같은 방식으로 /register 접속 시도
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 인증된 상태에서 /login, /register 접근 시 대시보드 리다이렉트 (구현 여부 확인)

---

## 테스트 케이스 13: XSS 페이로드 로그인 시도

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/login 에 접속
2. 다음을 입력:
   - 이메일: "<img src=x onerror=alert(1)>@test.com"
   - 비밀번호: "<script>document.cookie</script>"
3. "로그인" 버튼 클릭
4. browser_snapshot으로 결과 확인
5. 다음을 확인:
   - JavaScript가 실행되지 않는지
   - 에러 메시지가 이스케이프 처리되어 안전하게 표시되는지
   - browser_console_messages에 보안 관련 에러가 없는지
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- XSS 페이로드가 실행되지 않고 안전하게 처리됨

---

## 테스트 케이스 14: 다중 탭에서 로그아웃 동기화

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. test@example.com으로 로그인
2. 대시보드 확인
3. browser_evaluate로 storage 이벤트 리스너 동작 확인:
   - 현재 탭에서 localStorage의 auth-storage를 클리어:
     localStorage.removeItem('auth-storage')
4. browser_snapshot으로 결과 확인
5. Zustand persist가 storage 이벤트를 감지하여:
   - 자동 로그아웃 처리되는지
   - /login으로 리다이렉트되는지
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- localStorage 클리어 시 앱 상태 동기화 (구현 여부에 따라 결과 다름)

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(03-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
