# 21. API 계약(Contract) 검증 테스트

## 목적
프론트엔드와 백엔드 간 데이터 계약(스키마, 열거형, 필드명, 응답 구조)의 불일치를 검증합니다.
이 테스트는 FE/BE 간 런타임 에러를 사전에 발견하기 위한 것입니다.

## 사전 조건
- 로그인 완료 (일반 사용자 + 관리자 계정 모두 필요)
- 최소 1개 작업 존재

---

## 테스트 케이스 1: VideoStyle `storytelling` 전송 시 BE 422 에러

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

⚠️ FE VideoStyle: informative / storytelling / tutorial / opinion
⚠️ BE VideoStyle: informative / entertaining / educational / news

### Step 1: FE 전용 스타일 `storytelling` 직접 API 전송
1. test@example.com 로그인
2. browser_evaluate로 직접 API 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       topic: 'API Contract Test - storytelling',
       sources: [{ url: 'https://example.com/test', source_type: 'blog' }],
       style: 'storytelling'
     })
   });
   return { status: res.status, body: await res.json() };
   ```
3. 결과 확인:
   - 422 → BE가 `storytelling`을 거부함 (계약 불일치 확인)
   - 201 → BE가 허용함 (예상 외, 추가 확인 필요)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 422 Validation Error — `storytelling`은 BE의 `VideoStyle` enum에 없음

---

## 테스트 케이스 2: VideoStyle `tutorial` 전송 시 BE 422 에러

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

1. browser_evaluate로 style: 'tutorial' 전송:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       topic: 'API Contract Test - tutorial style',
       sources: [{ url: 'https://example.com/test', source_type: 'blog' }],
       style: 'tutorial'
     })
   });
   return { status: res.status, body: await res.json() };
   ```
2. 422 응답 확인

결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 422 Validation Error

---

## 테스트 케이스 3: VideoStyle `opinion` 전송 시 BE 422 에러

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

1. browser_evaluate로 style: 'opinion' 전송:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       topic: 'API Contract Test - opinion style',
       sources: [{ url: 'https://example.com/test', source_type: 'blog' }],
       style: 'opinion'
     })
   });
   return { status: res.status, body: await res.json() };
   ```
2. 422 응답 확인

결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 422 Validation Error

---

## 테스트 케이스 4: BE 전용 VideoStyle `entertaining` 직접 API 전송

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

1. browser_evaluate로 BE에만 있는 style 값 전송:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const results = {};
   for (const style of ['entertaining', 'educational', 'news']) {
     const res = await fetch('http://localhost:8000/api/v1/videos', {
       method: 'POST',
       headers: {
         'Authorization': 'Bearer ' + data.state.token,
         'Content-Type': 'application/json'
       },
       body: JSON.stringify({
         topic: `API Contract Test - ${style} style`,
         sources: [{ url: 'https://example.com/test', source_type: 'blog' }],
         style: style
       })
     });
     results[style] = { status: res.status };
   }
   return results;
   ```
2. 결과 확인:
   - 모두 201 → BE 전용 스타일은 유효
   - 일부 422 → 해당 스타일도 BE에서 미지원

결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- `entertaining`, `educational`, `news` 모두 BE에서 유효 (201)
- FE 드롭다운에서는 이 값들을 선택할 수 없음

---

## 테스트 케이스 5: custom_text 소스에 URL 없이 전송 시 BE 422

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

⚠️ FE SourceInput: url은 optional (`url?: string`)
⚠️ BE SourceInput: url은 required (`url: str = Field(..., min_length=1)`)

### Step 1: URL 없이 custom_text 소스 전송
1. browser_evaluate:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       topic: 'API Contract Test - custom_text without URL',
       sources: [{
         source_type: 'custom_text',
         custom_text: '이것은 커스텀 텍스트 소스입니다. URL 없이 전송합니다.'
       }]
     })
   });
   return { status: res.status, body: await res.json() };
   ```
2. 결과 확인:
   - 422 → BE가 url 필수 검증 (`min_length=1`) → FE와 불일치 확인
   - 201 → BE가 허용 (예상 외)

### Step 2: URL + custom_text 함께 전송
3. browser_evaluate:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       topic: 'API Contract Test - custom_text with URL',
       sources: [{
         url: 'https://example.com/custom',
         source_type: 'custom_text',
         custom_text: '커스텀 텍스트와 URL을 함께 전송합니다.'
       }]
     })
   });
   return { status: res.status, body: await res.json() };
   ```
