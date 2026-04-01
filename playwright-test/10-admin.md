# 10. 관리자 (Admin) 테스트 (단위)

## 목적
관리자 페이지의 통계 카드, 비용 차트, 작업 테이블, 강제 취소, 접근 제어를 테스트합니다.

## 사전 조건
- 관리자 계정으로 로그인 (role: "admin")

---

## 테스트 케이스 1: 관리자 페이지 전체 렌더링

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. admin@example.com / adminpassword123 으로 로그인
2. Sidebar에서 "관리" 메뉴를 클릭하여 /admin 이동
3. browser_snapshot으로 관리자 페이지 캡처
4. 다음 3개 섹션이 존재하는지 확인:
   - 통계 카드 4개 (AdminStatsCards)
   - 비용 차트 (AdminCostChart — "일별 비용 추이 (최근 30일)")
   - 전체 작업 테이블 (AdminJobTable)
5. "관리자" 제목(h1)이 보이는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 3개 섹션이 순서대로 렌더링

---

## 테스트 케이스 2: 통계 카드 4개 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지에서)

1. browser_snapshot으로 통계 카드 영역 캡처
2. 4개 카드가 그리드(sm:grid-cols-2 lg:grid-cols-4)로 표시되는지 확인
3. 각 카드 확인:
   - "오늘 생성" + Film 아이콘 — "N건" 형태
   - "성공률" + CheckCircle 아이콘 — "N.N%" 형태
   - "일 비용" + DollarSign 아이콘 — "$X.XX" 형태
   - "활성 작업" + Activity 아이콘 — "N건" 형태
4. 값이 합리적인 범위인지 확인 (음수가 아닌지 등)
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 4개 카드에 실시간 통계 데이터

---

## 테스트 케이스 3: 비용 차트 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지에서)

1. browser_snapshot으로 비용 차트(AdminCostChart) 영역 캡처
2. "일별 비용 추이 (최근 30일)" 제목 확인
3. AreaChart (Recharts)가 렌더링되었는지 확인:
   - X축: 날짜 (MM-DD 형태)
   - Y축: 비용 ($N 형태)
   - Area 그래프가 표시되는지
4. 데이터가 없으면 빈 차트가 표시되는지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 30일간 비용 추이 차트 표시

---

## 테스트 케이스 4: 작업 테이블 상태 필터링

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지의 "전체 작업" 섹션에서)

1. 상태 필터 드롭다운 확인 — "전체"가 기본 선택
2. 드롭다운 옵션 10개 확인:
   전체, 대기, 추출 중, 대본 생성, 승인 대기, 에셋 생성, 영상 조립, 완료, 실패, 취소
3. "완료"로 변경 후 browser_snapshot
4. 테이블에 완료 상태 작업만 표시되는지 확인
5. "전체"로 복원
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 상태 필터에 따른 테이블 데이터 변경

---

## 테스트 케이스 5: 작업 테이블 이메일 검색

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지에서)

1. 이메일 검색 입력 필드(placeholder: "이메일 검색...")에 "test@example.com" 입력
2. browser_snapshot으로 필터링 결과 확인
3. "사용자" 컬럼에 해당 이메일만 표시되는지 확인
4. 검색어 삭제 후 전체 목록 복원 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 이메일 필터링 동작

---

## 테스트 케이스 6: 작업 테이블 컬럼 구조

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지의 작업 테이블에서)

1. browser_snapshot으로 테이블 헤더 확인
2. 6개 컬럼 확인:
   - "사용자" — 이메일 (text-xs)
   - "주제" — 최대 200px truncate
   - "상태" — Badge (PHASE_COLORS + PHASE_LABELS)
   - "비용" — 우측 정렬, formatCost
   - "생성일" — text-xs, formatDate
   - 액션 — Eye(보기) + Ban(강제 취소) 아이콘 버튼
3. 데이터 행이 올바르게 표시되는지 확인
4. 주제가 길 경우 truncate 처리되는지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 6개 컬럼 + 적절한 포맷팅

---

## 테스트 케이스 7: 강제 취소 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지의 작업 테이블에서)

1. 진행 중인(terminal이 아닌) 작업 행 찾기
2. 해당 행의 강제 취소 버튼(Ban, text-destructive)이 보이는지 확인
3. 이미 완료/취소된 작업에는 Ban 버튼이 **없는지** 확인
   (TERMINAL_STATES.includes(job.phase)이면 미표시)
