# 00. 테스트 환경 설정

## 사전 준비

### 1. Docker로 전체 서비스 기동

```bash
docker compose up --build -d
```

서비스가 모두 올라올 때까지 대기 (약 30~60초):
- **API**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **MinIO**: localhost:9000 (콘솔: localhost:9001)

### 2. 헬스체크 확인

```
GET http://localhost:8000/health
```
- `status: "healthy"` 확인
- components 중 database, redis, minio 모두 healthy인지 확인

### 3. 프론트엔드 개발 서버 (Docker에 포함되지 않은 경우)

```bash
cd frontend && npm run dev
```

기본 URL: `http://localhost:5173`

---

## Playwright MCP 테스트 공통 설정

### 기본 URL
- **Frontend**: `http://localhost:5173`
- **API**: `http://localhost:8000`

### 테스트 계정 정보
- **일반 사용자**: `test@example.com` / `testpassword123`
- **관리자**: `admin@example.com` / `adminpassword123`

> 테스트 전 회원가입을 통해 계정을 먼저 생성해야 합니다.

### 라우트 구조 (App.tsx 기준)
| 경로 | 페이지 | 보호 | 비고 |
|------|--------|------|------|
| `/login` | 로그인 | Public | |
| `/register` | 회원가입 | Public | |
| `/dashboard` | 대시보드 | Protected | 영상 생성 + 내 영상 |
| `/jobs` | 작업 목록 | Protected | |
| `/jobs/:jobId` | 작업 상세 | Protected | SSE 실시간 |
| `/jobs/:jobId/approval` | 승인 페이지 | Protected | awaiting_approval만 |
| `/admin` | 관리자 | Protected + Admin | role=admin만 |
| `*` (기타) | - | - | `/dashboard`로 리다이렉트 |

### 레이아웃 구조
- **RootLayout**: Sidebar(좌측) + Header(상단) + Main(콘텐츠)
- **Sidebar**: 네비게이션(대시보드, 내 영상, 관리), 테마 토글, 로그아웃
- **Header**: 일일 할당량 배지("오늘 N/M"), 사용자 이메일

### Playwright MCP 사용 시 공통 패턴

1. `browser_navigate`로 페이지 이동
2. `browser_snapshot`으로 현재 페이지 상태 캡처 (accessibility tree)
3. `browser_fill_form` / `browser_click`으로 상호작용
4. `browser_snapshot`으로 결과 확인
5. `browser_console_messages`로 에러 로그 확인
6. `browser_network_requests`로 API 호출 확인

### 테스트 데이터 정리

각 테스트 시나리오는 독립적으로 실행 가능해야 합니다.
통합 테스트의 경우 선행 테스트(회원가입 -> 로그인)가 완료된 상태에서 진행합니다.

### 로그인 헬퍼 (반복 사용)

```
1. browser_navigate로 http://localhost:5173/login 에 접속
2. browser_snapshot으로 로그인 폼 확인
3. 이메일 필드에 값 입력
4. 비밀번호 필드에 값 입력
5. "로그인" 버튼 클릭
6. browser_snapshot으로 대시보드 이동 확인
```

---

## 테스트 자동 수정 규칙 (Auto-Fix Protocol)

> 모든 TC에서 공통으로 적용되는 규칙입니다.
> 각 TC 프롬프트 마지막에 "자동 수정 규칙은 00-setup.md의 Auto-Fix Protocol을 따른다"로 참조합니다.

### 판정 기준

| 판정 | 조건 | 후속 조치 |
|------|------|-----------|
| `PASS` | 기대 결과 100% 충족 | TEST-OVERVIEW.md 상태 업데이트 → 다음 TC |
| `FAIL` | 기대 결과 미충족 | 자동 수정 플로우 진입 |
| `SKIP` | 사전 조건 미충족 (데이터 없음 등) | TEST-OVERVIEW.md에 SKIP + 사유 기록 → 다음 TC |

### 자동 수정 플로우 (FAIL일 때만 실행)

