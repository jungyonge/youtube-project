# 15. 통합 테스트: 에러 처리 및 엣지 케이스

## 목적
네트워크 에러, 비정상 접근, 경계값, 중복 제출, 에러 바운더리 등의 엣지 케이스를 E2E로 테스트합니다.

---

## 통합 시나리오 1: 존재하지 않는 작업 접근

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 로그인
1. test@example.com으로 로그인

### Step 2: 잘못된 작업 ID로 상세 접근
2. browser_navigate로 http://localhost:5173/jobs/00000000-0000-0000-0000-000000000000 에 접속
3. browser_snapshot으로 결과 확인:
   - 로딩 스피너 표시 후
   - API 404 응답 시 에러 처리 확인
   - 빈 상태 또는 에러 메시지 표시

### Step 3: 잘못된 작업 ID로 승인 페이지 접근
4. browser_navigate로 http://localhost:5173/jobs/00000000-0000-0000-0000-000000000000/approval
5. browser_snapshot으로 결과 확인:
   - "데이터를 불러올 수 없습니다." 메시지 표시

### Step 4: 정상 페이지 복귀
6. Sidebar "대시보드" 클릭으로 정상 복귀 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 잘못된 ID → 에러 처리 |
| 3 | 승인 페이지도 에러 처리 |
| 4 | 정상 페이지 복귀 |

---

## 통합 시나리오 2: 중복 제출 방지 (isPending + 멱등성 키)

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 로그인 후 대시보드

### Step 2: 빠른 연속 제출 테스트
1. 주제: "동시성 테스트 영상 제목입니다" 입력
2. 소스 URL: "https://example.com/concurrency-test" 입력
3. "영상 생성 시작" 버튼 클릭
4. 버튼이 즉시 "생성 중..."(isPending) + disabled로 변경되는지 확인
5. disabled 상태에서 추가 클릭이 불가능한지 확인

### Step 3: 결과 확인
6. 작업 상세 페이지로 이동 확인
7. 하나의 작업만 생성되었는지 확인

### Step 4: 멱등성 키 확인 (409 처리)
8. browser_navigate로 대시보드 복귀
9. 만약 같은 멱등성 키로 재요청이 발생하면:
   - 409 응답 → "이미 동일한 요청이 있습니다." 토스트
   - 기존 작업 상세 페이지로 이동

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | isPending으로 중복 클릭 방지 |
| 3 | 작업 1개만 생성 |
| 4 | 409 → 기존 작업으로 안내 |

---

## 통합 시나리오 3: 주제 경계값 테스트

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 최소 길이 미달 (4자)
1. 주제에 "테스트" (3자) 입력
2. "영상 생성 시작" 클릭
3. "주제는 5자 이상이어야 합니다" 에러 확인

### Step 2: 정확히 5자 (최소)
4. 주제 "테스트입니다" (5자) 입력
5. 소스 URL 입력
6. "영상 생성 시작" 클릭
7. 에러 없이 제출되는지 확인

### Step 3: 정확히 200자 (최대)
8. 주제에 200자 텍스트 입력: "가" 반복 200회
9. 에러 없이 제출되는지 확인

### Step 4: 201자 초과
10. 주제에 201자 텍스트 입력
11. "주제는 200자 이하여야 합니다" 에러 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 1 | 4자 → 에러 |
| 2 | 5자 → 통과 |
| 3 | 200자 → 통과 |
| 4 | 201자 → 에러 |

---

## 통합 시나리오 4: 브라우저 새로고침 시 상태 유지

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 작업 상세 페이지 상태 기록
1. 로그인 후 작업 상세 페이지로 이동
2. browser_snapshot으로 현재 상태 기록:
   - 작업 phase, progress_percent, cost
   - 현재 URL

### Step 2: 새로고침
3. browser_navigate로 현재 URL 재접속
4. browser_snapshot으로 상태 확인:
   - 로그인 유지 (JWT persist)
   - 작업 데이터 재로딩
   - SSE 재연결 또는 폴링 시작

