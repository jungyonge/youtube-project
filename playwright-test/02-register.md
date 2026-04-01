# 02. 회원가입 테스트 (단위)

## 목적
회원가입 폼의 입력 검증, 성공/실패 시나리오를 개별적으로 테스트합니다.

### 핵심 동작 (use-auth.ts 기준)
- 성공 시: `setAuth(token, user)` → `toast.success("회원가입 완료")` → `navigate("/dashboard")`
- 실패 시: `toast.error("회원가입에 실패했습니다. 이미 존재하는 이메일일 수 있습니다.")`
- **주의**: 회원가입 성공 시 로그인 페이지가 아니라 **바로 대시보드로 이동**합니다.

---

## 테스트 케이스 1: 회원가입 페이지 렌더링 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. browser_snapshot으로 페이지 상태를 캡처
3. 다음 요소가 존재하는지 확인:
   - "회원가입" 제목 텍스트 (CardTitle)
   - "새 계정을 만들어 시작하세요" 설명 (CardDescription)
   - "이메일" 라벨 + 입력 필드 (placeholder: "you@example.com")
   - "비밀번호" 라벨 + 입력 필드 (type: password)
   - "비밀번호 확인" 라벨 + 입력 필드 (type: password)
   - "회원가입" 제출 버튼
   - "이미 계정이 있으신가요? 로그인" 링크 (/login으로 이동)
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 모든 폼 요소가 화면에 정상 렌더링

---

## 테스트 케이스 2: 빈 폼 제출 시 유효성 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. browser_snapshot으로 현재 상태 확인
3. 아무것도 입력하지 않고 "회원가입" 버튼을 browser_click으로 클릭
4. browser_snapshot으로 결과 확인
5. 유효성 검증 에러 메시지가 표시되는지 확인:
   - 이메일 필드: "올바른 이메일을 입력하세요"
   - 비밀번호 필드: "비밀번호는 8자 이상이어야 합니다"
6. 에러 메시지가 각 필드 아래에 FormMessage로 표시되는지 확인
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- zod 스키마 검증에 의한 에러 메시지 표시
- API 호출은 발생하지 않음

---

## 테스트 케이스 3: 비밀번호 불일치 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. browser_snapshot으로 현재 상태 확인
3. 다음을 입력:
   - 이메일: "mismatch@example.com"
   - 비밀번호: "password123"
   - 비밀번호 확인: "differentpassword"
4. "회원가입" 버튼을 browser_click으로 클릭
5. browser_snapshot으로 결과 확인
6. "비밀번호가 일치하지 않습니다" 에러 메시지가 비밀번호 확인 필드 아래에 표시되는지 확인
   (zod .refine()에 의한 path: ["confirmPassword"] 에러)
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- "비밀번호가 일치하지 않습니다" 에러 메시지 표시

---

## 테스트 케이스 4: 짧은 비밀번호 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 다음을 입력:
   - 이메일: "short@example.com"
   - 비밀번호: "1234567" (7자 — 최소 8자 미달)
   - 비밀번호 확인: "1234567"
3. "회원가입" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. "비밀번호는 8자 이상이어야 합니다" 에러 메시지가 표시되는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 8자 미만 비밀번호에 대한 에러 메시지 표시

---

## 테스트 케이스 5: 정상 회원가입

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. browser_snapshot으로 현재 상태 확인
3. 다음을 입력:
   - 이메일: "test@example.com"
   - 비밀번호: "testpassword123"
   - 비밀번호 확인: "testpassword123"
4. "회원가입" 버튼을 browser_click으로 클릭
5. 잠시 대기 후 browser_snapshot으로 결과 확인
6. 다음을 확인:
   - **대시보드(/dashboard)로 바로 이동**했는지 (useRegister는 성공 시 navigate("/dashboard"))
   - "회원가입 완료" 토스트 메시지가 표시되는지 (sonner Toaster, 우측 상단)
   - Sidebar가 보이는지 (RootLayout)
   - Header에 사용자 이메일이 표시되는지
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 회원가입 성공 → JWT 발급 → **대시보드로 직접 이동** (로그인 페이지 아님!)
- 토스트: "회원가입 완료"

---

## 테스트 케이스 6: 중복 이메일 회원가입 시도

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 이미 가입된 이메일로 다시 회원가입 시도:
   - 이메일: "test@example.com"
   - 비밀번호: "testpassword123"
   - 비밀번호 확인: "testpassword123"
