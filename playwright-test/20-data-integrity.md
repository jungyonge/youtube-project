# 20. 데이터 무결성 및 상태 일관성 테스트

## 목적
프론트엔드-백엔드 간 데이터 일관성, 캐시 무효화, 낙관적 업데이트 정합성,
동시 작업 간 데이터 격리를 테스트합니다.

---

## 테스트 케이스 1: 낙관적 업데이트 — 취소 후 롤백 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

### Step 1: 취소 낙관적 업데이트 확인
1. 진행 중인 작업의 상세 페이지
2. 현재 상태 Badge 기록
3. "취소" 버튼 클릭
4. 즉시 browser_snapshot — "취소됨" Badge 확인 (낙관적 업데이트)

### Step 2: 서버 응답 후 상태 확인
5. 1~2초 대기 후 browser_snapshot
6. 서버 응답이 성공이면 "취소됨" 유지
7. browser_evaluate로 실제 서버 상태 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return { serverPhase: job.phase, isCancelled: job.is_cancelled };
   ```
8. UI 표시와 서버 상태가 일치하는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 낙관적 업데이트 후 서버 상태와 동기화

---

## 테스트 케이스 2: 쿼리 캐시 무효화 — 작업 생성 후 목록 갱신

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

### Step 1: 작업 목록 확인
1. 대시보드의 "내 영상" 목록에서 현재 작업 수 기록

### Step 2: 새 작업 생성
2. 영상 생성 → 작업 상세 페이지로 자동 이동

### Step 3: 대시보드 복귀 후 목록 확인
3. "대시보드" 뒤로가기 클릭
4. browser_snapshot으로 "내 영상" 목록 확인
5. 새로 생성한 작업이 목록 상단에 표시되는지 확인
6. 이전 작업 수 + 1 인지 확인 (queryClient.invalidateQueries 동작 확인)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 작업 생성 후 목록 즉시 갱신 (캐시 무효화)

---

## 테스트 케이스 3: 할당량 실시간 동기화

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

### Step 1: 초기 할당량 확인
1. 로그인 후 Header의 "오늘 N/M" 배지 기록 (N = 현재 사용량)

### Step 2: 작업 생성
2. 영상 생성 실행

### Step 3: 할당량 업데이트 확인
3. 작업 상세 페이지에서 Header 확인
4. "오늘 (N+1)/M"으로 즉시 업데이트되었는지 확인
5. /dashboard로 이동하여도 동일한 값인지 확인
6. /jobs로 이동하여도 동일한 값인지 확인

### Step 4: 새로고침 후 확인
7. 페이지 새로고침
8. API에서 최신 할당량을 가져와 Header에 반영하는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 할당량이 모든 페이지에서 일관되게 표시

---

## 테스트 케이스 4: SSE 이벤트와 UI 상태 동기화

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

(진행 중인 작업의 상세 페이지에서)

### Step 1: SSE 이벤트 수신 확인
1. browser_evaluate로 현재 EventSource 상태 확인:
   ```javascript
   // SSE 연결 상태 확인 (간접적으로)
   const snapshot1 = document.querySelector('[data-testid="progress-percent"]')?.textContent;
   return { progress: snapshot1 };
   ```

### Step 2: 10초 대기 후 변화 확인
2. 10초 대기
3. browser_snapshot으로 변화 확인:
   - 진행률 바 변화
   - 비용 배지 변화
   - 단계 변화

### Step 3: API 직접 호출로 검증
4. browser_evaluate로 서버의 실제 상태 조회:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return {
     phase: job.phase,
     progress: job.progress_percent,
     cost: job.total_cost_usd
   };
   ```
5. UI에 표시된 값과 서버 값이 일치하는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- SSE 이벤트가 UI에 정확히 반영, 서버 상태와 일치

---

## 테스트 케이스 5: 다중 작업 간 데이터 격리

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

### Step 1: 작업 2개 생성
1. 첫 번째 영상 생성: 주제 "첫 번째 작업 데이터 격리 테스트"
2. 작업 ID 기록 (jobId1)
3. 대시보드 복귀
4. 두 번째 영상 생성: 주제 "두 번째 작업 데이터 격리 테스트"
5. 작업 ID 기록 (jobId2)

### Step 2: 각 작업 상세 확인
6. /jobs/{jobId1} 접속 → 상태, 비용, 진행률 기록
7. /jobs/{jobId2} 접속 → 상태, 비용, 진행률 기록
8. 두 작업의 데이터가 섞이지 않는지 확인:
   - 주제가 올바른지
   - 비용이 독립적인지
   - 파이프라인 상태가 독립적인지

### Step 3: 한 작업 취소 후 다른 작업 영향 없음
9. jobId1 취소
10. /jobs/{jobId2} 확인 → 영향 없이 계속 진행 중인지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 작업 간 데이터 완전 격리

---