### Step 3: 대시보드 새로고침
5. browser_navigate로 /dashboard 접속
6. 작업 목록 정상 로딩 확인
7. Header 할당량 표시 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 인증 + 데이터 유지 |
| 3 | 대시보드 정상 렌더링 |

---

## 통합 시나리오 5: 429 요청 제한 처리

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

참고: 미들웨어에서 Redis 기반 요청 제한 (60회/60초) 적용

### Step 1: 일반 사용 확인
1. 로그인 후 정상 동작 확인

### Step 2: 429 토스트 확인
2. axios 인터셉터에서 429 시:
   toast.error("요청 제한을 초과했습니다. 잠시 후 다시 시도해주세요.")
3. 이 토스트가 올바르게 표시되는지 확인하기 위해
   browser_evaluate로 API를 빠르게 반복 호출하여 429 유발 시도:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const token = data.state.token;
   const results = [];
   for (let i = 0; i < 65; i++) {
     const res = await fetch('http://localhost:8000/api/v1/videos?page=1', {
       headers: { 'Authorization': 'Bearer ' + token }
     });
     results.push(res.status);
   }
   return results.filter(s => s === 429).length;
   ```
4. 429 응답이 있는지 확인

### Step 3: 토스트 확인
5. browser_snapshot으로 429 토스트가 표시되는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 60회 초과 시 429 |
| 3 | 토스트 에러 표시 |

---

## 통합 시나리오 6: 에러 바운더리 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 에러 바운더리 UI 확인
1. 로그인 후 browser_evaluate로 의도적 에러 유발:
   (예: window.__test_error = true 같은 방식은 앱에 없으므로,
    ErrorBoundary의 정적 UI를 확인)
2. ErrorBoundary가 존재하는지 App.tsx 구조로 확인:
   - ErrorBoundary가 Routes를 감싸고 있음
   - 에러 발생 시: AlertTriangle 아이콘 + "오류가 발생했습니다" + 에러 메시지 + "새로고침" 버튼

### Step 2: 새로고침 버튼 확인
3. ErrorBoundary가 렌더링될 경우 "새로고침" 버튼이 window.location.reload()를 호출하는지

참고: 이 테스트는 에러 바운더리 컴포넌트의 존재와 구조를 확인하는 것입니다.
실제 에러 유발은 어렵기 때문에, 정상 상태에서 에러 바운더리가 트리거되지 않는 것을 확인합니다.

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 정상 상태에서는 에러 바운더리 미트리거
- 에러 시 사용자 친화적 fallback UI

---

## 통합 시나리오 7: SSE 연결 끊김 → 폴링 폴백

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 작업 생성 후 상세 페이지
1. 영상 생성 → 상세 페이지 이동
2. SSE 연결 상태 배지 확인: "실시간"(초록) 또는 이미 "폴링"(노란)

### Step 2: SSE 연결 상태 모니터링
3. 10초 후 browser_snapshot으로 상태 확인
4. SSE 연결이 유지되면: "실시간" 배지
5. SSE가 끊기면: 자동으로 "폴링" 모드로 전환되는지 확인
   - sse.ts의 MAX_RETRIES(5) + RETRY_DELAY_MS(3000) 후
   - useJobStream의 startPolling() 호출
   - 5초 간격 API 폴링

### Step 3: 폴링 모드에서도 데이터 업데이트
6. 폴링 모드에서 진행률이 여전히 업데이트되는지 확인
7. 작업이 terminal 상태에 도달하면 폴링도 중지되는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | SSE 연결 또는 폴링 확인 |
| 3 | 폴링 모드에서도 데이터 갱신 |

---

## 통합 시나리오 8: 비용 경고 토스트

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 낮은 예산으로 영상 생성
1. 주제: "비용 경고 테스트"
2. 소스 URL: "https://example.com/cost-test"
3. 고급 설정에서 비용 예산: $0.50 (최소값)
4. "영상 생성 시작"

### Step 2: 비용 경고 모니터링
5. 작업 상세에서 비용 배지 확인
6. SSE cost_warning 이벤트 시:
   - toast.warning("비용 경고: $X.XX / $Y.YY") 표시
7. 비용 배지 색상 변화:
   - 80% 도달: 노란색 (bg-yellow-100)
   - 100% 도달: 빨간색 (bg-red-100)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 비용 경고 토스트 + 배지 색상 변화 |

---

## 통합 시나리오 9: JWT 만료 시점 정밀 테스트

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 로그인 후 토큰 만료 시뮬레이션
1. test@example.com 으로 로그인
2. browser_evaluate로 현재 JWT 토큰 확인
3. JWT 디코딩하여 exp(만료 시간) 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const token = data.state.token;
   const payload = JSON.parse(atob(token.split('.')[1]));
   return { exp: payload.exp, now: Math.floor(Date.now()/1000), remaining: payload.exp - Math.floor(Date.now()/1000) };
   ```
