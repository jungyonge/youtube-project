# 22. SSE 이벤트 타입별 전수 테스트

## 목적
SSE(Server-Sent Events)로 전송되는 6가지 이벤트 타입 각각이 프론트엔드 UI에 올바르게 반영되는지,
연결 상태 전환(실시간↔폴링↔끊김)이 정상 동작하는지 전수 검증합니다.

## 사전 조건
- 로그인 완료
- 진행 중인 작업 존재 (파이프라인이 활발히 진행 중)

---

## 테스트 케이스 1: `progress` 이벤트 → UI 업데이트

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 이벤트 테스트를 수행해줘:

(진행 중인 작업의 상세 페이지에서)

### Step 1: 초기 상태 기록
1. browser_snapshot으로 현재 상태 기록:
   - 진행률 바 width %
   - phase 텍스트 (Badge)
   - 현재 단계 상세 텍스트
   - 비용 배지 값 ($X.XX / $Y.YY)

### Step 2: progress 이벤트 수신 대기
2. 15~30초 간격으로 browser_snapshot 3회
3. 각 스냅샷에서 다음 변화 확인:
   - progress_percent 증가 → 진행률 바 width 증가
   - phase 변경 시 Badge 텍스트/색상 변경
   - current_step_detail 변경 시 단계 텍스트 업데이트
   - cost_usd 변경 시 비용 배지 값 업데이트

### Step 3: 파이프라인 인디케이터 동기화
4. 9단계 인디케이터에서:
   - 새로 완료된 스텝이 초록색(bg-green-500)으로 변경되었는지
   - 현재 진행 스텝이 파란색 깜빡임(bg-blue-500 animate-pulse)인지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- progress 이벤트 수신 시: 진행률, phase, 단계 텍스트, 비용 모두 실시간 반영

---

## 테스트 케이스 2: `approval_required` 이벤트 → 토스트 + phase 변경

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 이벤트 테스트를 수행해줘:

(자동 승인 OFF 작업이 승인 대기에 도달하는 시점 관찰)

### Step 1: 자동 승인 OFF로 작업 생성
1. 대시보드에서 자동 승인 OFF로 영상 생성
2. 작업 상세 페이지 이동

### Step 2: approval_required 이벤트 대기
3. 파이프라인이 policy_review까지 진행되는 것을 관찰
4. awaiting_approval 도달 시 다음 확인:
   - "대본 승인이 필요합니다" 토스트 표시 (useJobStream의 onApprovalRequired)
   - Badge: "승인 대기" (PHASE_LABELS mapping)
   - 파이프라인 인디케이터 "승인" 스텝: 노란색 깜빡임 (bg-yellow-500 animate-pulse)
   - "승인" + "거부" 버튼 표시

### Step 3: 민감도 수준 확인
5. browser_evaluate로 현재 sensitivity_level 확인:
   ```javascript
   // SSE 이벤트의 sensitivity_level이 UI에 반영되었는지
   // PolicyFlagAlert 또는 승인 페이지에서 확인 가능
   return {
     approvalButtonVisible: !!document.querySelector('button:has(svg)'),
     // 추가 확인은 승인 페이지에서
   };
   ```

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- approval_required 이벤트 → 토스트 + awaiting_approval phase + 승인/거부 버튼

---

## 테스트 케이스 3: `cost_warning` 이벤트 → 경고 토스트

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 이벤트 테스트를 수행해줘:

### Step 1: 낮은 예산으로 작업 생성
1. 고급 설정에서 비용 예산: $0.50 (최소값)으로 영상 생성
2. 작업 상세 페이지 이동

### Step 2: cost_warning 이벤트 모니터링
3. browser_console_messages로 SSE 이벤트 로그 관찰
4. 비용 배지(JobCostBadge) 주기적으로 확인:
   - 비용 비율 < 80%: bg-secondary (기본)
   - 비용 비율 80-99%: bg-yellow-100 text-yellow-700 (경고)
   - 비용 비율 >= 100%: bg-red-100 text-red-700 (초과)

### Step 3: 경고 토스트 확인
5. cost_warning 이벤트 수신 시:
   - toast.warning("비용 경고: $X.XX / $Y.YY") 표시 확인
   - 토스트 내용에 current_cost와 budget이 올바르게 포맷되었는지

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- cost_warning 이벤트 → 경고 토스트 + 비용 배지 색상 변경
- ⚠️ 예산이 충분히 낮아야 이벤트가 발생하므로 $0.50으로 테스트

