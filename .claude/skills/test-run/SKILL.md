---
name: test-run
description: Playwright MCP 테스트를 자동 실행하고, 실패 시 코드를 자동 수정한 뒤 재테스트합니다.
user-invocable: true
argument-hint: "[test-file|all]"
---

# Playwright 테스트 자동 실행 + 자동 수정 스킬

당신은 20년차 QA 엔지니어입니다. 아래 절차에 따라 Playwright MCP 테스트를 실행하고, 실패 시 코드를 자동 수정한 뒤 재테스트합니다.

## 입력 인자

- `$ARGUMENTS` : 테스트 파일명 (예: `07-job-detail.md`) 또는 `all`
- 인자가 없으면 `all`로 간주
- 숫자만 입력 시 (예: `07`) → `07-*.md` 패턴으로 매칭

## 실행 절차

### Step 0: 준비

1. `playwright-test/00-setup.md`를 읽어 **Auto-Fix Protocol**, 테스트 계정, 공통 설정을 숙지한다.
2. `playwright-test/TEST-OVERVIEW.md`를 읽어 현재 테스트 현황을 파악한다.
3. 대상 파일을 결정한다:
   - `all` → `01-health-check.md` ~ `23-video-playback-download.md` (번호순)
   - 특정 파일 → 해당 파일만
4. Playwright MCP 브라우저가 열려 있는지 확인한다. 열려 있지 않으면 `browser_navigate`로 `http://localhost:5173`에 접속하여 초기화한다.

### Step 1: TC 순차 실행

대상 파일의 각 TC(테스트 케이스 / 통합 시나리오)를 **순서대로** 실행한다.

각 TC마다:

1. **TC 프롬프트 내 지시사항을 그대로 실행한다** — Playwright MCP 도구(`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill_form`, `browser_evaluate`, `browser_console_messages`, `browser_network_requests`, `browser_wait_for` 등)를 사용하여 지시된 조작과 검증을 수행한다.

2. **판정한다:**
   - `PASS` — "기대 결과" 섹션의 조건을 모두 충족
   - `FAIL` — 하나라도 미충족
   - `SKIP` — 사전 조건 미충족 (예: awaiting_approval 작업이 없음, 데이터 부족 등)

3. **TEST-OVERVIEW.md를 즉시 업데이트한다** — 해당 TC 행의 상태를 `PASS` / `FAIL` / `SKIP`으로 변경, 비고에 간단한 메모 추가.

### Step 2: 자동 수정 플로우 (FAIL인 경우만)

`00-setup.md`의 **Auto-Fix Protocol**을 정확히 따른다:

```
Step A: 실패 원인 분류
  [FE-BUG]      → frontend/src/ 수정
  [BE-BUG]      → app/ 수정
  [CONTRACT]    → 적절한 쪽 수정 (수정 우선순위 가이드 참조)
  [FE-MISSING]  → frontend/src/ 구현
  [BE-MISSING]  → app/ 구현
  [ENV]         → 수정 불가, BUG 기록만
  [TEST]        → playwright-test/*.md 수정

Step B: 코드 수정
  - 원인 파일을 읽고 문제 지점 파악
  - 기존 패턴/컨벤션 유지, 최소 범위 수정
  - 다른 TC에 영향 주는 변경 금지
  - 수정 내용을 한 줄로 요약

Step C: 재테스트
  - 동일 TC를 처음부터 재실행
  - PASS → TEST-OVERVIEW.md에 "Auto-Fixed: {요약}" 기록
  - FAIL → Step B 한 번 더 시도

Step D: 최대 2회 재시도
  - 3회 모두 실패 → TEST-OVERVIEW.md에 FAIL 기록
  - "발견된 버그 / 이슈 로그" 테이블에 상세 기록
  - 다음 TC로 진행 (멈추지 않는다)
```

### 수정 금지 항목
- 테스트 통과만을 위한 하드코딩
- 보안 관련 코드 약화
- DB 마이그레이션이 필요한 스키마 변경 (기록만)
- 다른 TC를 깨뜨리는 광범위 리팩토링

### Step 3: 다음 TC로 진행

한 TC의 판정 + (필요시) 자동 수정이 끝나면 **바로 다음 TC**로 진행한다. 절대 멈추지 않는다.

### Step 4: 실행 요약 리포트

모든 TC 완료 후 아래 형태로 리포트를 출력한다:

```
## 테스트 실행 요약

- 실행 일시: {날짜}
- 대상: {파일명 또는 all}
- 총 TC: N개
- PASS: N개
- FAIL: N개
- SKIP: N개
- Auto-Fixed: N개

### 수정한 파일
| 파일 | 변경 요약 | 관련 TC |
|------|-----------|---------|
| ... | ... | ... |

### 미해결 이슈
| TC | 원인 분류 | 설명 |
|----|-----------|------|
| ... | ... | ... |
```

그리고 `TEST-OVERVIEW.md` 하단의 **"테스트 실행 기록"** 테이블에 이 실행 결과를 추가한다.

## 중요 규칙

- **한 번에 하나의 TC만 실행** — 병렬 실행하지 않는다.
- **브라우저 상태 관리** — TC 간 로그인 상태가 유지되면 재로그인하지 않는다. 필요 시 재로그인한다.
- **스크린샷 = browser_snapshot** — 항상 `browser_snapshot`으로 현재 상태를 확인한 후 판정한다.
- **API 직접 호출 = browser_evaluate** — TC에서 `browser_evaluate`로 API를 호출하라고 하면 그대로 따른다.
- **TC 실패해도 멈추지 않는다** — 기록하고 다음으로 넘어간다.
- **수정 시 CLAUDE.md의 기술 스택과 아키텍처를 준수**한다.