## 테스트 케이스 6: 재시도 작업의 parent_job_id 정합성

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

### Step 1: 원본 작업 생성 → 취소
1. 영상 생성 → 상세 → 취소
2. jobId 기록 (originalJobId)

### Step 2: 재시도
3. "재시도" 클릭 → 새 작업 상세 이동
4. 새 jobId 기록 (retryJobId)

### Step 3: parent_job_id 확인
5. "원본 작업: {8자}..." 링크 텍스트 확인
6. 링크의 8자가 originalJobId의 앞 8자와 일치하는지 확인
7. 링크 클릭 → /jobs/{originalJobId}로 이동 확인
8. 원본 작업의 상태가 "취소됨"인지 확인

### Step 4: API 검증
9. browser_evaluate로 재시도 작업의 서버 데이터 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{retryJobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return { parentJobId: job.parent_job_id, attemptCount: job.attempt_count };
   ```
10. parent_job_id가 originalJobId와 일치하는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 재시도 작업의 parent_job_id가 원본과 정확히 일치

---

## 테스트 케이스 7: 승인/거부 후 상태 불변성

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

(awaiting_approval 작업 상태에서)

### Step 1: 승인 처리
1. 승인 페이지에서 "승인하고 생성 시작" 클릭
2. 상태 변경 확인: awaiting_approval → generating_assets

### Step 2: 승인된 작업에 대한 재승인 시도
3. browser_evaluate로 이미 승인된 작업에 다시 승인 API 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}/approve', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     }
   });
   return { status: res.status, body: await res.json() };
   ```
4. 400 또는 409 에러 확인 (이미 처리된 작업)

### Step 3: 승인된 작업에 대한 거부 시도
5. 동일하게 reject API 호출
6. 400 또는 409 에러 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 이미 처리된 승인/거부 → 중복 처리 방지

---

## 테스트 케이스 8: Cancel API 실패 시 Optimistic Update 롤백

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

### Step 1: Cancel 실패 시뮬레이션
1. 진행 중인 작업의 상세 페이지
2. browser_evaluate로 fetch를 래핑하여 cancel API 500 에러 반환:
   ```javascript
   const originalFetch = window.fetch;
   window.__originalFetch = originalFetch;
   window.fetch = async (url, opts) => {
     if (typeof url === 'string' && url.includes('/cancel') && opts?.method === 'POST') {
       return new Response(JSON.stringify({detail: 'Internal Server Error'}), {
         status: 500, headers: {'Content-Type': 'application/json'}
       });
     }
     return originalFetch(url, opts);
   };
   ```

### Step 2: 취소 시도 및 롤백 확인
3. 현재 phase 기록 (예: "extracting")
4. "취소" 버튼 클릭
5. 즉시 browser_snapshot — 낙관적 업데이트로 "취소됨" Badge 표시 확인
6. 1~2초 대기
7. browser_snapshot — 500 에러 후 원래 phase로 롤백되었는지 확인
8. 에러 토스트 표시 확인
9. "취소" 버튼이 다시 나타나는지 확인

### Step 3: 정리
10. browser_evaluate로 fetch 복원: `window.fetch = window.__originalFetch;`

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Cancel 실패 → 낙관적 업데이트 롤백 → 원래 phase 복원
- useCancelJob의 onError 콜백이 queryClient rollback 수행

---

## 테스트 케이스 9: Approve 실패 시 Optimistic Update 롤백

### 프롬프트

```
Playwright MCP를 사용하여 다음 데이터 일관성 테스트를 수행해줘:

### Step 1: Approve 실패 시뮬레이션
1. awaiting_approval 상태 작업의 상세 페이지
2. browser_evaluate로 fetch를 래핑하여 approve API 500 에러 반환:
   ```javascript
   const originalFetch = window.fetch;
   window.__originalFetch = originalFetch;
   window.fetch = async (url, opts) => {
     if (typeof url === 'string' && url.includes('/approve') && opts?.method === 'POST') {
       return new Response(JSON.stringify({detail: 'Internal Server Error'}), {
         status: 500, headers: {'Content-Type': 'application/json'}
       });
     }
     return originalFetch(url, opts);
   };
   ```

### Step 2: 승인 시도 및 롤백 확인
3. "승인" 버튼 클릭 (작업 상세 페이지에서)
4. 즉시 browser_snapshot — 낙관적 업데이트로 phase 변경 확인
5. 1~2초 대기
6. browser_snapshot — 원래 상태(awaiting_approval)로 롤백 확인
7. 서버 상태와 UI 상태 일치 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return { serverPhase: job.phase, humanApproved: job.human_approved };
   ```
   ⚠️ 주의: window.__originalFetch를 사용해야 서버에 실제 요청 가능

### Step 3: 정리
8. browser_evaluate로 fetch 복원

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Approve 실패 → phase: `awaiting_approval`로 롤백
- 서버 상태와 UI 상태 일치

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(20-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
