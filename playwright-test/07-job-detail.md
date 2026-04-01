# 07. 작업 상세 (Job Detail) 테스트 (단위)

## 목적
작업 상세 페이지의 렌더링, 파이프라인 스텝 인디케이터, 진행률, SSE 연결 상태,
상세 탭(진행 상세/대본/결과), 액션 버튼을 테스트합니다.

## 사전 조건
- 로그인 완료, 최소 1개 작업 존재

---

## 테스트 케이스 1: 작업 상세 페이지 전체 구조

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 로그인 후 대시보드의 "내 영상" 목록에서 작업 카드 클릭
2. browser_snapshot으로 작업 상세 페이지 캡처
3. 다음 요소가 모두 존재하는지 확인:
   - "대시보드" 뒤로가기 버튼 (ArrowLeft + Link to="/dashboard")
   - 상태 Badge (PHASE_LABELS[phase], PHASE_COLORS[phase])
   - 생성일 (formatDate)
   - JobActions 영역 (상태에 따른 버튼들)
   - JobProgress 컴포넌트:
     - 9단계 파이프라인 스텝 인디케이터 (추출→정규화→근거→대본→검수→정책→승인→에셋→조립)
     - 진행률 바 (0~100%)
     - 현재 단계 상세 텍스트
     - 비용 배지 (JobCostBadge: "$X.XX / $Y.YY")
     - SSE 연결 상태 배지 (실시간/폴링/끊김)
   - Separator
   - JobDetailPanel (탭 3개: 진행 상세, 대본, 결과)
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 작업 상세 페이지 전체 구성 요소 확인

---

## 테스트 케이스 2: 파이프라인 9단계 스텝 인디케이터

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(작업 상세 페이지에서)

1. browser_snapshot으로 파이프라인 스텝 인디케이터 캡처
2. 9개 스텝이 순서대로 표시되는지 확인:
   - 추출, 정규화, 근거, 대본, 검수, 정책, 승인, 에셋, 조립
3. 각 스텝의 상태 색상 확인:
   - 완료(completed): 초록색 (bg-green-500)
   - 진행 중(active): 파란색 + 깜빡임 (bg-blue-500 animate-pulse)
   - 대기(pending): 회색 (bg-muted-foreground/30)
   - 실패(failed): 빨간색 (bg-red-500)
   - 승인 대기(approval): 노란색 + 깜빡임 (bg-yellow-500 animate-pulse)
4. 현재 phase에 맞게 스텝 상태가 올바른지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 현재 단계 이전: 초록, 현재: 파란(깜빡임), 이후: 회색

---

## 테스트 케이스 3: 비용 배지 색상 변화 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(작업 상세 페이지에서)

1. browser_snapshot으로 비용 배지(JobCostBadge) 캡처
2. 현재 비용과 예산 확인 — "$X.XX / $Y.YY" 형태
3. 비용 배지의 색상 규칙 확인:
   - ratio < 0.8 → bg-secondary (기본 색상)
   - 0.8 ≤ ratio < 1.0 → bg-yellow-100 text-yellow-700 (경고)
   - ratio ≥ 1.0 → bg-red-100 text-red-700 (초과)
4. 현재 비용 비율에 맞는 색상이 적용되었는지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 비용 80% 이상: 노란색 경고, 100% 이상: 빨간색

---

## 테스트 케이스 4: SSE 연결 상태 배지 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(진행 중인 작업의 상세 페이지에서)

1. browser_snapshot으로 SSE 연결 상태 배지 캡처
2. 다음 3가지 상태 중 하나가 표시되는지 확인:
   - 연결됨(isConnected: true): Wifi 아이콘 + "실시간" (text-green-600)
   - 폴링 폴백(isFallbackPolling: true): RefreshCw 아이콘 + "폴링" (text-yellow-600)
   - 연결 끊김: WifiOff 아이콘 + "끊김" (text-red-600)
3. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- SSE 연결 상태가 시각적으로 표시

---

## 테스트 케이스 5: JobDetailPanel — 진행 상세 탭

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(작업 상세 페이지에서)

1. 하단의 탭 패널 확인 — "진행 상세" 탭이 기본 선택(defaultValue="progress")인지
2. browser_snapshot으로 진행 상세 테이블(JobProgressSteps) 확인
3. 테이블 헤더 확인:
   - (상태 아이콘), 단계, 상태, 소요 시간(우측 정렬), 비용(우측 정렬), 오류