4. 남은 시간 확인 (기본 30분)

### Step 2: 만료된 토큰으로 API 호출
5. browser_evaluate로 만료된 JWT 생성 시뮬레이션:
   - 현재 토큰의 payload를 변조하면 signature 불일치로 401 발생
   - 이 경우 401 → 자동 로그아웃 확인
6. browser_snapshot으로 /login 리다이렉트 확인

### Step 3: 정상 재로그인
7. 재로그인 → 새 토큰 발급 → 정상 동작 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 1 | JWT exp 시간 확인 (30분) |
| 2 | 만료/변조 토큰 → 401 → 자동 로그아웃 |
| 3 | 재로그인 정상 |

---

## 통합 시나리오 10: 동시 탭 작업 충돌 테스트

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 작업 생성
1. 로그인 → 영상 생성 (자동 승인 OFF)
2. 승인 대기 상태까지 대기

### Step 2: 동일 작업을 두 탭에서 접근 시뮬레이션
3. 첫 번째 "탭"에서 승인 페이지(/jobs/{jobId}/approval) 접속
4. browser_evaluate로 승인 API를 직접 호출하여 "두 번째 탭에서의 승인" 시뮬레이션:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}/approve', {
     method: 'POST',
     headers: {
       'Authorization': 'Bearer ' + data.state.token,
       'Content-Type': 'application/json'
     }
   });
   return { status: res.status };
   ```
5. 200 OK 확인 (첫 번째 승인 성공)

### Step 3: 첫 번째 탭에서 중복 승인 시도
6. 화면의 "승인하고 생성 시작" 버튼 클릭
7. browser_snapshot으로 결과 확인:
   - 이미 승인된 작업에 대해 에러 처리가 되는지
   - "이미 처리된 작업입니다" 또는 유사 에러
   - 또는 상태가 이미 변경되어 버튼이 비활성화 되었는지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | API 직접 호출로 승인 성공 |
| 3 | 중복 승인 시도 → 적절한 에러 처리 |

---

## 통합 시나리오 11: 네트워크 지연 시 UI 피드백

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 로그인 상태에서 느린 네트워크 시뮬레이션
1. 로그인 후 대시보드 확인
2. browser_evaluate로 네트워크 지연 시뮬레이션:
   ```javascript
   // fetch를 래핑하여 2초 지연 추가
   const originalFetch = window.fetch;
   window.fetch = async (...args) => {
     await new Promise(r => setTimeout(r, 2000));
     return originalFetch(...args);
   };
   ```

### Step 2: 지연된 상태에서 작업 생성 시도
3. 주제: "네트워크 지연 테스트 영상입니다" 입력
4. 소스 URL: "https://example.com/slow-test"
5. "영상 생성 시작" 클릭
6. browser_snapshot으로 확인:
   - 로딩 상태("생성 중...")가 2초 이상 유지되는지
   - 사용자가 기다리는 동안 버튼이 disabled 상태인지
   - 타임아웃 에러가 발생하지 않는지

### Step 3: 원래 fetch 복원
7. browser_evaluate로 window.fetch = originalFetch 복원

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 2 | 지연 중 로딩 UI 유지 |
| 3 | fetch 복원 후 정상 동작 |

---

## 통합 시나리오 12: Trace ID 전파 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: API 응답 헤더의 Trace ID 확인
1. 로그인 후 대시보드
2. browser_evaluate로 API 호출 시 응답 헤더 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos?page=1', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   return {
     status: res.status,
     traceId: res.headers.get('X-Trace-ID')
   };
   ```
