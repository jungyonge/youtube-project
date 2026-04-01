# 08. 승인/거부 (Approval) 테스트 (단위)

## 목적
승인 페이지의 대본 미리보기, 정책 경고, 승인/거부/수정 요청 기능을 테스트합니다.

### 핵심: 라우트 경로는 `/jobs/:jobId/approval` (approve가 아님!)

## 사전 조건
- 로그인 완료
- 자동 승인 OFF 작업이 `awaiting_approval` 상태에 도달

---

## 테스트 케이스 1: 승인 페이지 렌더링 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 로그인 후 awaiting_approval 상태 작업의 jobId를 확보
2. browser_navigate로 http://localhost:5173/jobs/{jobId}/approval 에 접속
   (주의: /approve가 아니라 /approval 입니다)
3. browser_snapshot으로 승인 페이지 상태 캡처
4. 다음 요소가 존재하는지 확인:
   - "상세로 돌아가기" 뒤로가기 버튼 (ArrowLeft + Link to="/jobs/{jobId}")
   - ScriptPreview 영역:
     - PolicyFlagAlert (민감도가 있는 경우)
     - 대본 제목(h2, text-xl font-bold) + 부제
     - 태그 배지들
     - 총 시간 배지 + "N개 씬" 배지
     - 씬 카드들 (ScriptSceneCard)
   - Separator
   - 하단 고정(sticky) 액션 영역:
     - "거부" 버튼 (XCircle, destructive)
     - "수정 요청" 버튼 (RefreshCw, outline)
     - "승인하고 생성 시작" 버튼 (CheckCircle)
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 대본 내용이 구조화되어 표시
- 3개 액션 버튼이 하단에 고정

---

## 테스트 케이스 2: ScriptPreview — 씬 카드 상세 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(승인 페이지에서)

1. browser_snapshot으로 씬 카드(ScriptSceneCard) 영역 캡처
2. 각 씬 카드에서 다음을 확인:
   - 헤더: "씬 N: {section}" + 에셋 타입 Badge + 목표 시간
   - 목적(purpose) 텍스트 (text-xs)
   - 나레이션(narration) 영역 (bg-muted p-3)
   - 근거 배지(ClaimBadge):
     - "사실: {text} (N%)" — bg-green-100
     - "추론: {text} (N%)" — bg-yellow-100
     - "의견: {text} (N%)" — bg-orange-100
     - hover 시 Tooltip으로 근거 인용문 표시
   - 정책 플래그: destructive Badge
   - 키워드: secondary Badge
3. 스크롤하여 전체 씬 목록을 확인
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 씬별로 나레이션, 근거, 정책, 키워드가 구조화되어 표시

---

## 테스트 케이스 3: PolicyFlagAlert — 민감 주제 경고

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(정책 경고가 있는 대본의 승인 페이지에서)

1. browser_snapshot으로 PolicyFlagAlert 영역 캡처
2. 다음을 확인:
   - Alert variant="destructive" 스타일
   - "민감 주제 - 승인 필요" 제목
   - 민감도 Badge:
     - low: "낮음" (bg-green-100)
     - medium: "보통" (bg-yellow-100)
     - high: "높음" (bg-red-100)
   - 경고 항목들이 outline Badge로 나열
3. 경고가 없는 대본에서는 이 컴포넌트가 렌더링되지 않는지 확인
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 경고 있을 때만 표시, 민감도 수준별 색상 구분

---

## 테스트 케이스 4: 승인 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(awaiting_approval 상태 작업의 승인 페이지에서)

1. browser_snapshot으로 현재 상태 확인
2. "승인하고 생성 시작" 버튼을 클릭
3. browser_snapshot으로 결과 확인
4. 다음을 확인:
   - "대본이 승인되었습니다." 토스트 (useApproveJob의 onSuccess)
   - 낙관적 업데이트: phase → "generating_assets", human_approved → true
   - 쿼리 무효화 후 상태 갱신
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 승인 → 파이프라인이 TTS 단계부터 재개

---

## 테스트 케이스 5: 거부 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(awaiting_approval 상태 작업의 승인 페이지에서)