4. 각 행(step)의 상태 아이콘 확인:
   - pending: Circle (회색)
   - running: Loader2 (파란색, 회전)
   - completed: CheckCircle (초록색)
   - failed: XCircle (빨간색)
   - skipped: SkipForward (회색)
5. 실행 기록이 없는 경우 "실행 기록이 없습니다." 메시지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 각 파이프라인 단계의 상태, 소요 시간, 비용, 에러 정보 표시

---

## 테스트 케이스 6: JobDetailPanel — 대본 탭

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(대본이 생성된 작업의 상세 페이지에서 — awaiting_approval 이후 단계)

1. "대본" 탭을 클릭
2. browser_snapshot으로 대본 내용 확인
3. 다음을 확인:
   - 제목(script.title)과 부제(script.subtitle)
   - 태그들 (Badge variant="outline")
   - 정책 경고가 있으면 Alert(variant="destructive") 표시
   - 씬 카드들:
     - "씬 N: {section}" 제목
     - 나레이션(narration) 텍스트
     - 근거 배지(claims): 사실(초록), 추론(노란), 의견(주황)
     - 정책 플래그가 있으면 destructive Badge
4. 대본이 아직 없으면 "대본이 아직 생성되지 않았습니다." 메시지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 대본 정보가 구조화되어 표시

---

## 테스트 케이스 7: JobDetailPanel — 결과 탭

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(작업 상세 페이지에서)

1. "결과" 탭을 클릭
2. browser_snapshot으로 결과 내용 확인
3. 상태별 표시 확인:
   - completed: 비디오 플레이어(<video>) + "MP4 파일 다운로드" 링크
   - failed: 실패 Alert(AlertTriangle + "생성 실패" + error 메시지)
   - 그 외: "영상이 아직 생성되지 않았습니다." 메시지
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 완료: 비디오 플레이어, 실패: 에러 Alert, 그 외: 안내 메시지

---

## 테스트 케이스 8: 뒤로가기 버튼 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(작업 상세 페이지에서)

1. "대시보드" 뒤로가기 버튼(ArrowLeft + Link to="/dashboard")을 클릭
2. browser_snapshot으로 대시보드(/dashboard)로 이동했는지 확인
3. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- `/dashboard`로 이동

---

## 테스트 케이스 9: 취소 버튼 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(진행 중인 작업의 상세 페이지에서)

1. browser_snapshot으로 현재 상태 확인
2. "취소" 버튼(Ban 아이콘)이 보이는지 확인 (canCancel: phase가 terminal이 아닐 때)
3. "취소" 버튼을 클릭
4. browser_snapshot으로 결과 확인:
   - 낙관적 업데이트(optimistic update)로 즉시 "취소됨" Badge 표시되는지
   - "작업이 취소되었습니다." 토스트가 표시되는지
   - "취소" 버튼이 사라지고 "재시도" 버튼이 나타나는지
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 낙관적 업데이트 → 취소 상태 즉시 반영 → 서버 확인

---

## 테스트 케이스 10: 재시도 버튼 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(취소/실패된 작업의 상세 페이지에서)

1. "재시도" 버튼(RotateCcw 아이콘)이 보이는지 확인
   (canRetry: phase가 terminal일 때)
2. 현재 작업의 job_id와 attempt_count를 기록
3. "재시도" 버튼을 클릭
4. browser_snapshot으로 결과 확인:
   - "재시도 작업이 생성되었습니다." 토스트가 표시되는지
   - ⚠️ **주의: BE는 새 Job을 생성하지 않고 같은 Job을 업데이트함**
   - 같은 작업 상세 페이지(/jobs/{sameJobId})에 머무는지 확인
   - phase가 "running"으로 변경되었는지 확인