3. X-Trace-ID 헤더가 존재하는지 확인
4. UUID 형태인지 확인

### Step 2: 여러 요청의 Trace ID 고유성
5. 동일 API를 3회 호출
6. 각 응답의 X-Trace-ID가 모두 다른지 확인 (요청별 고유)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
| Step | 기대 결과 |
|------|-----------|
| 1 | X-Trace-ID 헤더 존재 |
| 2 | 요청마다 고유한 Trace ID |

---

## 통합 시나리오 13: Cancel on rejected/failed 상태 — FE/BE 불일치

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

⚠️ **알려진 이슈**: BE의 cancel 엔드포인트는 `completed`, `cancelled`만 차단하므로
`rejected`, `failed` 상태에서도 cancel이 가능함.
반면 FE는 `TERMINAL_STATES`(completed, failed, cancelled, rejected)에 포함되면 취소 버튼을 미표시.

### Step 1: rejected 상태 Job에서 Cancel API 직접 호출
1. rejected 상태의 작업 ID 확보
2. browser_snapshot으로 "취소" 버튼이 표시되지 않음을 확인 (FE: terminal)
3. browser_evaluate로 Cancel API 직접 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}/cancel', {
     method: 'POST',
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   return { status: res.status, body: await res.json() };
   ```
4. 응답 확인:
   - 200 → BE는 허용 (FE와 불일치)
   - 400 → BE도 차단 (일관됨)

### Step 2: failed 상태 Job에서 Cancel API 직접 호출
5. failed 상태의 작업 ID로 동일한 테스트 수행
6. 응답 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- ⚠️ BE는 rejected/failed에서도 cancel 허용 → FE와 불일치
- BE에 `rejected`, `failed`도 cancel 차단 목록에 추가 필요

---

## 통합 시나리오 14: Presigned URL 만료 시 에러 처리

### 프롬프트

```
Playwright MCP를 사용하여 다음 통합 테스트를 수행해줘:

### Step 1: 만료된 Presigned URL 시뮬레이션
1. completed 작업의 상세 페이지 접속
2. "결과" 탭 클릭
3. browser_evaluate로 현재 video src의 presigned URL 확인:
   ```javascript
   const video = document.querySelector('video');
   return { src: video?.src };
   ```
4. URL의 X-Amz-Date 또는 Expires 파라미터로 만료 시간 확인

### Step 2: 만료 URL 직접 접근 테스트
5. browser_evaluate로 만료 시뮬레이션 (URL의 Expires를 과거로 변경하여 요청):
   ```javascript
   const video = document.querySelector('video');
   const url = video?.src;
   if (url) {
     // 원본 URL로 직접 fetch하여 응답 확인
     const res = await fetch(url);
     return { status: res.status, ok: res.ok };
   }
   ```
6. 현재 URL이 유효한지 확인

### Step 3: 페이지 재진입 시 URL 갱신 확인
7. 다른 페이지 이동 후 다시 작업 상세로 돌아옴
8. "결과" 탭의 video src가 새로운 presigned URL인지 확인
   (API 재호출로 새 URL 발급)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- Presigned URL이 API 호출 시 매번 새로 발급
- 만료된 URL 접근 시 적절한 에러 처리

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(15-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