4. 201 응답 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- URL 없이 전송 → 422 (BE url 필수)
- URL + custom_text 전송 → 201 (정상)

---

## 테스트 케이스 6: FE에서 custom_text 소스 추가 시 실제 전송 데이터 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

### Step 1: FE UI에서 custom_text 소스 추가
1. 로그인 → 대시보드
2. 주제: "커스텀 텍스트 소스 테스트"
3. 소스 추가 → "직접 입력" 타입 선택
4. 텍스트 입력: "직접 입력한 텍스트 내용입니다"
5. browser_network_requests 시작

### Step 2: 제출 및 네트워크 요청 확인
6. "영상 생성 시작" 클릭
7. browser_network_requests로 POST /api/v1/videos 요청의 body 확인:
   - sources 배열에서 custom_text 소스의 url 필드가 포함되어 있는지
   - url이 빈 문자열 "", 또는 undefined, 또는 누락인지
8. 서버 응답 확인 (201 vs 422)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- FE가 custom_text 소스에 url을 어떤 값으로 전송하는지 확인
- 422 발생 시 FE에서 url placeholder 추가 필요

---

## 테스트 케이스 7: Retry API 응답에 parent_job_id 필드 부재 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

### Step 1: Retry API 응답 구조 확인
1. 취소 또는 실패한 작업의 ID 확보
2. browser_evaluate로 retry API 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}/retry?from_step=extract', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     }
   });
   const body = await res.json();
   return {
     status: res.status,
     responseKeys: Object.keys(body),
     job_id: body.job_id,
     phase: body.phase,
     attempt_count: body.attempt_count,
     hasParentJobId: 'parent_job_id' in body
   };
   ```
3. 확인 사항:
   - `job_id`가 원본과 동일한지 (BE는 같은 Job 업데이트)
   - `parent_job_id` 필드가 응답에 없는지
   - `attempt_count`가 증가했는지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Retry 응답: `{ job_id: (원본과 동일), phase: "running", attempt_count: N+1 }`
- `parent_job_id` 필드 미포함

---

## 테스트 케이스 8: Retry 후 job_id 동일성 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

### Step 1: 원본 작업 ID 기록 후 Retry
1. failed/cancelled 작업의 job_id 기록: originalJobId
2. retry API 호출
3. 응답의 job_id 확인: retryJobId

### Step 2: ID 비교
4. originalJobId === retryJobId 인지 확인
5. FE에서 navigate(`/jobs/${data.job_id}`) 호출 시:
   - 같은 페이지에 머무는지 (같은 ID)
   - 다른 페이지로 이동하는지 (다른 ID)

### Step 3: GET /api/v1/videos/{retryJobId} 확인
6. 재시도 후 작업 상태 조회:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{retryJobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return {
     job_id: job.job_id,
     phase: job.phase,
     attempt_count: job.attempt_count,
     parent_job_id: job.parent_job_id
   };
   ```

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- originalJobId === retryJobId (BE는 같은 Job 업데이트)
- FE navigate는 같은 페이지에 머무름 (실질적으로 새로고침 효과)

---

## 테스트 케이스 9: Admin Stats 응답 중첩 구조 → FE 플랫 구조 매핑

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