4. 강제 취소 버튼 클릭
5. browser_snapshot으로 결과 확인:
   - "강제 취소되었습니다." 토스트 (useForceCancel의 onSuccess)
   - 해당 작업 상태가 "취소됨"으로 변경
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 관리자만 강제 취소 가능

---

## 테스트 케이스 8: 보기 버튼으로 상세 이동

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 작업 테이블에서 Eye 아이콘 버튼 클릭
2. 해당 작업의 상세 페이지(/jobs/{jobId})로 이동 확인
3. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- navigate(`/jobs/${job.job_id}`) 동작

---

## 테스트 케이스 9: 일반 사용자의 관리자 페이지 접근 차단

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. test@example.com (일반 사용자)으로 로그인
2. browser_navigate로 http://localhost:5173/admin 에 접속
3. browser_snapshot으로 결과 확인
4. ProtectedRoute(requireAdmin=true)에 의해:
   - user.role !== "admin" → Navigate to="/dashboard" replace
   - /dashboard로 리다이렉트 확인
5. Sidebar에서 "관리" 메뉴가 보이지 않는지 확인
6. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 일반 사용자 → `/dashboard` 리다이렉트

---

## 테스트 케이스 10: 테이블 빈 상태

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지에서)

1. 존재하지 않는 이메일로 검색: "nobody@example.com"
2. browser_snapshot으로 결과 확인
3. "작업이 없습니다." 메시지가 표시되는지 확인
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 검색 결과 없으면 빈 상태 메시지

---

## 테스트 케이스 11: 상태 + 이메일 복합 필터링

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지에서)

1. 이메일 검색: "test@example.com" 입력
2. 상태 필터: "완료" 선택
3. browser_snapshot으로 결과 확인:
   - test@example.com 사용자의 완료 작업만 표시되는지
4. 상태를 "전체"로 변경
5. 해당 사용자의 모든 작업이 표시되는지 확인
6. 이메일 삭제 후 상태를 "실패"로 변경
7. 모든 사용자의 실패 작업이 표시되는지 확인
8. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 복합 필터링 정상 동작

---

## 테스트 케이스 12: 작업 테이블 페이지네이션

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지의 작업 테이블에서)

1. 현재 표시된 행 수 확인
2. 페이지네이션 영역 확인:
   - 20개 이하: 페이지네이션 미표시 확인
   - 20개 초과: "이전" / "N / M" / "다음" 표시
3. "다음" 클릭 시 2페이지 데이터가 다른 행인지 확인
4. "이전" 클릭 시 1페이지로 복귀 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 관리자 테이블 페이지네이션 정상 동작

---

## 테스트 케이스 13: 강제 취소 확인 다이얼로그 여부

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지에서 진행 중인 작업에 대해)

1. 강제 취소 버튼(Ban) 클릭
2. browser_snapshot으로 확인:
   - 확인 다이얼로그가 표시되는지 (예: "정말로 강제 취소하시겠습니까?")
   - 또는 바로 취소 처리되는지
3. 확인 다이얼로그가 있는 경우:
   - "취소" 클릭 → 작업 상태 유지 확인
   - 다시 강제 취소 → "확인" 클릭 → 취소 처리 확인
4. 확인 다이얼로그가 없는 경우:
   - 즉시 취소됨 → 위험한 작업에 대한 확인 절차 부재 기록
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 파괴적 행위(강제 취소)에 대한 확인 절차 검증

---

## 테스트 케이스 14: 통계 데이터 새로고침

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(관리자 페이지에서)

1. 통계 카드의 "오늘 생성" 건수 기록
2. 새 탭이나 다른 방법으로 작업 1건 생성 (또는 이미 생성 중인 작업 완료 대기)
3. 관리자 페이지에서 browser_navigate로 /admin 재접속 (새로고침)
4. 통계 카드 확인:
   - "오늘 생성" 건수가 업데이트되었는지
   - "활성 작업" 건수가 변했는지
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 새로고침 시 최신 통계 반영

---

## 테스트 케이스 15: Admin Stats API 응답 구조 vs FE 매핑 검증

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

⚠️ **알려진 이슈**: BE `/admin/stats` 응답은 중첩 구조이고, FE `AdminStats` 타입은 플랫 구조

