# 01. 헬스체크 테스트 (단위)

## 목적
서비스가 정상적으로 기동되었는지 API 헬스체크와 프론트엔드 로딩을 확인합니다.

---

## 테스트 케이스 1: API 헬스체크 응답 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:8000/health 에 접속
2. browser_snapshot으로 페이지 내용을 캡처
3. 응답 JSON에서 다음을 확인:
   - "status" 값이 "healthy"인지
   - "components.database.status"가 "healthy"인지
   - "components.redis.status"가 "healthy"인지
   - "components.minio.status"가 "healthy"인지
   - "components.api_keys.status"가 "healthy" 또는 "warning"인지
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
```json
{
  "status": "healthy",
  "components": {
    "database": { "status": "healthy" },
    "redis": { "status": "healthy" },
    "minio": { "status": "healthy" },
    "api_keys": { "status": "healthy" 또는 "warning" }
  }
}
```

---

## 테스트 케이스 2: 프론트엔드 초기 로딩 및 리다이렉트

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173 에 접속
2. browser_snapshot으로 페이지 상태를 캡처
3. 다음을 확인:
   - 미인증 상태이므로 /login 으로 리다이렉트되는지 확인
     (ProtectedRoute가 token 없으면 /login으로 Navigate)
   - "로그인" 제목 텍스트가 보이는지
   - "AI Video Studio에 로그인하세요" 설명이 보이는지
   - 이메일, 비밀번호 입력 필드가 있는지
4. browser_console_messages로 JavaScript 에러가 없는지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 미인증 → `/login` 리다이렉트
- 페이지가 에러 없이 정상 렌더링

---

## 테스트 케이스 3: Fallback 라우트 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. browser_navigate로 http://localhost:5173/some-nonexistent-page 에 접속
2. browser_snapshot으로 결과 확인
3. 다음을 확인:
   - App.tsx의 fallback 라우트 ("*" → Navigate to="/dashboard" replace)에 의해
     /dashboard로 리다이렉트 시도하는지
   - 미인증이라면 다시 /login으로 리다이렉트되는지
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- `*` → `/dashboard` → (미인증) → `/login` 순서로 리다이렉트

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(01-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