3. "회원가입" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. 다음을 확인:
   - "회원가입에 실패했습니다. 이미 존재하는 이메일일 수 있습니다." 토스트 에러가 표시되는지
     (useRegister의 onError 토스트)
   - 페이지가 여전히 회원가입 페이지에 머물러 있는지
   - 버튼이 다시 "회원가입"으로 돌아왔는지 (isPending 해제)
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 409 Conflict → 토스트 에러 메시지 표시
- 회원가입 페이지 유지

---

## 테스트 케이스 7: 로그인 페이지 링크 이동

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. browser_snapshot으로 확인
3. "로그인" 링크 (Link to="/login") 를 browser_click으로 클릭
4. browser_snapshot으로 결과 확인
5. 로그인 페이지(/login)로 정상 이동했는지 확인
6. "로그인" 제목과 "AI Video Studio에 로그인하세요" 텍스트가 보이는지 확인
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- `/login` 페이지로 이동, 로그인 폼이 표시

---

## 테스트 케이스 8: 잘못된 이메일 형식 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 다음을 입력:
   - 이메일: "invalid-email" (@ 없는 형식)
   - 비밀번호: "password123"
   - 비밀번호 확인: "password123"
3. "회원가입" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. "올바른 이메일을 입력하세요" 에러가 이메일 필드에 표시되는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- zod의 `.email()` 검증에 의한 에러 메시지

---

## 테스트 케이스 9: 비밀번호 최대 길이(128자) 경계값

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 다음을 입력:
   - 이메일: "maxpw@example.com"
   - 비밀번호: "a" 128회 반복 (정확히 128자)
   - 비밀번호 확인: 동일하게 "a" 128회 반복
3. "회원가입" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. 유효성 에러 없이 정상 제출되는지 확인 (128자 = 최대 허용)
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 128자 비밀번호 → 에러 없이 제출

---

## 테스트 케이스 10: 비밀번호 129자 초과 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 다음을 입력:
   - 이메일: "overlength@example.com"
   - 비밀번호: "a" 129회 반복 (129자 — 최대 128자 초과)
   - 비밀번호 확인: 동일하게 "a" 129회 반복
3. "회원가입" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. 비밀번호 최대 길이 초과 에러 메시지가 표시되는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 129자 → 최대 길이 초과 에러

---

## 테스트 케이스 11: XSS 스크립트 입력 시도

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 다음을 입력:
   - 이메일: "<script>alert('xss')</script>@example.com"
   - 비밀번호: "password123"
   - 비밀번호 확인: "password123"
3. "회원가입" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. 다음을 확인:
   - JavaScript alert가 실행되지 않는지 (browser_console_messages에 에러 없는지)
   - "올바른 이메일을 입력하세요" 에러가 표시되는지 (이메일 형식 불량)
   - DOM에 스크립트 태그가 삽입되지 않았는지
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- XSS 페이로드 → 이메일 형식 에러, 스크립트 실행 안 됨

---

## 테스트 케이스 12: SQL 인젝션 패턴 입력 시도

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 다음을 입력:
   - 이메일: "test'OR'1'='1@example.com"
   - 비밀번호: "'; DROP TABLE users; --"
   - 비밀번호 확인: "'; DROP TABLE users; --"
3. "회원가입" 버튼을 클릭
4. browser_snapshot으로 결과 확인
5. 다음을 확인:
   - 이메일 형식 에러 또는 서버 에러가 정상 처리되는지
   - 서비스가 계속 정상 동작하는지 (다른 페이지 접속 가능)
   - browser_console_messages에서 500 에러가 없는지
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- SQL 인젝션 → 정상 에러 처리, 서비스 무중단

---

## 테스트 케이스 13: 회원가입 버튼 로딩 상태 (isPending)

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 다음을 입력:
   - 이메일: "loading-test@example.com"
   - 비밀번호: "password123"
   - 비밀번호 확인: "password123"
3. "회원가입" 버튼 클릭 직후 빠르게 browser_snapshot
4. 버튼 텍스트가 "가입 중..." 또는 유사한 로딩 텍스트로 변경되었는지 확인
5. 버튼이 disabled 상태인지 확인 (중복 제출 방지)
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 요청 중 로딩 텍스트 + disabled 상태로 중복 제출 방지

---

## 테스트 케이스 14: Enter 키로 폼 제출

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/register 에 접속
2. 다음을 입력:
   - 이메일: "enterkey@example.com"
   - 비밀번호: "password123"
   - 비밀번호 확인: "password123"
3. 비밀번호 확인 필드에 포커스가 있는 상태에서 browser_press_key로 "Enter" 키 입력
4. browser_snapshot으로 결과 확인
5. 버튼 클릭 없이도 폼이 제출되어 대시보드로 이동하는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Enter 키로 폼 제출 가능 (HTML form 기본 동작)

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(02-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
