# 16. 보안 테스트

## 목적
XSS, CSRF, 인젝션, IDOR, JWT 조작, 권한 우회 등 OWASP Top 10 기반 보안 취약점을 E2E로 테스트합니다.

---

## 테스트 케이스 1: Stored XSS — 주제 필드

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

### Step 1: XSS 페이로드가 포함된 작업 생성
1. 로그인 후 대시보드
2. 주제에 다음 XSS 페이로드 입력:
   <img src=x onerror="document.title='XSS'">테스트 영상 제목입니다
3. 소스 URL: "https://example.com/xss-test"
4. "영상 생성 시작" 클릭
5. 작업 생성 성공 여부 확인

### Step 2: 저장된 XSS 실행 여부 확인
6. 작업 상세 페이지에서 browser_snapshot
7. 다음을 확인:
   - document.title이 "XSS"로 변경되지 않았는지
   - browser_evaluate: document.title !== 'XSS'
   - 주제가 이스케이프 처리되어 텍스트로 표시되는지
   - <img> 태그가 DOM에 실제 요소로 삽입되지 않았는지

### Step 3: 작업 목록에서도 확인
8. /jobs 페이지에서 해당 작업 카드 확인
9. 카드 내 주제 텍스트가 이스케이프 처리되었는지
10. browser_console_messages에서 에러 없는지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- React의 기본 이스케이프 처리로 XSS 방지
- DOM에 스크립트/이벤트 핸들러 삽입 안 됨

---

## 테스트 케이스 2: Stored XSS — 소스 URL 필드

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

1. 로그인 후 대시보드
2. 주제: "소스 URL XSS 테스트 영상입니다"
3. 소스 URL에 다음 입력:
   javascript:alert(document.cookie)
4. "영상 생성 시작" 클릭
5. browser_snapshot으로 결과 확인:
   - URL 유효성 검증에 의해 거부되는지
   - 또는 서버에서 400 에러가 반환되는지
6. 다른 페이로드 시도:
   소스 URL: "https://example.com/<script>alert(1)</script>"
7. 결과 확인
8. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- javascript: 프로토콜 → 거부
- URL 내 스크립트 태그 → 이스케이프 처리

---

## 테스트 케이스 3: IDOR — 타 사용자 작업 접근

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

### Step 1: 사용자 A의 작업 생성
1. test@example.com 로그인
2. 영상 생성 → 작업 ID(jobIdA) 기록
3. 로그아웃

