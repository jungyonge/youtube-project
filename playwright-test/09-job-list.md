# 09. 작업 목록 (Job List) 테스트 (단위)

## 목적
작업 목록의 렌더링, 페이지네이션, 작업 카드, 자동 갱신을 테스트합니다.

### 핵심 동작 (use-jobs.ts)
- useJobList: refetchInterval 10_000 (10초마다 자동 갱신)

## 사전 조건
- 로그인 완료, 1개 이상 작업 존재

---

## 테스트 케이스 1: 작업 목록 페이지 렌더링

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 로그인 후 browser_navigate로 http://localhost:5173/jobs 에 접속
2. browser_snapshot으로 페이지 상태 캡처
3. 다음 요소가 존재하는지 확인:
   - "내 영상" 제목 (h1, text-2xl font-bold)
   - 작업 카드들 (JobCard)
   - 각 카드의 구성:
     - 상태 Badge (PHASE_COLORS + PHASE_LABELS)
     - 상대 시간 ("N분 전", "N시간 전" 등)
     - 진행률 바 (h-2, bg-primary)
     - 현재 단계 텍스트 또는 퍼센트
     - 비용: "$X.XX / $Y.YY" (formatCost)
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 카드 형태로 작업 목록 표시

---

## 테스트 케이스 2: 작업 카드 클릭으로 상세 이동

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 작업 목록에서 첫 번째 카드를 클릭
   (Card에 onClick={() => navigate(`/jobs/${job.job_id}`)} 있음)
2. browser_snapshot으로 작업 상세 페이지(/jobs/{jobId}) 이동 확인
3. browser_navigate_back으로 뒤로 이동
4. 작업 목록 페이지 복귀 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 카드 클릭 → 상세 페이지, 뒤로 → 목록 복귀

---

## 테스트 케이스 3: 전체 상태별 Badge 라벨/색상 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(작업 목록에서)

1. browser_snapshot으로 모든 카드의 Badge 확인
2. 다음 14개 상태의 한글 라벨과 색상이 올바른지 확인:
   - queued → "대기 중" (bg-slate-100)
   - extracting → "콘텐츠 추출" (bg-blue-100)
   - normalizing → "소스 정규화" (bg-blue-100)
   - building_evidence → "근거 구축" (bg-blue-100)
   - generating_script → "대본 생성" (bg-indigo-100)
   - reviewing_script → "대본 검수" (bg-indigo-100)
   - policy_review → "정책 검토" (bg-amber-100)
   - awaiting_approval → "승인 대기" (bg-yellow-100)
   - generating_assets → "에셋 생성" (bg-purple-100)
   - assembling_video → "영상 조립" (bg-orange-100)
   - completed → "완료" (bg-green-100)
   - failed → "실패" (bg-red-100)
   - cancelled → "취소됨" (bg-slate-100)
   - rejected → "거부됨" (bg-red-100)
3. 현재 목록에 있는 상태들이 올바르게 표시되는지 확인
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 각 phase에 맞는 한글 라벨 + 색상 클래스

---

## 테스트 케이스 4: 페이지네이션 동작

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(20개 이상의 작업이 있는 상태에서 — 없으면 "데이터가 적어 페이지네이션 미표시" 확인)

1. 작업 목록에서 페이지네이션 영역 확인
2. 다음을 확인:
   - 작업이 20개 이하면 페이지네이션이 **숨겨져** 있는지
     (data.has_next === false && page === 1이면 미표시)
   - 20개 초과 시:
     - "이전" 버튼 (1페이지에서 disabled)
     - "N / M" 형태 페이지 표시
     - "다음" 버튼
3. "다음" 클릭 → 2페이지 확인
4. "이전" 클릭 → 1페이지 복귀
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 20건 단위 페이지네이션

---

## 테스트 케이스 5: 카드 hover 효과

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 작업 목록에서 첫 번째 카드에 browser_hover
2. browser_snapshot으로 hover 스타일 확인:
   - cursor: pointer (cursor-pointer 클래스)
   - 그림자 효과 (hover:shadow-md)
3. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- hover 시 그림자 효과로 클릭 가능함을 시각적으로 표시

---

## 테스트 케이스 6: 작업 목록 최신순 정렬 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(2개 이상의 작업이 있는 상태에서)

1. 작업 목록에서 browser_snapshot
2. 각 카드의 생성 시간 확인
3. 첫 번째 카드가 가장 최근 작업인지 확인
4. 시간순으로 내림차순 정렬되어 있는지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 최신 작업이 상단에 위치

---

## 테스트 케이스 7: 빈 작업 목록 상태 확인

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(새로 가입한 계정으로 로그인, 작업 없는 상태)

1. browser_navigate로 http://localhost:5173/jobs 에 접속
2. browser_snapshot으로 빈 상태 확인
3. 다음을 확인:
   - "아직 생성된 영상이 없습니다." 또는 유사한 빈 상태 메시지
   - Film 아이콘 또는 빈 상태 일러스트
   - 페이지네이션이 표시되지 않는지
4. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 빈 상태 UI 정상 표시, 페이지네이션 숨김

---

## 테스트 케이스 8: 작업 목록 자동 갱신 확인 (10초 인터벌)

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

1. 작업 목록 페이지에서 browser_network_requests로 모니터링 시작
2. 12초 대기
3. browser_network_requests로 확인:
   - GET /api/v1/videos 요청이 자동으로 반복 호출되는지
   - 호출 간격이 약 10초인지
4. 자동 갱신 중 UI가 깜빡이거나 스크롤 위치가 변하지 않는지 확인
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 10초 인터벌 자동 갱신, UI 깜빡임 없음

---

## 테스트 케이스 9: 작업 목록에서 진행 중 작업의 실시간 상태 변화

### 프롬프트

```
Playwright MCP를 사용하여 다음 테스트를 수행해줘:

(진행 중인 작업이 있는 상태에서)

1. 작업 목록에서 진행 중인 작업 카드 확인
2. browser_snapshot으로 현재 상태 Badge와 진행률 기록
3. 10~15초 대기 (자동 갱신 대기)
4. browser_snapshot으로 변화 확인:
   - 상태 Badge가 변경되었는지 (예: extracting → normalizing)
   - 진행률 바의 width가 증가했는지
5. 결과를 정리해서 알려줘

(자동 수정 규칙: 00-setup.md Auto-Fix Protocol 적용)
```

### 기대 결과
- 목록에서도 실시간 상태 반영

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(09-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