1. "거부" 버튼을 클릭
2. browser_snapshot으로 거부 다이얼로그 확인:
   - "대본 거부" 제목
   - "거부 사유를 입력하세요 (선택)" 설명
   - 거부 사유 Textarea (rows=3)
   - "취소" 버튼 + "거부 확인" 버튼
3. 거부 사유에 "3번 씬의 내용이 부정확합니다" 입력
4. "거부 확인" 버튼 클릭
5. browser_snapshot으로 결과 확인:
   - "대본이 거부되었습니다." 토스트 (useRejectJob의 onSuccess)
   - 상태가 "rejected"로 변경
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 거부 다이얼로그 → 사유 입력(선택) → 거부 처리

---

## 테스트 케이스 6: 거부 다이얼로그 취소

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(승인 페이지에서)

1. "거부" 버튼 클릭
2. 거부 다이얼로그가 열린 것을 확인
3. "취소" 버튼을 클릭
4. browser_snapshot으로 다이얼로그가 닫혔는지 확인
5. 승인 페이지 상태가 그대로 유지되는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 다이얼로그 닫힘, 이전 상태 유지

---

## 테스트 케이스 7: 수정 요청 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(승인 페이지에서)

1. "수정 요청" 버튼(RefreshCw) 클릭
2. browser_snapshot으로 수정 요청 다이얼로그 확인:
   - "수정 요청" 제목
   - "수정할 내용을 지시하세요. 대본 재생성부터 새로 시작됩니다." 설명
   - "추가 지시사항" Label + Textarea (rows=4)
   - "취소" 버튼 + "수정 요청 확인" 버튼
3. **지시사항이 비어있을 때** "수정 요청 확인" 버튼이 **disabled** 인지 확인
   (disabled={retryJob.isPending || !modifyInstructions.trim()})
4. 지시사항에 "3번 씬의 투자 예측 표현을 완화해주세요" 입력
5. "수정 요청 확인" 버튼이 **활성화**되었는지 확인
6. 버튼 클릭
7. browser_snapshot으로 결과 확인:
   - useRetryJob 호출 (from_step: "review")
   - "재시도 작업이 생성되었습니다." 토스트
   - 새 작업 상세 페이지로 이동
8. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 빈 지시사항 → 버튼 disabled
- 입력 후 → review 단계부터 재시도

---

## 테스트 케이스 8: 비승인대기 상태에서 접근 시 리다이렉트

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. awaiting_approval이 **아닌** 상태의 작업 ID 확보 (예: completed, running)
2. browser_navigate로 http://localhost:5173/jobs/{jobId}/approval 에 접속
3. browser_snapshot으로 결과 확인
4. ApprovalPage의 로직 확인:
   - job.phase !== "awaiting_approval" → Navigate to={`/jobs/${job.job_id}`} replace
   - 작업 상세 페이지(/jobs/{jobId})로 리다이렉트되는지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- awaiting_approval이 아닌 작업 → 상세 페이지로 리다이렉트

---

## 테스트 케이스 9: 승인 버튼 더블클릭 방지

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(awaiting_approval 상태 작업의 승인 페이지에서)

1. "승인하고 생성 시작" 버튼을 빠르게 2회 연속 클릭
2. browser_snapshot으로 결과 확인
3. 다음을 확인:
   - 첫 번째 클릭 후 버튼이 disabled 상태가 되는지 (isPending)
   - 중복 승인 API 호출이 발생하지 않는지 (browser_network_requests로 확인)
   - 토스트가 1개만 표시되는지
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- isPending으로 더블클릭 방지, API 1회만 호출

---

## 테스트 케이스 10: 빈 거부 사유로 거부 제출

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(awaiting_approval 상태 작업의 승인 페이지에서)

1. "거부" 버튼 클릭 → 거부 다이얼로그 열림
2. 거부 사유를 **비워둔 채** "거부 확인" 클릭
3. browser_snapshot으로 결과 확인
4. 다음을 확인:
   - 거부 사유가 선택(optional)이므로 비어있어도 제출 가능한지
   - "대본이 거부되었습니다." 토스트가 정상 표시되는지
   - 상태가 "rejected"로 변경되는지
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 거부 사유 없이도 거부 가능 (선택 필드)