5. browser_evaluate로 서버 상태 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return {
     job_id: job.job_id,
     phase: job.phase,
     attempt_count: job.attempt_count
   };
   ```
6. attempt_count가 이전보다 1 증가했는지 확인
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 재시도 → **같은 Job**이 `running`으로 변경, `attempt_count` +1
- ⚠️ FE는 새 Job 생성을 기대하지만, BE는 같은 Job 업데이트 (계약 불일치 확인)

---

## 테스트 케이스 11: parent_job_id 필드 계약 불일치 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(재시도 후 작업의 상세 페이지에서)

⚠️ **알려진 이슈**: FE `JobStatusResponse` 타입은 `parent_job_id: string | null` 필드를 기대하지만,
BE `JobStatusResponse` 스키마와 DB 모델에는 해당 필드가 존재하지 않음.

1. 작업을 취소한 후 "재시도" 실행
2. browser_evaluate로 서버 응답에 parent_job_id 필드가 있는지 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return {
     hasParentJobId: 'parent_job_id' in job,
     parentJobId: job.parent_job_id,
     keys: Object.keys(job)
   };
   ```
3. parent_job_id 필드 존재 여부 확인
4. FE에서 "원본 작업:" 링크 영역이 렌더링되는지 확인
5. 만약 parent_job_id가 null/undefined이면 링크가 표시되지 않아야 함
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- ⚠️ BE에 `parent_job_id` 필드 미구현 → FE에서 항상 null → "원본 작업" 링크 미표시
- 이 불일치는 BE에 `parent_job_id` 컬럼 추가가 필요한 사항으로 기록

---

## 테스트 케이스 12: 승인/거부 버튼 (awaiting_approval 상태)

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(awaiting_approval 상태의 작업 상세 페이지에서)

1. browser_snapshot으로 액션 버튼 영역 캡처
2. 다음 버튼이 모두 표시되는지 확인:
   - "승인" 버튼 (CheckCircle, canApprove)
   - "거부" 버튼 (XCircle, destructive, canReject)
   - "취소" 버튼 (Ban, canCancel)
3. "승인" 버튼 클릭
4. browser_snapshot으로 결과 확인:
   - "대본이 승인되었습니다." 토스트
   - 상태가 "에셋 생성"으로 변경
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 승인 대기 상태에서 승인/거부/취소 버튼 모두 표시

---

## 테스트 케이스 13: 완료 작업의 다운로드 버튼

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(completed 상태의 작업 상세 페이지에서)

1. browser_snapshot으로 액션 버튼 확인
2. "다운로드" 버튼(Download 아이콘)이 보이는지 확인
3. 다운로드 링크의 href가 올바른 형태인지 확인:
   `{API_BASE_URL}/api/v1/videos/{jobId}/download`
4. "취소" 버튼은 보이지 않는지 확인 (완료 = terminal)
5. "재시도" 버튼은 보이는지 확인 (terminal이므로 canRetry = true)
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 완료: 다운로드 + 재시도 표시, 취소/승인/거부 미표시

---

## 테스트 케이스 14: 로딩 상태 (스켈레톤/스피너) 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 로그인 후 browser_navigate로 작업 상세 페이지 URL에 직접 접속
2. 페이지 로딩 즉시 browser_snapshot 캡처
3. 다음을 확인:
   - 데이터 로딩 중 스피너 또는 스켈레톤 UI가 표시되는지
   - "로딩 중..." 텍스트 또는 Loader2 아이콘이 보이는지
4. 데이터 로딩 완료 후 browser_snapshot
5. 스피너가 사라지고 실제 데이터가 표시되는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 데이터 fetch 중 적절한 로딩 UI 표시

---

## 테스트 케이스 15: 타 사용자 작업 상세 접근 차단

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. test@example.com으로 로그인
2. browser_evaluate로 다른 사용자의 작업 ID를 조회 시도:
   (관리자 API가 아닌, 직접 URL 조작)
3. browser_navigate로 http://localhost:5173/jobs/{타인의jobId} 에 접속
4. browser_snapshot으로 결과 확인:
   - 403 에러 또는 "접근 권한이 없습니다" 메시지 표시
   - 또는 빈 상태 / 에러 처리
5. 자신의 작업 상세 페이지에는 정상 접근 가능한지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- IDOR(Insecure Direct Object Reference) 방지 — 타인 작업 접근 불가

---

## 테스트 케이스 16: 탭 전환 시 데이터 유지 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(작업 상세 페이지에서)