### Step 1: BE 응답 구조 검증
1. admin@example.com 로그인
2. browser_evaluate:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/admin/stats', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const stats = await res.json();

   // FE가 기대하는 필드와 실제 필드 비교
   const feExpected = {
     today_jobs: stats.today_jobs,
     success_rate: stats.success_rate,
     daily_cost_usd: stats.daily_cost_usd,
     active_jobs: stats.active_jobs
   };

   const beActual = {
     'jobs.created': stats.jobs?.created,
     'jobs.completed': stats.jobs?.completed,
     'jobs.active': stats.jobs?.active,
     'cost.total_usd': stats.cost?.total_usd,
     'performance.failure_rate': stats.performance?.failure_rate
   };

   return {
     feFieldsAllUndefined: Object.values(feExpected).every(v => v === undefined),
     beFieldsAvailable: Object.values(beActual).some(v => v !== undefined),
     feExpected,
     beActual,
     fullResponse: stats
   };
   ```
3. FE 기대 필드가 모두 undefined이면 → 매핑 불일치 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- FE 기대 필드(`today_jobs`, `success_rate` 등) → 모두 undefined
- BE 실제 필드(`jobs.created`, `cost.total_usd` 등) → 값 존재
- FE에서 응답 매핑 로직 수정 필요

---

## 테스트 케이스 10: Admin Jobs 응답 user_id 필드 (not user_email)

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

1. admin 로그인
2. browser_evaluate:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/admin/jobs?page=1&per_page=3', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const result = await res.json();

   return {
     firstItemKeys: result.items?.[0] ? Object.keys(result.items[0]) : [],
     hasUserEmail: result.items?.[0] && 'user_email' in result.items[0],
     hasUserId: result.items?.[0] && 'user_id' in result.items[0],
     sampleUserId: result.items?.[0]?.user_id,
     sampleUserEmail: result.items?.[0]?.user_email,
     // FE AdminJobItem 타입 기대: user_email
   };
   ```
3. `user_email` vs `user_id` 확인

결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- BE: `user_id` (UUID 문자열) 반환
- FE: `user_email` 기대 → undefined
- BE에 user email join 추가 또는 FE에서 별도 조회 필요

---

## 테스트 케이스 11: cost_budget_usd 범위 차이 (FE $0.50-$10 vs BE $0.10-$50)

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

### Step 1: FE 범위 밖, BE 범위 안 값 테스트
1. browser_evaluate로 $0.30 전송 (FE 최소 $0.50 미만, BE 최소 $0.10 이상):
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       topic: 'Cost budget range test - $0.30',
       sources: [{ url: 'https://example.com/test', source_type: 'blog' }],
       cost_budget_usd: 0.30
     })
   });
   return { status: res.status, body: await res.json() };
   ```
2. 201 확인 (BE 허용)

### Step 2: $25 전송 (FE 최대 $10 초과, BE 최대 $50 이내)
3. browser_evaluate로 $25 전송:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     },
     body: JSON.stringify({
       topic: 'Cost budget range test - $25',
       sources: [{ url: 'https://example.com/test', source_type: 'blog' }],
       cost_budget_usd: 25.00
     })
   });
   return { status: res.status, body: await res.json() };
   ```
4. 201 확인 (BE 허용)

### Step 3: BE 범위 초과 값 테스트
5. $0.05 전송 → 422 확인 (BE 최소 $0.10 미만)
6. $55.00 전송 → 422 확인 (BE 최대 $50 초과)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- $0.30, $25: BE 201 (FE에서는 입력 불가하지만 API로는 가능)
- $0.05: BE 422, $55: BE 422

---

## 테스트 케이스 12: /admin/stats/daily 엔드포인트 존재 여부

### 프롬프트

```
Playwright MCP를 사용하여 다음 API 계약 검증 테스트를 수행해줘:

⚠️ FE `useAdminDailyStats` 훅이 호출하는 엔드포인트

1. admin 로그인
2. browser_evaluate:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));

   // /admin/stats/daily 엔드포인트 확인
   const res1 = await fetch('http://localhost:8000/admin/stats/daily?days=30', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });

   // /admin/stats/daily/ (trailing slash) 도 확인
   const res2 = await fetch('http://localhost:8000/admin/stats/daily/?days=30', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });

   return {
     withoutSlash: { status: res1.status, statusText: res1.statusText },
     withSlash: { status: res2.status, statusText: res2.statusText },
     body: res1.status === 200 ? await res1.json() : await res1.text()
   };
   ```
3. 결과 확인:
   - 200 → 엔드포인트 존재 (FE 차트 정상 동작)
   - 404/405 → 엔드포인트 미구현 (FE 차트 데이터 없음)

결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- ⚠️ 404 가능성 높음 — BE admin 라우터에 `/stats/daily` 미구현
- FE 비용 차트(`AdminCostChart`)가 데이터를 받지 못해 빈 상태일 수 있음

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(21-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