### Step 1: BE 응답 구조 확인
1. admin@example.com 으로 로그인
2. browser_evaluate로 admin stats API 직접 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/admin/stats', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const stats = await res.json();
   return {
     topLevelKeys: Object.keys(stats),
     hasNestedJobs: typeof stats.jobs === 'object',
     hasNestedCost: typeof stats.cost === 'object',
     hasFlatTodayJobs: 'today_jobs' in stats,
     hasFlatSuccessRate: 'success_rate' in stats,
     fullResponse: stats
   };
   ```
3. 응답 구조 확인:
   - BE: `{ date, jobs: { created, completed, ... }, cost: { total_usd, by_provider }, performance: { ... } }`
   - FE 기대: `{ today_jobs, success_rate, daily_cost_usd, active_jobs }`

### Step 2: FE 통계 카드 렌더링 확인
4. /admin 페이지에서 browser_snapshot
5. 4개 카드의 값이 실제로 표시되는지, NaN이나 undefined가 아닌지 확인:
   - "오늘 생성" → `stats.jobs.created` 에서 와야 함
   - "성공률" → `completed/created * 100` 계산 필요
   - "일 비용" → `stats.cost.total_usd` 에서 와야 함
   - "활성 작업" → `stats.jobs.active` 에서 와야 함
6. 값이 "NaN", "undefined", "$NaN" 등으로 표시되면 매핑 오류 기록

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- ⚠️ BE 중첩 구조와 FE 플랫 구조 간 매핑 불일치 가능성 높음
- 카드에 NaN/undefined 표시 시 → FE에서 응답 매핑 로직 수정 필요

---

## 테스트 케이스 16: Admin Jobs 테이블 user_id vs user_email 불일치

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

⚠️ **알려진 이슈**: BE `/admin/jobs` 응답에 `user_id`(UUID)만 포함, FE는 `user_email` 기대

### Step 1: BE 응답 필드 확인
1. admin 로그인
2. browser_evaluate로 admin jobs API 직접 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/admin/jobs?page=1&per_page=5', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   const result = await res.json();
   const firstItem = result.items?.[0];
   return {
     hasUserEmail: firstItem && 'user_email' in firstItem,
     hasUserId: firstItem && 'user_id' in firstItem,
     itemKeys: firstItem ? Object.keys(firstItem) : [],
     sampleItem: firstItem
   };
   ```
3. `user_email` 필드 존재 여부 확인

### Step 2: FE 테이블 렌더링 확인
4. /admin 페이지에서 작업 테이블의 "사용자" 컬럼 확인
5. browser_snapshot으로 "사용자" 컬럼에 표시되는 값 확인:
   - 이메일 표시 → 정상
   - UUID 표시 → BE에서 user_id만 반환하고 FE가 그대로 표시
   - 빈 값 / undefined → user_email 매핑 실패

### Step 3: 이메일 검색 동작 확인
6. 이메일 검색 필드에 "test@example.com" 입력
7. browser_network_requests로 실제 API 요청 확인:
   - 요청 URL에 `user_id` 파라미터가 사용되는지
   - 또는 `user_email` 파라미터가 사용되는지 (BE 미지원)
8. 검색 결과가 정상 동작하는지 확인

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- ⚠️ BE는 `user_id`만 반환 → FE "사용자" 컬럼에 UUID가 표시될 가능성
- ⚠️ 이메일 검색: BE API에 email 파라미터 미지원 → 검색 미동작 가능성

---

## 테스트 케이스 17: Admin Daily Stats 엔드포인트 존재 여부

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

⚠️ FE의 `useAdminDailyStats` 훅이 `/admin/stats/daily` 엔드포인트를 호출하지만,
BE에 이 엔드포인트가 구현되어 있지 않을 수 있음

### Step 1: 엔드포인트 존재 확인
1. admin 로그인
2. browser_evaluate로 daily stats API 호출:
   ```javascript
   const data = JSON.parse(localStorage.getItem('auth-storage'));
   const res = await fetch('http://localhost:8000/admin/stats/daily?days=30', {
     headers: { 'Authorization': 'Bearer ' + data.state.token }
   });
   return {
     status: res.status,
     statusText: res.statusText,
     body: res.status === 200 ? await res.json() : await res.text()
   };
   ```
3. 응답 확인:
   - 200 → 엔드포인트 존재, 응답 구조 확인
   - 404 → 엔드포인트 미구현 → 차트 데이터 소스 없음
   - 405 → 메서드 불일치

### Step 2: 비용 차트 데이터 확인
4. /admin 페이지에서 "일별 비용 추이" 차트 영역 확인
5. 차트에 데이터가 표시되는지, 빈 상태인지 확인
6. browser_console_messages로 에러 로그 확인 (404 등)

각 단계의 결과를 정리해줘.

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- ⚠️ `/admin/stats/daily` 엔드포인트 미구현 가능성 → 차트 데이터 로딩 실패
- BE에 해당 엔드포인트 추가 필요 여부 기록

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(10-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