---

## 테스트 케이스 4: `completed` 이벤트 → 성공 UI

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 이벤트 테스트를 수행해줘:

(파이프라인이 완료 직전인 작업의 상세 페이지에서)

### Step 1: 완료 이벤트 수신 시 UI 변화
1. 작업이 assembling_video 단계에 있을 때 관찰 시작
2. completed 이벤트 수신 시 다음 확인:
   - "영상이 완료되었습니다!" 성공 토스트 표시
   - Badge: "완료" (bg-green-100 text-green-700)
   - 진행률 바: 100%
   - "다운로드" 버튼 활성화 (Download 아이콘)
   - "취소" 버튼 사라짐
   - 파이프라인 인디케이터: 모든 9단계 초록색

### Step 2: 결과 탭 확인
3. "결과" 탭 클릭
4. `<video>` 플레이어가 표시되는지 확인
5. "MP4 파일 다운로드" 링크가 존재하는지 확인

### Step 3: SSE 자동 종료 확인
6. completed 이벤트 후 SSE 연결이 자동으로 닫히는지 확인
   (터미널 상태에서는 SSE 불필요)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- completed → 100% 진행률 + 성공 토스트 + 다운로드 활성화 + SSE 종료

---

## 테스트 케이스 5: `failed` 이벤트 → 에러 UI

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 이벤트 테스트를 수행해줘:

(실패 가능성이 높은 작업 관찰 — 예: 존재하지 않는 URL 소스)

### Step 1: 실패 유도
1. 소스 URL: "https://this-domain-does-not-exist-99999.com/page" 로 작업 생성
2. 작업 상세 페이지에서 관찰

### Step 2: failed 이벤트 수신 시 UI 확인
3. 실패 시 다음 확인:
   - 에러 토스트: "영상 생성에 실패했습니다: {error_message}" 표시
   - Badge: "실패" (bg-red-100 text-red-700)
   - 파이프라인 인디케이터: 실패 스텝 빨간색 (bg-red-500)
   - "재시도" 버튼(RotateCcw) 활성화
   - "취소" 버튼 사라짐

### Step 3: 에러 상세 확인
4. "진행 상세" 탭에서 failed 스텝의 error_message 확인
5. "결과" 탭에서 AlertTriangle + "생성 실패" 메시지 확인

### Step 4: SSE 자동 종료 확인
6. failed 이벤트 후 SSE 연결이 자동으로 닫히는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- failed → 에러 토스트 + 실패 Badge + 재시도 버튼 + SSE 종료

---

## 테스트 케이스 6: `cancelled` 이벤트 → 취소 UI

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 이벤트 테스트를 수행해줘:

### Step 1: 작업 생성 후 취소
1. 작업 생성 → 상세 페이지
2. SSE 연결 확인 (연결 상태 배지)
3. "취소" 버튼 클릭

### Step 2: cancelled 이벤트 수신 시 UI 확인
4. 다음 확인:
   - Badge: "취소됨" (bg-gray-100)
   - "취소" 버튼 사라짐
   - "재시도" 버튼 표시
   - 파이프라인 인디케이터: 완료된 스텝 초록, 나머지 회색

### Step 3: SSE 자동 종료 확인
5. cancelled 이벤트 후 SSE 연결이 닫히는지 확인
6. 추가 이벤트가 수신되지 않는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- cancelled → 취소 Badge + 재시도 버튼 + SSE 종료

---

## 테스트 케이스 7: SSE 연결 끊김 → 폴링 폴백 전환

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 연결 상태 테스트를 수행해줘:

### Step 1: SSE 연결 상태 확인
1. 진행 중인 작업의 상세 페이지
2. SSE 연결 상태 배지 확인: "실시간" (Wifi 아이콘, text-green-600)

### Step 2: SSE 연결 강제 끊기
3. browser_evaluate로 EventSource 연결 강제 종료:
   ```javascript
   // SSE 연결이 끊기면 useJobStream이 감지하여 폴링으로 전환
   // 간접적으로 확인: 네트워크 차단은 Playwright에서 직접 할 수 없으므로
   // SSE 재연결 시도 + 폴링 전환 로직을 관찰
   ```