### Step 2: 사용자 B로 접근 시도 (다른 일반 사용자)
4. 다른 계정으로 로그인 (없으면 새로 가입)
5. browser_evaluate로 사용자 A의 작업에 직접 API 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const results = {};

   // 작업 상세 조회
   let res = await fetch('http://localhost:8000/api/v1/videos/{jobIdA}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   results.getDetail = res.status;

   // 작업 취소 시도
   res = await fetch('http://localhost:8000/api/v1/videos/{jobIdA}/cancel', {
     method: 'POST',
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   results.cancel = res.status;

   // 작업 승인 시도
   res = await fetch('http://localhost:8000/api/v1/videos/{jobIdA}/approve', {
     method: 'POST',
     headers: { 'Authorization': 'Bearer ' + data.state.token, 'Content-Type': 'application/json' }
   });
   results.approve = res.status;

   // SSE 스트림 접근 시도
   res = await fetch('http://localhost:8000/api/v1/videos/{jobIdA}/stream?token=' + data.state.token);
   results.stream = res.status;

   return results;
   ```
6. 모든 요청이 403 Forbidden인지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| API | 기대 상태 |
|-----|-----------|
| GET /videos/{jobIdA} | 403 |
| POST /cancel | 403 |
| POST /approve | 403 |
| GET /stream | 403 |

---

## 테스트 케이스 4: JWT 토큰 변조 탐지

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

### Step 1: 정상 JWT 확인
1. test@example.com 로그인
2. browser_evaluate로 JWT 구조 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const parts = data.state.token.split('.');
   const header = JSON.parse(atob(parts[0]));
   const payload = JSON.parse(atob(parts[1]));
   return { header, payload, signatureLength: parts[2].length };
   ```

### Step 2: Payload 변조 시도
3. browser_evaluate로 role을 admin으로 변조:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const parts = data.state.token.split('.');
   const payload = JSON.parse(atob(parts[1]));
   payload.role = 'admin';
   const newPayload = btoa(JSON.stringify(payload)).replace(/=/g, '');
   const tamperedToken = parts[0] + '.' + newPayload + '.' + parts[2];

   // 변조된 토큰으로 admin API 호출
   const res = await fetch('http://localhost:8000/admin/stats', {
     headers: { 'Authorization': 'Bearer ' + tamperedToken }
   });
   return { status: res.status };
   ```
4. 401 또는 403 확인 (서명 불일치로 거부)

### Step 3: Algorithm None 공격 시도
5. browser_evaluate로 알고리즘 none 공격:
   ```javascript
   const header = btoa(JSON.stringify({alg: "none", typ: "JWT"})).replace(/=/g, '');
   const payload = btoa(JSON.stringify({sub: "admin-id", role: "admin"})).replace(/=/g, '');
   const noneToken = header + '.' + payload + '.';

   const res = await fetch('http://localhost:8000/admin/stats', {
     headers: { 'Authorization': 'Bearer ' + noneToken }
   });
   return { status: res.status };
   ```
6. 401 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- JWT payload 변조 → 서명 불일치 → 401
- Algorithm none 공격 → 401

---

## 테스트 케이스 5: 미인증 API 직접 호출

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

1. 로그아웃 상태에서 browser_evaluate로 보호된 API 직접 호출:
   ```javascript
   const endpoints = [
     { method: 'GET', url: '/api/v1/videos' },
     { method: 'POST', url: '/api/v1/videos' },
     { method: 'GET', url: '/api/v1/videos/some-id' },
     { method: 'GET', url: '/auth/me' },
     { method: 'GET', url: '/admin/stats' },
     { method: 'GET', url: '/admin/jobs' },
   ];

   const results = [];
   for (const ep of endpoints) {
     const res = await fetch('http://localhost:8000' + ep.url, {
       method: ep.method,
       headers: { 'Content-Type': 'application/json' }
     });
     results.push({ endpoint: ep.method + ' ' + ep.url, status: res.status });
   }
   return results;
   ```
2. 모든 보호된 엔드포인트가 401 Unauthorized인지 확인
3. 공개 엔드포인트(POST /auth/register, POST /auth/login, GET /health)는 접근 가능한지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 보호된 엔드포인트: 모두 401
- 공개 엔드포인트: 200 또는 적절한 응답

---

## 테스트 케이스 6: HTTP 보안 헤더 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

1. browser_evaluate로 API 응답의 보안 헤더 확인:
   ```javascript
   const res = await fetch('http://localhost:8000/health');
   return {
     'X-Content-Type-Options': res.headers.get('X-Content-Type-Options'),
     'X-Frame-Options': res.headers.get('X-Frame-Options'),
     'X-XSS-Protection': res.headers.get('X-XSS-Protection'),
     'Strict-Transport-Security': res.headers.get('Strict-Transport-Security'),
     'Content-Security-Policy': res.headers.get('Content-Security-Policy'),
     'X-Trace-ID': res.headers.get('X-Trace-ID'),
     'Access-Control-Allow-Origin': res.headers.get('Access-Control-Allow-Origin'),
   };
   ```
2. 다음 보안 헤더가 설정되어 있는지 확인:
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY 또는 SAMEORIGIN
   - X-Trace-ID: UUID 형태
3. 누락된 보안 헤더 기록

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 기본 보안 헤더 존재 여부 확인 (누락 시 보안 개선 필요)

---

## 테스트 케이스 7: 비밀번호 brute-force 방지

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

1. browser_evaluate로 잘못된 비밀번호로 반복 로그인 시도:
   ```javascript
   const results = [];
   for (let i = 0; i < 15; i++) {
     const res = await fetch('http://localhost:8000/auth/login', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         email: 'test@example.com',
         password: 'wrong_password_' + i
       })
     });
     results.push({ attempt: i + 1, status: res.status });
   }
   return results;
   ```
2. 다음을 확인:
   - 일정 횟수 이후 429(Rate Limit)가 반환되는지
   - 또는 계정 잠금이 발생하는지
   - 또는 제한 없이 모든 시도가 401인지 (취약점)
3. Rate Limit 미들웨어(60회/60초)에 의해 제한되는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Rate Limit에 의해 일정 횟수 이후 429 반환
- 별도 계정 잠금 메커니즘 존재 여부 확인

---

## 테스트 케이스 8: SSE 엔드포인트 인증 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

1. 미인증 상태에서 SSE 스트림 접근 시도:
   ```javascript
   // 토큰 없이 SSE 접근
   const res = await fetch('http://localhost:8000/api/v1/videos/some-job-id/stream');
   return { status: res.status };
   ```
2. 401 확인

3. 잘못된 토큰으로 SSE 접근:
   ```javascript
   const res = await fetch('http://localhost:8000/api/v1/videos/some-job-id/stream?token=invalid_token');
   return { status: res.status };
   ```
4. 401 확인

5. 정상 토큰으로 타인 작업 SSE 접근:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{otherUserJobId}/stream?token=' + data.state.token);
   return { status: res.status };
   ```