```
Step A: 실패 원인 분류
  - [FE-BUG]      프론트엔드 코드 버그           → frontend/src/ 수정
  - [BE-BUG]      백엔드 코드 버그               → app/ 수정
  - [CONTRACT]    FE↔BE 스키마/타입 불일치       → 둘 중 적절한 쪽 수정
  - [FE-MISSING]  프론트엔드 기능 미구현          → frontend/src/ 구현
  - [BE-MISSING]  백엔드 엔드포인트/필드 미구현   → app/ 구현
  - [ENV]         환경/인프라/데이터 문제          → 수정 불가, BUG 기록만
  - [TEST]        테스트 시나리오 자체 오류        → playwright-test/*.md 수정

Step B: 코드 수정 (ENV 제외)
  1. 원인 파일을 읽고 문제 지점 파악
  2. 기존 코드 패턴/컨벤션을 유지하며 최소 범위로 수정
  3. 수정 시 주의사항:
     - 다른 TC에 영향을 줄 수 있는 변경은 하지 않는다
     - 타입 변경 시 해당 타입을 사용하는 다른 곳도 함께 수정
     - import 누락 주의
  4. 수정 내용을 한 줄로 요약 기록

Step C: 재테스트
  1. 동일 TC를 처음부터 재실행
  2. 결과 판정:
     - PASS → TEST-OVERVIEW.md에 PASS + 비고: "Auto-Fixed: {수정 요약}" 기록
     - FAIL → 한 번 더 수정 시도 (Step B 반복)

Step D: 최대 재시도 제한
  - 최대 2회까지만 자동 수정 시도 (원본 + 수정1 + 수정2 = 총 3회 실행)
  - 3회 모두 실패 시:
    → TEST-OVERVIEW.md에 FAIL 기록
    → 비고에 "Auto-Fix 실패 (2회 시도): {원인 요약}" 기록
    → 발견된 버그 테이블에 상세 이슈 추가
    → 다음 TC로 진행 (멈추지 않는다)
```

### 수정 우선순위 가이드

| 불일치 유형 | 어느 쪽을 수정? | 이유 |
|------------|----------------|------|
| VideoStyle enum 불일치 | **BE** 수정 (FE 값 수용) | FE가 사용자에게 노출된 값 |
| Source URL 필수 여부 | **BE** 수정 (optional로) | custom_text는 URL 불필요 |
| 응답 필드명 (user_id vs user_email) | **BE** 수정 (email join) | FE가 사용자에게 보여줄 값 |
| 응답 구조 (중첩 vs 플랫) | **FE** 수정 (매핑 추가) | BE 구조가 더 확장 가능 |
| 엔드포인트 미구현 | **BE** 구현 | FE가 이미 호출 중 |
| UI 동작 버그 | **FE** 수정 | |
| API 로직 버그 | **BE** 수정 | |

### 수정 금지 항목
- 테스트 통과만을 위한 하드코딩 (예: if test then return mock)
- 보안 관련 코드 약화 (인증/인가 우회)
- DB 마이그레이션이 필요한 스키마 변경 (기록만 하고 SKIP)
- 다른 TC를 깨뜨릴 수 있는 광범위 리팩토링

---

## 연속 실행 프롬프트 템플릿

전체 TC를 순서대로 연속 실행하려면 아래 프롬프트를 사용합니다:

```
Playwright MCP를 사용하여 {XX}-{파일명}.md의 모든 테스트 케이스를 순서대로 실행해줘.

실행 규칙:
1. 00-setup.md의 "Auto-Fix Protocol"을 따른다
2. 각 TC 실행 후 판정(PASS/FAIL/SKIP) → TEST-OVERVIEW.md 즉시 업데이트
3. FAIL 시 자동 수정 플로우 진입 (최대 2회 재시도)
4. 한 TC가 끝나면 바로 다음 TC로 진행 (멈추지 않는다)
5. 모든 TC 완료 후 실행 요약 리포트 출력:
   - 총 TC 수, PASS, FAIL, SKIP, Auto-Fixed 수
   - 수정한 파일 목록 + 변경 요약
   - 미해결 이슈 목록
```

---

> **테스트 완료 후 체크리스트**
> 1. 위 테스트 케이스를 모두 실행했으면 [TEST-OVERVIEW.md](./TEST-OVERVIEW.md)의 해당 섹션(00-*)에서 각 TC의 상태를 업데이트하세요.
> 2. 버그 발견 시 TEST-OVERVIEW.md 하단 "발견된 버그 / 이슈 로그" 테이블에 기록하세요.
> 3. "테스트 실행 기록" 테이블에 실행 일자, 범위, 결과를 추가하세요.