---

## 테스트 케이스 11: 긴 대본 스크롤 및 씬 카드 전체 표시

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(승인 페이지에서 — 씬이 여러 개인 대본)

1. browser_snapshot으로 초기 화면 캡처
2. 스크롤하여 마지막 씬 카드까지 이동
3. browser_snapshot으로 마지막 씬 카드 확인
4. 하단 고정(sticky) 액션 버튼 영역이 스크롤과 무관하게 항상 보이는지 확인:
   - "거부", "수정 요청", "승인하고 생성 시작" 버튼이 하단에 고정
5. 스크롤 위치와 관계없이 버튼 클릭이 가능한지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 스크롤 시에도 하단 액션 버튼 항상 접근 가능

---

## 테스트 케이스 12: 작업 상세에서 승인 페이지로 직접 이동

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(awaiting_approval 상태의 작업 상세 페이지에서)

1. browser_snapshot으로 작업 상세 확인
2. "승인" 버튼(CheckCircle)을 확인
3. 이 버튼이 승인 페이지(/jobs/{jobId}/approval)로 이동하는 링크인지,
   또는 직접 승인 API를 호출하는지 확인
4. 승인 페이지로 이동하는 경우:
   - 페이지 이동 확인
   - 대본 미리보기가 표시되는지 확인
5. 직접 API 호출하는 경우:
   - 대본 검토 없이 바로 승인 처리되는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 작업 상세 ↔ 승인 페이지 간 네비게이션 확인

---

## 테스트 케이스 13: 승인 API 실패 시 Optimistic Update 롤백

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(awaiting_approval 상태의 작업 승인 페이지에서)

⚠️ 이 테스트는 FE의 낙관적 업데이트 롤백 메커니즘을 검증합니다.

### Step 1: 서버 에러 시뮬레이션 설정
1. browser_evaluate로 fetch를 임시 래핑하여 approve API만 500 에러 반환:
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

### Step 2: 승인 시도
2. browser_snapshot으로 현재 상태 기록 — phase: "awaiting_approval"
3. "승인하고 생성 시작" 버튼 클릭
4. 즉시 browser_snapshot — 낙관적 업데이트로 phase가 변경되었을 수 있음

### Step 3: 롤백 확인
5. 1~2초 대기 후 browser_snapshot
6. 500 에러 발생 후 UI가 원래 상태(awaiting_approval)로 롤백되었는지 확인
7. 에러 토스트가 표시되었는지 확인
8. "승인" / "거부" 버튼이 다시 활성화되었는지 확인

### Step 4: 정리
9. browser_evaluate로 fetch 복원: `window.fetch = window.__originalFetch;`

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 승인 API 실패 → 낙관적 업데이트 롤백 → `awaiting_approval` 상태 복원
- 에러 토스트 표시 + 버튼 재활성화

---

## 테스트 케이스 14: 거부 API 실패 시 Optimistic Update 롤백

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(awaiting_approval 상태의 작업 승인 페이지에서)

### Step 1: 서버 에러 시뮬레이션
1. browser_evaluate로 fetch를 래핑하여 reject API만 500 에러 반환:
   ```javascript
   const originalFetch = window.fetch;
   window.__originalFetch = originalFetch;
   window.fetch = async (url, opts) => {
     if (typeof url === 'string' && url.includes('/reject') && opts?.method === 'POST') {
       return new Response(JSON.stringify({detail: 'Internal Server Error'}), {
         status: 500, headers: {'Content-Type': 'application/json'}
       });
     }
     return originalFetch(url, opts);
   };
   ```

### Step 2: 거부 시도
2. "거부" 버튼 클릭 → 다이얼로그에서 사유 입력 → "거부 확인" 클릭
3. 1~2초 대기

### Step 3: 롤백 확인
4. browser_snapshot으로 확인:
   - phase가 "awaiting_approval"로 롤백되었는지
   - 에러 토스트 표시 여부
   - "승인" / "거부" 버튼 재활성화 여부

### Step 4: 정리
5. browser_evaluate로 fetch 복원

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 거부 API 실패 → 롤백 → `awaiting_approval` 상태 복원

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(08-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
