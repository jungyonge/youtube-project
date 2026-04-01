# 18. 성능 및 스트레스 테스트

## 목적
대량 데이터, 동시 요청, 메모리 누수, 렌더링 성능 등을 E2E로 테스트합니다.

---

## 테스트 케이스 1: 대량 작업 목록 렌더링 성능

### 프롬프트

```
Playwright MCP를 사용하여 다음 성능 테스트를 수행해줘:

### Step 1: 대량 작업 생성 (데이터 준비)
1. 로그인 후 browser_evaluate로 작업 목록 API 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos?page=1', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const body = await res.json();
   return { total: body.total, pageSize: body.size };
   ```
2. 현재 작업 수 확인

### Step 2: 목록 페이지 로딩 시간 측정
3. browser_evaluate로 페이지 로딩 시간 측정:
   ```javascript
   const start = performance.now();
   ```
4. browser_navigate로 /jobs 접속
5. browser_evaluate로 로딩 완료까지 시간 측정:
   ```javascript
   return performance.now() - window.__startTime;
   ```
6. 3초 이내에 렌더링이 완료되는지 확인

### Step 3: 스크롤 성능
7. 페이지네이션 "다음" 클릭 시 로딩 시간 확인
8. 각 페이지 전환이 2초 이내인지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 페이지 로딩 3초 이내, 페이지 전환 2초 이내

---

## 테스트 케이스 2: SSE 장시간 연결 안정성

### 프롬프트

```
Playwright MCP를 사용하여 다음 성능 테스트를 수행해줘:

### Step 1: SSE 연결 유지 테스트
1. 영상 생성 후 작업 상세 페이지 이동
2. SSE 연결 상태 배지 확인: "실시간"
3. 30초 동안 browser_snapshot을 5초 간격으로 6회 수행
4. 각 스냅샷에서:
   - SSE 연결이 유지되는지 ("실시간" 또는 "폴링")
   - 메모리 사용량 증가 확인:
     ```javascript
     return performance.memory ? {
       usedJSHeapSize: performance.memory.usedJSHeapSize,
       totalJSHeapSize: performance.memory.totalJSHeapSize
     } : 'Not available';
     ```
5. 메모리가 비정상적으로 증가하지 않는지 확인

### Step 2: 완료 후 SSE 정리
6. 작업이 terminal 상태에 도달하면:
   - SSE 연결이 정상적으로 종료되는지
   - 폴링이 중지되는지
   - 메모리가 해제되는지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- SSE 장시간 연결 안정, 메모리 누수 없음

---

## 테스트 케이스 3: 빠른 연속 페이지 이동 안정성

### 프롬프트

```
Playwright MCP를 사용하여 다음 성능 테스트를 수행해줘:

1. 로그인 후 빠르게 페이지 이동:
   - /dashboard → /jobs → /dashboard → /jobs/{jobId} → /dashboard
2. 각 이동 사이에 0.5초만 대기
3. browser_snapshot으로 최종 페이지 확인:
   - 정상 렌더링되었는지
   - 에러가 발생하지 않았는지
4. browser_console_messages에서 에러 확인:
   - "Can't perform a React state update on an unmounted component" 같은 에러 없는지
   - 취소된 fetch 에러가 gracefully 처리되었는지
5. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 빠른 네비게이션 시 에러 없이 정상 동작

---

## 테스트 케이스 4: 동시 API 요청 처리

### 프롬프트

```
Playwright MCP를 사용하여 다음 성능 테스트를 수행해줘:

1. 로그인 후 browser_evaluate로 동시 API 요청:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const token = data.state.token;

   const start = performance.now();
   const promises = [];
   for (let i = 0; i < 10; i++) {
     promises.push(
       fetch('http://localhost:8000/api/v1/videos?page=1', {
         headers: { 'Authorization': 'Bearer ' + token }
       }).then(r => ({ status: r.status, ok: r.ok }))
     );
   }
   const results = await Promise.all(promises);
   const elapsed = performance.now() - start;

   return {
     elapsed: Math.round(elapsed),
     results: results,
     allOk: results.every(r => r.ok),
     any429: results.some(r => r.status === 429)
   };
   ```
2. 10개 동시 요청이 모두 처리되는지 확인
3. 429(Rate Limit)가 발생하는지 확인
4. 전체 응답 시간이 합리적인지 확인 (10초 이내)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 동시 요청 처리, Rate Limit 적절히 동작

---

## 테스트 케이스 5: 대본 탭 긴 콘텐츠 렌더링

### 프롬프트

```
Playwright MCP를 사용하여 다음 성능 테스트를 수행해줘:

(대본이 생성된 작업의 상세 페이지에서)

1. "대본" 탭 클릭
2. browser_snapshot으로 대본 내용 확인
3. 씬 수가 많은 경우(10개 이상):
   - 모든 씬이 렌더링 되는지 확인
   - 스크롤이 정상 동작하는지
   - 렌더링 중 UI가 멈추지 않는지
4. 각 씬의 claims(근거) 배지가 많은 경우:
   - Tooltip hover가 정상 동작하는지
   - 렌더링이 지연되지 않는지
5. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 긴 대본도 정상 렌더링, 스크롤 부드러움

---

## 테스트 케이스 6: 관리자 페이지 대량 데이터 처리

### 프롬프트

```
Playwright MCP를 사용하여 다음 성능 테스트를 수행해줘:

1. admin@example.com 로그인 → /admin 이동
2. browser_evaluate로 전체 작업 수 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/admin/jobs?page=1', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const body = await res.json();
   return { total: body.total };
   ```
3. 작업 테이블 로딩 시간 확인
4. 이메일 검색 시 응답 시간 확인:
   - 입력 후 테이블 갱신까지 소요 시간
   - 디바운스가 적용되어 있는지 (입력할 때마다 API 호출하지 않는지)
5. 상태 필터 전환 시 응답 시간 확인
6. 결과를 정리해줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 테이블 로딩 3초 이내, 필터링 2초 이내

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(18-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