6. 403 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- SSE 엔드포인트도 동일한 인증/인가 적용

---

## 테스트 케이스 9: CORS 설정 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

1. browser_evaluate로 다른 Origin에서의 API 호출 시뮬레이션:
   ```javascript
   // Preflight OPTIONS 요청 확인
   const res = await fetch('http://localhost:8000/api/v1/videos', {
     method: 'OPTIONS',
     headers: {
       'Origin': 'https://malicious-site.com',
       'Access-Control-Request-Method': 'GET',
       'Access-Control-Request-Headers': 'Authorization'
     }
   });
   return {
     status: res.status,
     allowOrigin: res.headers.get('Access-Control-Allow-Origin'),
     allowMethods: res.headers.get('Access-Control-Allow-Methods'),
     allowHeaders: res.headers.get('Access-Control-Allow-Headers'),
   };
   ```
2. 다음을 확인:
   - Access-Control-Allow-Origin이 와일드카드(*)가 아닌지
   - 허용된 Origin 목록에 localhost만 포함되는지
   - malicious-site.com이 거부되는지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- CORS가 허용된 Origin만 허용
- 임의 도메인에서의 요청 차단

---

## 테스트 케이스 10: 민감 정보 노출 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 보안 테스트를 수행해줘:

### Step 1: API 에러 응답에서 민감 정보 미노출
1. 로그인 후 존재하지 않는 엔드포인트 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/nonexistent', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const body = await res.text();
   return { status: res.status, body: body };
   ```
2. 에러 응답에 스택 트레이스, 파일 경로, DB 쿼리 등이 포함되지 않는지 확인

### Step 2: 사용자 목록 API 미존재
3. 다음 엔드포인트들이 존재하지 않는지 확인:
   - GET /api/v1/users (사용자 목록 노출)
   - GET /api/v1/users/{userId} (타인 정보 조회)

### Step 3: 비밀번호 해시 미노출
4. GET /auth/me 응답에 password 또는 password_hash 필드가 없는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 에러 응답에 민감 정보 미포함
- 사용자 정보 API 미존재 또는 보호됨
- 비밀번호 해시 미노출

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(16-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