1. "진행 상세" 탭(기본)에서 browser_snapshot으로 데이터 확인
2. "대본" 탭 클릭 → browser_snapshot으로 대본 데이터 확인
3. "결과" 탭 클릭 → browser_snapshot으로 결과 데이터 확인
4. 다시 "진행 상세" 탭 클릭
5. browser_snapshot으로 이전과 동일한 데이터가 표시되는지 확인
6. 탭 전환 시 데이터가 리로드되지 않고 캐시된 상태인지 확인
   (network_requests에서 탭 전환마다 API 재호출 여부)
7. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 탭 전환 시 데이터 유지, 불필요한 API 재호출 없음

---

## 테스트 케이스 17: 진행 중 작업 — 실시간 진행률 업데이트

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(진행 중인 작업의 상세 페이지에서)

1. browser_snapshot으로 현재 진행률(progress_percent) 기록
2. 10초 대기
3. browser_snapshot으로 진행률 변화 확인
4. 다음을 확인:
   - progress_percent 값이 증가했는지
   - 파이프라인 인디케이터의 완료(초록) 스텝 수가 변했는지
   - 비용 배지의 값이 변했는지
   - 현재 단계 텍스트가 업데이트되었는지
5. SSE 또는 폴링으로 데이터가 실시간 갱신되는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 실시간 데이터 갱신 확인 (SSE 또는 폴링)

---

## 테스트 케이스 18: Max Retry 초과 시 UI 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(실패한 작업의 상세 페이지에서 — attempt_count가 max_attempts(3)에 도달한 경우)

1. browser_evaluate로 작업의 attempt_count 확인:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/api/v1/videos/{jobId}', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const job = await res.json();
   return { attempt_count: job.attempt_count, phase: job.phase };
   ```
2. attempt_count가 3(max)인 경우:
   - "재시도" 버튼 클릭
   - BE가 403 응답("Max retry attempts reached")을 반환하는지 확인
   - UI에서 적절한 에러 토스트가 표시되는지 확인
   - 또는 "재시도" 버튼이 비활성화/미표시인지 확인
3. attempt_count가 3 미만인 경우:
   - 재시도를 반복하여 3에 도달시킨 후 위 테스트 수행
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- max retry(3회) 초과 시 403 에러 → UI에서 적절한 피드백
- ⚠️ FE에 max retry 도달 시 버튼 비활성화 로직이 없을 수 있음 (확인 필요)

---

## 테스트 케이스 19: 완료 Job 비디오 재생 및 다운로드 상세 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(completed 상태의 작업 상세 페이지에서)

1. "결과" 탭 클릭
2. browser_snapshot으로 결과 영역 확인
3. `<video>` 요소 검증:
   - `<video>` 태그가 존재하는지 확인
   - `controls` 속성이 있는지 확인
   - `src` 속성이 presigned URL 형태(S3 서명 파라미터 포함)인지 확인
   - browser_evaluate로 확인:
     ```javascript
     const video = document.querySelector('video');
     return {
       exists: !!video,
       src: video?.src,
       hasControls: video?.hasAttribute('controls'),
       readyState: video?.readyState,
       hasS3Signature: video?.src?.includes('X-Amz-Signature') || video?.src?.includes('AWSAccessKeyId')
     };
     ```
4. "MP4 파일 다운로드" 링크 검증:
   - href가 유효한 URL인지 확인
   - target="_blank" 또는 download 속성이 있는지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- `<video>` 요소에 유효한 presigned URL, controls 속성 존재
- 다운로드 링크가 동작

---

## 테스트 케이스 20: 미완료 Job의 Result 탭 상태별 표시

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

다양한 상태의 작업에서 "결과" 탭의 표시를 확인합니다:

### 진행 중인 작업 (queued/extracting 등)
1. "결과" 탭 클릭
2. "영상이 아직 생성되지 않았습니다." 메시지 확인
3. `<video>` 요소가 없는지 확인

### 실패한 작업 (failed)
4. failed 작업의 "결과" 탭 클릭
5. AlertTriangle 아이콘 + "생성 실패" 메시지 확인
6. error_message가 표시되는지 확인
7. `<video>` 요소가 없는지 확인

### 취소된 작업 (cancelled)
8. cancelled 작업의 "결과" 탭 클릭
9. "영상이 아직 생성되지 않았습니다." 메시지 확인

각 상태별 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 상태별로 적절한 메시지 표시, 미완료 시 비디오 플레이어 미표시

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(07-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