### Step 3: 폴링 모드 확인
4. SSE 끊김 후 연결 상태 배지 변화 관찰:
   - 재연결 시도 (최대 5회, 3초 간격)
   - 5회 실패 후: "폴링" (RefreshCw 아이콘, text-yellow-600) 전환
   - 또는 "끊김" (WifiOff 아이콘, text-red-600) 표시
5. 폴링 모드에서도 데이터가 5초 간격으로 업데이트되는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- SSE 끊김 → 재연결 시도(5회) → 폴링 폴백(5초 간격) 전환

---

## 테스트 케이스 8: SSE 재연결 성공 → 폴링 중지 + 상태 동기화

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 재연결 테스트를 수행해줘:

### Step 1: SSE 연결 상태 관찰
1. 진행 중인 작업의 상세 페이지
2. SSE 연결 상태 배지 확인

### Step 2: SSE 재연결 메커니즘 확인
3. browser_evaluate로 SSE 재연결 로직 확인:
   ```javascript
   // sse.ts의 onopen 핸들러는 재연결 시:
   // 1. retryCount를 0으로 리셋
   // 2. GET /api/v1/videos/{jobId}로 최신 상태 동기화
   // 3. onConnectionChange(true) 호출
   ```
4. SSE가 재연결되면:
   - 연결 상태 배지: "실시간"으로 복귀
   - 폴링 중지 (clearInterval)
   - GET API 호출로 현재 상태와 UI 동기화

### Step 3: 상태 동기화 검증
5. browser_evaluate로 API 상태와 UI 상태 비교:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return {
     serverPhase: job.phase,
     serverProgress: job.progress_percent,
     serverCost: job.total_cost_usd
   };
   ```
6. UI 표시 값과 서버 값이 일치하는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- SSE 재연결 → 폴링 중지 + "실시간" 배지 + 최신 상태 동기화

---

## 테스트 케이스 9: Heartbeat(15초) 수신 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE heartbeat 테스트를 수행해줘:

### Step 1: SSE 스트림 직접 관찰
1. 진행 중인 작업의 상세 페이지
2. browser_evaluate로 SSE 엔드포인트에 직접 연결하여 heartbeat 관찰:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const token = data.state.token;

   return new Promise((resolve) => {
     const events = [];
     const es = new EventSource(
       `http://localhost:8000/api/v1/videos/{jobId}/stream?token=${token}`
     );

     es.onmessage = (e) => {
       events.push({ type: 'message', data: e.data, time: Date.now() });
     };

     es.addEventListener('heartbeat', (e) => {
       events.push({ type: 'heartbeat', data: e.data, time: Date.now() });
     });

     // 20초 관찰 후 결과 반환
     setTimeout(() => {
       es.close();
       resolve({
         totalEvents: events.length,
         heartbeats: events.filter(e => e.type === 'heartbeat').length,
         events: events.slice(0, 10) // 최대 10개
       });
     }, 20000);
   });
   ```
3. 15초 이내에 heartbeat 이벤트가 1회 이상 수신되는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 15초 간격으로 heartbeat 이벤트 수신 → SSE 연결 유지 확인

---

## 테스트 케이스 10: 터미널 상태 도달 시 SSE 자동 종료

### 프롬프트

```
Playwright MCP를 사용하여 다음 SSE 종료 테스트를 수행해줘:

### Step 1: 터미널 상태에서 SSE 연결 확인
1. completed 또는 failed 또는 cancelled 작업의 상세 페이지 접속
2. browser_snapshot으로 SSE 연결 상태 배지 확인

### Step 2: SSE 미연결 확인
3. 터미널 상태에서는 SSE가 연결되지 않아야 함:
   - useJobStream 훅의 조건: isTerminal이면 SSE 미시작
   - 연결 상태 배지: "끊김" 또는 미표시
4. browser_evaluate로 확인:
   ```javascript
   // EventSource 인스턴스가 없거나 CLOSED 상태인지
   // 간접 확인: 네트워크 요청에서 /stream 호출 없음
   ```

### Step 3: 진행 중 → 터미널 전환 시 SSE 종료
5. 진행 중인 작업을 "취소" → cancelled 이벤트 수신
6. 이후 SSE 연결이 자동으로 닫히는지 확인
7. 추가 heartbeat가 수신되지 않는지 확인 (20초 대기)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 터미널 상태 → SSE 미연결 또는 자동 종료
- 불필요한 연결 유지 방지

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(22-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
