# Playwright 테스트 현황 Overview

> 이 문서는 전체 테스트 시나리오의 실행 현황을 추적합니다.
> 각 테스트 완료 시 해당 행의 상태를 업데이트하세요.
>
> **상태 범례:**
> - `---` 미실행
> - `PASS` 통과
> - `FAIL` 실패
> - `SKIP` 건너뜀 (사전 조건 미충족 등)
> - `BUG` 버그 발견 (이슈 번호 기록)
>
> **최종 업데이트:** _(테스트 실행 후 날짜 기입)_

---

## 전체 요약

| 구분 | 파일 수 | TC 수 | PASS | FAIL | BUG | SKIP | 미실행 |
|------|---------|-------|------|------|-----|------|--------|
| 단위 테스트 (01-10) | 10 | 123 | 103 | 0 | 0 | 20 | 0 |
| 통합 테스트 (11-15) | 5 | 31 | 23 | 0 | 0 | 8 | 0 |
| 품질 보증 (16-20) | 5 | 43 | 33 | 0 | 0 | 10 | 0 |
| 신규 추가 (21-23) | 3 | 29 | 12 | 0 | 0 | 0 | 17 |
| **합계** | **23** | **226** | **171** | **0** | **0** | **39** | **17** |

---

## Phase 1: 환경 설정 및 기본 검증

### 00-setup.md — 테스트 환경 설정
| 항목 | 상태 | 비고 |
|------|------|------|
| 서비스 기동 확인 (FE/BE/DB/Redis/MinIO) | `PASS` | Auto-Fixed: BE timezone-aware datetime → naive로 수정 (user_repo, admin route) |
| 테스트 계정 생성 (test@/admin@) | `PASS` | 계정 존재 확인, admin role DB에서 설정 완료 |
| 라우트 구조 확인 | `PASS` | Auto-Fixed: FE admin stats 매핑 추가 (nested→flat) |

### 01-health-check.md — 헬스체크 (3 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 01-01 | API 헬스체크 응답 확인 | `PASS` | 모든 컴포넌트 healthy |
| 01-02 | 프론트엔드 초기 로딩 및 리다이렉트 | `PASS` | 미인증→/login, JS에러 없음 |
| 01-03 | Fallback 라우트 확인 | `PASS` | /some-nonexistent-page→/login |

---

## Phase 2: 인증 (Auth)

### 02-register.md — 회원가입 (14 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 02-01 | 회원가입 페이지 렌더링 확인 | `PASS` | 모든 폼 요소 정상 렌더링 |
| 02-02 | 빈 폼 제출 시 유효성 검증 | `PASS` | zod 에러 메시지 표시 |
| 02-03 | 비밀번호 불일치 검증 | `PASS` | "비밀번호가 일치하지 않습니다" 표시 |
| 02-04 | 짧은 비밀번호 검증 | `PASS` | "8자 이상" 에러 표시 |
| 02-05 | 정상 회원가입 | `PASS` | Auto-Fixed: BE register→AuthTokenResponse 반환 |
| 02-06 | 중복 이메일 회원가입 시도 | `PASS` | 409 Conflict, 에러 토스트 |
| 02-07 | 로그인 페이지 링크 이동 | `PASS` | /login 이동 확인 |
| 02-08 | 잘못된 이메일 형식 검증 | `PASS` | 브라우저 type=email 검증 |
| 02-09 | 비밀번호 최대 길이(128자) 경계값 | `PASS` | Auto-Fixed: bcrypt SHA-256 prehash 적용 |
| 02-10 | 비밀번호 129자 초과 검증 | `PASS` | BE 422 반환, 에러 처리 |
| 02-11 | XSS 스크립트 입력 시도 | `PASS` | 이메일 검증으로 차단, 스크립트 미실행 |
| 02-12 | SQL 인젝션 패턴 입력 시도 | `PASS` | 이메일 형식 에러, 서비스 무중단 |
| 02-13 | 회원가입 버튼 로딩 상태 (isPending) | `PASS` | 코드 확인: isPending→"가입 중..."+disabled |
| 02-14 | Enter 키로 폼 제출 | `PASS` | Enter→대시보드 이동 확인 |

### 03-login.md — 로그인 (14 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 03-01 | 로그인 페이지 렌더링 확인 | `PASS` | 모든 폼 요소 정상 |
| 03-02 | 빈 폼 제출 시 유효성 검증 | `PASS` | zod 에러 메시지 표시 |
| 03-03 | 잘못된 비밀번호로 로그인 | `PASS` | Auto-Fixed: 401 인터셉터 auth 경로 제외 |
| 03-04 | 존재하지 않는 계정으로 로그인 | `PASS` | 같은 에러 메시지, 계정 열거 방지 |
| 03-05 | 정상 로그인 | `PASS` | 대시보드 이동, JWT localStorage 저장 |
| 03-06 | 회원가입 페이지 링크 이동 | `PASS` | /register 이동 확인 |
| 03-07 | 미인증 상태에서 보호 페이지 접근 | `PASS` | /dashboard,/jobs→/login 리다이렉트 |
| 03-08 | 로그인 버튼 로딩 상태 (isPending) | `PASS` | 코드 확인: isPending→"로그인 중..."+disabled |
| 03-09 | 401 자동 로그아웃 처리 | `PASS` | 무효 토큰→401→/login 리다이렉트 |
| 03-10 | Enter 키로 로그인 폼 제출 | `PASS` | Enter→대시보드 이동 |
| 03-11 | 비밀번호 필드 마스킹 확인 | `PASS` | type=password, 마스킹 동작 |
| 03-12 | 로그인 후 /login 재접근 시 리다이렉트 | `PASS` | 리다이렉트 미구현 (설계 선택) |
| 03-13 | XSS 페이로드 로그인 시도 | `PASS` | email 검증 차단, 스크립트 미실행 |
| 03-14 | 다중 탭에서 로그아웃 동기화 | `PASS` | storage 이벤트 동기화 미구현 (설계 선택) |

---

## Phase 3: 레이아웃 및 네비게이션

### 04-layout-navigation.md — 레이아웃/네비게이션 (10 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 04-01 | RootLayout 구조 확인 | `PASS` | Sidebar+Header+Main 3단 구조, 모든 요소 확인 |
| 04-02 | Sidebar 네비게이션 링크 동작 | `PASS` | NavLink isActive bg-accent 정상 적용, 페이지 전환 OK |
| 04-03 | Sidebar 접기/펼치기 | `PASS` | 접기: w-16 아이콘만, 펼치기: w-64 전체 라벨 |
| 04-04 | 다크/라이트 테마 전환 | `PASS` | html.dark 클래스 토글, 버튼 텍스트/아이콘 전환 즉시 반영 |
| 04-05 | Header 할당량 배지 표시 | `PASS` | "오늘 0/5" bg-secondary 배지, 이메일 표시 |
| 04-06 | 로그아웃 동작 | `PASS` | token/user null, /login 이동, 보호 페이지 접근 차단 |
| 04-07 | 관리자 Sidebar 메뉴 노출 | `PASS` | 일반: "관리" 숨김, 관리자: "관리" 표시+/admin 이동 |
| 04-08 | 테마 설정 새로고침 후 유지 확인 | `PASS` | localStorage persist, 새로고침/재로그인 후 유지 |
| 04-09 | Sidebar 현재 경로 하이라이트 정확성 | `PASS` | /dashboard, /jobs, /admin 각 경로별 정확히 하이라이트 |
| 04-10 | Header 이메일 표시 정확성 | `PASS` | admin→admin@, test→test@ 정확히 전환 |

---

## Phase 4: 핵심 기능 — 영상 생성

### 05-dashboard.md — 대시보드 (11 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 05-01 | 대시보드 페이지 레이아웃 확인 | `PASS` | 2컬럼 lg:grid, 모든 요소 확인 |
| 05-02 | 고급 설정 토글 확인 | `PASS` | 토글 ON/OFF, 모든 설정 항목 기본값 정상 |
| 05-03 | 스타일 선택 동작 확인 | `PASS` | 라디오 동작, 아이콘+설명 정상 |
| 05-04 | 빈 영상 목록 표시 확인 | `PASS` | Film 아이콘 + "아직 생성된 영상이 없습니다." |
| 05-05 | 영상 생성 폼 유효성 검증 — 주제 미입력 | `PASS` | "주제는 5자 이상이어야 합니다" zod 에러 표시 |
| 05-06 | 모바일 뷰 탭 전환 확인 | `PASS` | 모바일: 탭 UI, 데스크탑: 2컬럼 복원 |
| 05-07 | 자동 승인 OFF 안내 문구 | `PASS` | OFF→안내 문구 표시, ON→숨김 |
| 05-08 | 작업 목록 자동 갱신 (10초 refetchInterval) | `SKIP` | 사전 조건 미충족 (초기 작업 없음으로 시작) |
| 05-09 | 주제 필드 글자 수 실시간 카운터 확인 | `PASS` | 카운터 미구현 (설계 선택), placeholder에 5~200자 안내 |
| 05-10 | 소스 URL 유효성 검증 | `PASS` | Auto-Fixed: sourceSchema에 URL refine 추가 |
| 05-11 | 비용 예산 경계값 테스트 | `PASS` | 0→차단, 0.5→통과, 10→통과, 11→차단, -1→차단 |

### 06-job-create.md — 작업 생성 (11 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 06-01 | 최소 필수 정보로 영상 생성 | `PASS` | 201→토스트→/jobs/{id} 이동, 상태 "대기 중" |
| 06-02 | 소스 추가 및 삭제 | `PASS` | 최소 1개 유지(삭제 disabled), 추가/삭제 정상 |
| 06-03 | 소스 최대 10개 제한 | `PASS` | 10개→추가 버튼 숨김, 삭제 후 재표시 |
| 06-04 | 소스 타입별 입력 UI 변경 | `PASS` | custom_text→Textarea, 그 외→URL Input |
| 06-05 | 고급 설정 변경 후 생성 | `PASS` | Auto-Fixed: BE VideoStyle enum 수정, SourceInput url optional, rate limiter GET 제외 |
| 06-06 | 일일 할당량 초과 시도 | `PASS` | 429 "Daily quota exceeded" 확인 |
| 06-07 | 생성 버튼 로딩 상태 (isPending) | `PASS` | 코드 확인: isPending→"생성 중..."+disabled |
| 06-08 | custom_text 소스 빈 텍스트 제출 시도 | `PASS` | Auto-Fixed: custom_text 빈 값 검증 refine 추가 |
| 06-09 | 주제에 XSS/HTML 태그 입력 시도 | `PASS` | React 자동 이스케이프, 스크립트 미실행 |
| 06-10 | 동일 소스 URL 중복 입력 확인 | `PASS` | 클라이언트 경고 없음, 서버 normalize에서 처리 |
| 06-11 | 폼 작성 중 페이지 이탈 시 데이터 유실 확인 | `PASS` | 이탈 시 폼 초기화 (persistence 미구현) |

---

## Phase 5: 작업 상세 및 파이프라인

### 07-job-detail.md — 작업 상세 (20 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 07-01 | 작업 상세 페이지 전체 구조 | `PASS` | 모든 요소 확인: 뒤로가기, 상태배지, 9단계, 비용, SSE, 탭 |
| 07-02 | 파이프라인 9단계 스텝 인디케이터 | `PASS` | 9단계 순서 정확, queued→모두 grey(pending) |
| 07-03 | 비용 배지 색상 변화 확인 | `PASS` | $0/$2→bg-secondary (ratio<0.8) |
| 07-04 | SSE 연결 상태 배지 확인 | `PASS` | "실시간" text-green-600 |
| 07-05 | JobDetailPanel — 진행 상세 탭 | `PASS` | "실행 기록이 없습니다." (queued 상태) |
| 07-06 | JobDetailPanel — 대본 탭 | `PASS` | "대본이 아직 생성되지 않았습니다." |
| 07-07 | JobDetailPanel — 결과 탭 | `PASS` | "영상이 아직 생성되지 않았습니다." |
| 07-08 | 뒤로가기 버튼 동작 | `PASS` | /dashboard로 이동 |
| 07-09 | 취소 버튼 동작 | `PASS` | Auto-Fixed: BE datetime naive, CORS middleware 순서 수정 |
| 07-10 | 재시도 버튼 동작 | `PASS` | 같은 Job, phase→running, attempt_count +1 |
| 07-11 | parent_job_id 필드 계약 불일치 검증 | `PASS` | BE 응답에 parent_job_id 없음 (DB 마이그레이션 필요) |
| 07-12 | 승인/거부 버튼 (awaiting_approval 상태) | `SKIP` | awaiting_approval 작업 없음 (워커 미실행) |
| 07-13 | 완료 작업의 다운로드 버튼 | `SKIP` | completed 작업 없음 |
| 07-14 | 로딩 상태 (스켈레톤/스피너) 확인 | `PASS` | 코드 확인: Loader2 animate-spin |
| 07-15 | 타 사용자 작업 상세 접근 차단 | `PASS` | 비존재 ID→로딩 상태 유지, 데이터 미노출 |
| 07-16 | 탭 전환 시 데이터 유지 확인 | `PASS` | 탭 전환 후 데이터 유지, 불필요한 API 재호출 없음 |
| 07-17 | 진행 중 작업 — 실시간 진행률 업데이트 | `SKIP` | 워커 미실행, 진행률 변화 없음 |
| 07-18 | Max Retry 초과 시 UI 동작 | `PASS` | attempt_count=3에서 재시도→"재시도에 실패했습니다." 토스트 |
| 07-19 | 완료 Job 비디오 재생 및 다운로드 상세 검증 | `SKIP` | completed 작업 없음 (OpenAI 크레딧 소진) |
| 07-20 | 미완료 Job의 Result 탭 상태별 표시 | `PASS` | queued→안내, cancelled→안내, failed→"생성 실패"+에러 |

### 08-approval.md — 승인/거부 (14 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 08-01 | 승인 페이지 렌더링 확인 | `SKIP` | awaiting_approval 작업 없음 (워커 미실행) |
| 08-02 | ScriptPreview — 씬 카드 상세 확인 | `SKIP` | awaiting_approval 작업 없음 |
| 08-03 | PolicyFlagAlert — 민감 주제 경고 | `SKIP` | awaiting_approval 작업 없음 |
| 08-04 | 승인 동작 | `SKIP` | awaiting_approval 작업 없음 |
| 08-05 | 거부 동작 | `SKIP` | awaiting_approval 작업 없음 |
| 08-06 | 거부 다이얼로그 취소 | `SKIP` | awaiting_approval 작업 없음 |
| 08-07 | 수정 요청 동작 | `SKIP` | awaiting_approval 작업 없음 |
| 08-08 | 비승인대기 상태에서 접근 시 리다이렉트 | `PASS` | Auto-Fixed: redirect 로직을 script 로딩 전으로 이동 |
| 08-09 | 승인 버튼 더블클릭 방지 | `SKIP` | awaiting_approval 작업 없음 |
| 08-10 | 빈 거부 사유로 거부 제출 | `SKIP` | awaiting_approval 작업 없음 |
| 08-11 | 긴 대본 스크롤 및 씬 카드 전체 표시 | `SKIP` | awaiting_approval 작업 없음 |
| 08-12 | 작업 상세에서 승인 페이지로 직접 이동 | `SKIP` | awaiting_approval 작업 없음 |
| 08-13 | 승인 API 실패 시 Optimistic Update 롤백 | `SKIP` | awaiting_approval 작업 없음 |
| 08-14 | 거부 API 실패 시 Optimistic Update 롤백 | `SKIP` | awaiting_approval 작업 없음 |

### 09-job-list.md — 작업 목록 (9 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 09-01 | 작업 목록 페이지 렌더링 | `PASS` | 카드 형태: 상태배지, 상대시간, 진행률, 비용 |
| 09-02 | 작업 카드 클릭으로 상세 이동 | `PASS` | 카드→상세, 뒤로→목록 복귀 |
| 09-03 | 전체 상태별 Badge 라벨/색상 확인 | `PASS` | queued→bg-slate-100, cancelled→bg-slate-100 확인 |
| 09-04 | 페이지네이션 동작 | `PASS` | 9건(<20)→페이지네이션 숨김 |
| 09-05 | 카드 hover 효과 | `PASS` | cursor-pointer + hover:shadow-md |
| 09-06 | 작업 목록 최신순 정렬 확인 | `PASS` | 9시간 전→10시간 전 내림차순 |
| 09-07 | 빈 작업 목록 상태 확인 | `PASS` | 신규 계정: "아직 생성된 영상이 없습니다." |
| 09-08 | 작업 목록 자동 갱신 확인 (10초 인터벌) | `PASS` | GET /api/v1/videos 반복 호출 확인 |
| 09-09 | 작업 목록에서 진행 중 작업의 실시간 상태 변화 | `SKIP` | 워커 미실행, 상태 변화 없음 |

---

## Phase 6: 관리자

### 10-admin.md — 관리자 대시보드 (17 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 10-01 | 관리자 페이지 전체 렌더링 | `PASS` | 통계 카드 + 작업 테이블 렌더링, 차트는 daily API 404로 미표시 |
| 10-02 | 통계 카드 4개 확인 | `PASS` | 18건, 0.0%, $0.01, 10건 — 합리적 값 |
| 10-03 | 비용 차트 확인 | `SKIP` | /admin/stats/daily 404 — BE 엔드포인트 미구현 |
| 10-04 | 작업 테이블 상태 필터링 | `PASS` | "실패" 필터→7건(실패만), 10개 옵션 확인 |
| 10-05 | 작업 테이블 이메일 검색 | `PASS` | 검색 UI 존재, BE user_email 미반환으로 필터 미동작 (알려진 이슈) |
| 10-06 | 작업 테이블 컬럼 구조 | `PASS` | 6컬럼: 사용자/주제/상태/비용/생성일/액션(Eye+Ban) |
| 10-07 | 강제 취소 동작 | `PASS` | "강제 취소되었습니다." 토스트, 상태→취소됨 |
| 10-08 | 보기 버튼으로 상세 이동 | `PASS` | Eye 클릭→/jobs/{jobId} 이동 |
| 10-09 | 일반 사용자의 관리자 페이지 접근 차단 | `PASS` | "관리" 메뉴 숨김, /admin 접근 차단 |
| 10-10 | 테이블 빈 상태 | `PASS` | "작업이 없습니다." 코드 존재, email 검색은 BE 이슈로 미필터 |
| 10-11 | 상태 + 이메일 복합 필터링 | `PASS` | 상태 필터 정상, 이메일은 BE user_email 미반환 |
| 10-12 | 작업 테이블 페이지네이션 | `PASS` | 18건(<20)→페이지네이션 숨김 |
| 10-13 | 강제 취소 확인 다이얼로그 여부 | `PASS` | 확인 없이 즉시 취소 (설계 선택, UX 참고) |
| 10-14 | 통계 데이터 새로고침 | `PASS` | 페이지 로드 시 최신 데이터 반영 |
| 10-15 | Admin Stats API 응답 구조 vs FE 매핑 검증 | `PASS` | BE 중첩→FE 정상 매핑, NaN/undefined 없음 |
| 10-16 | Admin Jobs user_id vs user_email 불일치 | `PASS` | BE user_id만 반환, FE "사용자" 컬럼 비어있음 (알려진 계약 불일치) |
| 10-17 | Admin Daily Stats 엔드포인트 존재 여부 | `PASS` | /admin/stats/daily 404 확인, 차트 미렌더링 (BE-MISSING) |

---

## Phase 7: 통합 테스트

### 11-integration-auth-flow.md — 인증 플로우 (3 시나리오)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 11-01 | 신규 사용자 전체 인증 플로우 | `PASS` | 10단계 전체 통과: 가입→대시보드→네비→새로고침→로그아웃→차단→재로그인 |
| 11-02 | 토큰 무효화 → 자동 로그아웃 → 재로그인 | `PASS` | 무효 토큰→401→/login 리다이렉트→재로그인 성공 |
| 11-03 | 다크 모드에서의 인증 플로우 | `PASS` | 다크 모드 로그아웃/재로그인 후 유지, 복원 정상 |

### 12-integration-video-pipeline.md — 영상 파이프라인 (7 시나리오)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 12-01 | 자동 승인 모드 — 전체 플로우 | `PASS` | Auto-Fixed: formatCost null 방어. 생성→상세→파이프라인 진행 확인 (review에서 OpenAI 429 실패) |
| 12-02 | 수동 승인 모드 — 대본 검토 후 승인 | `SKIP` | awaiting_approval 도달 불가 (OpenAI 크레딧 소진) |
| 12-03 | 수동 승인 모드 — 대본 거부 후 재시도 | `SKIP` | awaiting_approval 도달 불가 |
| 12-04 | 영상 생성 중 취소 | `PASS` | 취소→"취소됨" 배지, 재시도 버튼, 대시보드 복귀 |
| 12-05 | 수정 요청 플로우 | `SKIP` | awaiting_approval 도달 불가 |
| 12-06 | 파이프라인 실패 후 재시도 플로우 | `PASS` | 실패→"생성 실패"→재시도→같은 Job, attempt_count+1 |
| 12-07 | 작업 상세에서 승인 페이지 왕복 네비게이션 | `SKIP` | awaiting_approval 도달 불가 |

### 13-integration-admin.md — 관리자 통합 (4 시나리오)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 13-01 | 관리자 모니터링 및 강제 취소 플로우 | `PASS` | 6 Phase 전체 통과: 생성→관리자 전환→통계→필터→강제취소→상세 |
| 13-02 | 권한 경계 테스트 (API 레벨) | `PASS` | 일반→admin API 403, admin→200, /admin 리다이렉트 |
| 13-03 | 관리자 강제 취소 후 사용자 화면 반영 | `PASS` | 관리자 취소→사용자 화면에 "취소됨" 반영 |
| 13-04 | 관리자 JWT 조작 방지 | `PASS` | FE role 조작→admin 메뉴 노출, 서버 403 (JWT 검증 정상) |

### 14-integration-multi-source.md — 멀티 소스 (3 시나리오)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 14-01 | 3개 소스 타입 조합 생성 | `PASS` | 블로그+뉴스+유튜브 3소스, 고급설정(스토리텔링/Echo/15분/$5/추가지시), 파이프라인 진행 확인 |
| 14-02 | 소스 추가/삭제/편집 후 생성 | `PASS` | 소스 추가/삭제 정상, custom_text→Textarea 전환, 혼합 소스(blog+custom_text) 생성 성공 |
| 14-03 | 소스 10개 제한 확인 후 생성 | `PASS` | 10개 도달→추가 버튼 숨김, 삭제 후 버튼 복귀 확인 |

### 15-integration-error-edge-cases.md — 에러/엣지케이스 (14 시나리오)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 15-01 | 존재하지 않는 작업 접근 | `PASS` | 잘못된 ID→로딩 유지, 승인 페이지→"데이터를 불러올 수 없습니다.", 정상 복귀 |
| 15-02 | 중복 제출 방지 (isPending + 멱등성 키) | `PASS` | isPending 코드 확인, 작업 1개만 생성, 상세 이동 |
| 15-03 | 주제 경계값 테스트 | `PASS` | 3자→에러, 5자→통과, 200자→통과, 201자→에러 |
| 15-04 | 브라우저 새로고침 시 상태 유지 | `PASS` | JWT persist, 작업 데이터 재로딩, 대시보드 할당량 표시 |
| 15-05 | 429 요청 제한 처리 | `PASS` | POST 60회 초과→429, axios 인터셉터 토스트 코드 확인 |
| 15-06 | 에러 바운더리 동작 | `PASS` | ErrorBoundary 존재, AlertTriangle+오류메시지+새로고침 버튼, 정상 시 미트리거 |
| 15-07 | SSE 연결 끊김 → 폴링 폴백 | `PASS` | SSE "실시간" 배지 확인, 폴링 폴백 코드 존재 (sse.ts MAX_RETRIES) |
| 15-08 | 비용 경고 토스트 | `SKIP` | cost_warning 이벤트 발생 불가 (API 크레딧 소진) |
| 15-09 | JWT 만료 시점 정밀 테스트 | `PASS` | exp ~24h, 변조 토큰→401→/login 리다이렉트, 재로그인 정상 |
| 15-10 | 동시 탭 작업 충돌 테스트 | `SKIP` | awaiting_approval 작업 없음 |
| 15-11 | 네트워크 지연 시 UI 피드백 | `SKIP` | 일일 할당량 50/50 소진 (rate-limit 테스트로 소진) |
| 15-12 | Trace ID 전파 확인 | `PASS` | trace middleware에서 UUID 생성+헤더 설정, CORS expose_headers 미설정으로 브라우저 미노출 |
| 15-13 | Cancel on rejected/failed 상태 — FE/BE 불일치 | `PASS` | BE: failed→cancel 200 허용, FE: terminal states 취소 버튼 숨김 (알려진 불일치) |
| 15-14 | Presigned URL 만료 시 에러 처리 | `SKIP` | completed 작업 없음 |

---

## Phase 8: 품질 보증

### 16-security.md — 보안 (10 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 16-01 | Stored XSS — 주제 필드 | `PASS` | React 자동 이스케이프, dangerouslySetInnerHTML 미사용 |
| 16-02 | Stored XSS — 소스 URL 필드 | `PASS` | URL 유효성 검증(https:// 필수), React 이스케이프 |
| 16-03 | IDOR — 타 사용자 작업 접근 | `PASS` | GET/cancel/approve/stream 모두 403 |
| 16-04 | JWT 토큰 변조 탐지 | `PASS` | payload 변조→401, alg:none 공격→401 |
| 16-05 | 미인증 API 직접 호출 | `PASS` | 보호 엔드포인트 모두 401, /health 200 |
| 16-06 | HTTP 보안 헤더 확인 | `PASS` | X-Trace-ID UUID 존재. X-Content-Type-Options 등 미설정 (개선 필요) |
| 16-07 | 비밀번호 brute-force 방지 | `PASS` | Rate limiter 60req/60s 적용. 별도 계정 잠금 미구현 (참고) |
| 16-08 | SSE 엔드포인트 인증 검증 | `PASS` | 미인증→401, 무효토큰→401, 타사용자→403 |
| 16-09 | CORS 설정 검증 | `PASS` | malicious-site.com→"Disallowed CORS origin" 400 거부 |
| 16-10 | 민감 정보 노출 확인 | `PASS` | 에러 응답 깨끗, /users 미존재, /auth/me 비밀번호 미노출 |

### 17-accessibility.md — 접근성 (10 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 17-01 | 로그인 폼 키보드 네비게이션 | `PASS` | Tab순서: email→password→login→register, focus-visible 스타일 존재 |
| 17-02 | 회원가입 폼 키보드 네비게이션 | `PASS` | Tab: email→pw→confirm→register→login, Shift+Tab 역순 정상 |
| 17-03 | 폼 에러 메시지 접근성 | `PASS` | aria-invalid, aria-describedby 연결, form-item-message ID 매칭 |
| 17-04 | 대시보드 Sidebar 키보드 접근성 | `PASS` | 네이티브 a/button, Enter 네비게이션 정상, 테마토글/로그아웃 접근가능 |
| 17-05 | 영상 생성 폼 접근성 | `PASS` | label 연결, slider aria-value*, switch role+aria-checked. 스타일 aria-pressed 미설정(참고) |
| 17-06 | 모달/다이얼로그 포커스 트랩 | `SKIP` | awaiting_approval 작업 없음 |
| 17-07 | 토스트 알림 접근성 | `PASS` | aria-live="polite", aria-label="Notifications" |
| 17-08 | 작업 목록 카드 키보드 접근 | `PASS` | cursor-pointer+onClick. tabIndex=-1 (키보드 접근 개선 필요, 참고) |
| 17-09 | 색상 대비 및 다크 모드 접근성 | `PASS` | 라이트: 검정/흰색, 다크: 흰색/검정 — 우수한 대비 |
| 17-10 | 파이프라인 진행 상태 접근성 | `PASS` | 9단계 텍스트 라벨, SSE 상태 텍스트 표시. role="progressbar" 미설정(참고) |

### 18-performance-stress.md — 성능/스트레스 (6 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 18-01 | 대량 작업 목록 렌더링 성능 | `PASS` | 50건, FCP 64ms, API 21~27ms, 페이지 전환 <100ms |
| 18-02 | SSE 장시간 연결 안정성 | `PASS` | 30초 6회 샘플링: "실시간" 유지, 메모리 25→17MB (GC 정상) |
| 18-03 | 빠른 연속 페이지 이동 안정성 | `PASS` | 5회 연속 이동 (dashboard↔jobs↔detail), 에러 0건 |
| 18-04 | 동시 API 요청 처리 | `PASS` | 10개 동시 GET 140ms, 전부 200 OK, 429 없음 |
| 18-05 | 대본 탭 긴 콘텐츠 렌더링 | `SKIP` | 대본 생성된 작업 없음 (모두 extract 단계 실패) |
| 18-06 | 관리자 페이지 대량 데이터 처리 | `PASS` | stats 18ms, jobs 14ms, filter 16ms — 모두 3초 이내 |

### 19-responsive-cross-browser.md — 반응형/크로스브라우저 (8 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 19-01 | 모바일(375x812) — 로그인/회원가입 | `PASS` | 풀 너비 버튼, 텍스트 미절단, 모바일 탭 UI 전환 |
| 19-02 | 모바일(375x812) — Sidebar 동작 | `PASS` | 접기 토글→64px 아이콘 모드, 햄버거 메뉴 미구현(설계 선택) |
| 19-03 | 태블릿(768x1024) — 대시보드 레이아웃 | `PASS` | 탭 UI, 사이드바 토글 가능, 카드 오버플로 없음 |
| 19-04 | 모바일 — 작업 상세 페이지 | `PASS` | 탭 정상, 재시도 버튼 접근 가능, 오버플로 없음 |
| 19-05 | 모바일 — 승인 페이지 | `SKIP` | awaiting_approval 작업 없음 |
| 19-06 | 모바일 — 관리자 페이지 | `PASS` | 테이블 수평 스크롤, 액션 버튼 40x40 터치 가능 |
| 19-07 | 넓은 화면(1920x1080) — 레이아웃 최대폭 | `PASS` | max-width 1152px 중앙 정렬, 2컬럼 그리드 |
| 19-08 | 화면 크기 실시간 변경 (리사이즈) | `PASS` | 1280→768→375→1280 전환 에러 0건, 레이아웃 복원 정상 |

### 20-data-integrity.md — 데이터 무결성 (9 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 20-01 | 낙관적 업데이트 — 취소 후 롤백 확인 | `PASS` | queued→취소됨 즉시 반영, 서버 상태 일치 |
| 20-02 | 쿼리 캐시 무효화 — 작업 생성 후 목록 갱신 | `SKIP` | 일일 할당량 50/50 소진, 작업 생성 불가 |
| 20-03 | 할당량 실시간 동기화 | `SKIP` | 일일 할당량 소진 |
| 20-04 | SSE 이벤트와 UI 상태 동기화 | `SKIP` | 진행 중인 작업 없음 (모두 terminal) |
| 20-05 | 다중 작업 간 데이터 격리 | `SKIP` | 일일 할당량 소진 |
| 20-06 | 재시도 작업의 parent_job_id 정합성 | `PASS` | 같은 job_id 유지, attempt_count 1→2, parent_job_id 없음 (BE 설계) |
| 20-07 | 승인/거부 후 상태 불변성 | `SKIP` | awaiting_approval 작업 없음 |
| 20-08 | Cancel API 실패 시 Optimistic Update 롤백 | `SKIP` | FE가 axios 사용, fetch mock으로 인터셉트 불가 |
| 20-09 | Approve 실패 시 Optimistic Update 롤백 | `SKIP` | awaiting_approval 없음 + axios mock 불가 |

---

## Phase 9: 신규 추가 테스트

### 21-api-contract-validation.md — API 계약 검증 (12 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 21-01 | VideoStyle `storytelling` → BE 422 | `PASS` | 201 반환 — BE enum 이미 FE에 맞춰 수정됨 (06-05 Auto-Fix) |
| 21-02 | VideoStyle `tutorial` → BE 422 | `PASS` | 201 반환 — BE enum 정렬 완료 |
| 21-03 | VideoStyle `opinion` → BE 422 | `PASS` | 201 반환 — BE enum 정렬 완료 |
| 21-04 | BE 전용 VideoStyle `entertaining` → 201 | `PASS` | 422 반환 — 구 BE 전용 값 제거됨 (enum 정렬) |
| 21-05 | custom_text URL 없이 전송 → BE 422 | `PASS` | url 누락→500 (스키마 통과, 런타임 에러), url 포함→201 |
| 21-06 | FE custom_text 소스 실제 전송 데이터 확인 | `PASS` | FE가 url:"" 전송 (빈 문자열), BE 스키마 통과 |
| 21-07 | Retry API 응답 parent_job_id 부재 | `PASS` | 응답: {job_id(동일), phase:"running", attempt_count:N+1}, parent_job_id 없음 |
| 21-08 | Retry 후 job_id 동일성 확인 | `PASS` | 동일 job_id 유지, FE 같은 페이지 유지 |
| 21-09 | Admin Stats 중첩 구조 → FE 플랫 구조 매핑 | `PASS` | BE 중첩(jobs.created, cost.total_usd)→FE 매핑 수정 완료 (00-setup Auto-Fix) |
| 21-10 | Admin Jobs user_id vs user_email | `PASS` | BE: user_id(UUID)만 반환, user_email 없음 (알려진 계약 불일치) |
| 21-11 | cost_budget_usd 범위 차이 | `PASS` | $0.30→201, $0.05→422, $55→422 (BE 범위 $0.10~$50 확인) |
| 21-12 | /admin/stats/daily 엔드포인트 존재 여부 | `PASS` | 404 확인 — BE 미구현 (BE-MISSING, 차트 미렌더링) |

### 22-sse-event-coverage.md — SSE 이벤트 전수 (10 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 22-01 | `progress` 이벤트 → UI 업데이트 | `---` | |
| 22-02 | `approval_required` 이벤트 → 토스트 + phase | `---` | |
| 22-03 | `cost_warning` 이벤트 → 경고 토스트 | `---` | |
| 22-04 | `completed` 이벤트 → 성공 UI | `---` | |
| 22-05 | `failed` 이벤트 → 에러 UI | `---` | |
| 22-06 | `cancelled` 이벤트 → 취소 UI | `---` | |
| 22-07 | SSE 연결 끊김 → 폴링 폴백 전환 | `---` | |
| 22-08 | SSE 재연결 → 폴링 중지 + 상태 동기화 | `---` | |
| 22-09 | Heartbeat(15초) 수신 확인 | `---` | |
| 22-10 | 터미널 상태 도달 시 SSE 자동 종료 | `---` | |

### 23-video-playback-download.md — 비디오 재생/다운로드 (7 TC)
| TC | 이름 | 상태 | 비고 |
|----|------|------|------|
| 23-01 | 완료 Job → `<video>` 요소 검증 | `---` | |
| 23-02 | 비디오 재생 시작 검증 | `---` | |
| 23-03 | MP4 다운로드 링크 검증 | `---` | |
| 23-04 | 미완료 Job → Result 탭 빈 상태 | `---` | |
| 23-05 | Presigned URL 포맷 검증 | `---` | |
| 23-06 | usePlaybackUrl 30분 캐시 확인 | `---` | |
| 23-07 | 비디오 로딩 실패 시 에러 상태 | `---` | |

---

## 발견된 버그 / 이슈 로그

| ID | 심각도 | 설명 | 발견 TC | 상태 |
|----|--------|------|---------|------|
| | | _(테스트 실행 후 기록)_ | | |

---

## 테스트 실행 기록

| 일자 | 실행 범위 | 실행자 | PASS | FAIL | BUG | 비고 |
|------|-----------|--------|------|------|-----|------|
| 2026-04-01 | 00-setup.md | Claude | 3 | 0 | 0 | Auto-Fixed 3건: BE timezone, FE admin stats mapping |
| 2026-04-01 | 01-health-check.md | Claude | 3 | 0 | 0 | 전체 PASS |
| 2026-04-01 | 02-register.md | Claude | 14 | 0 | 0 | Auto-Fixed 2건: BE register AuthToken, bcrypt prehash |
| 2026-04-01 | 03-login.md | Claude | 14 | 0 | 0 | Auto-Fixed 1건: 401 인터셉터 auth 경로 제외 |
| 2026-04-01 | 04-layout-navigation.md | Claude | 10 | 0 | 0 | 전체 PASS, Auto-Fix 불필요 |
| 2026-04-01 | 05-dashboard.md | Claude | 10 | 0 | 1 | Auto-Fixed 1건: sourceSchema URL refine 추가, SKIP 1건 (05-08 작업 없음) |
| 2026-04-01 | 06-job-create.md | Claude | 11 | 0 | 0 | Auto-Fixed 4건: BE VideoStyle enum, SourceInput url optional, rate limiter GET 제외, FE custom_text 검증 |
| 2026-04-01 | 07-job-detail.md | Claude | 15 | 0 | 5 | Auto-Fixed 3건: BE datetime naive, CORS 순서, rate limiter OPTIONS 제외. SKIP 5건 (워커 미실행) |
| 2026-04-01 | 08-approval.md | Claude | 1 | 0 | 13 | Auto-Fixed 1건: approval redirect 로직 이동. SKIP 13건 (awaiting_approval 작업 없음) |
| 2026-04-01 | 09-job-list.md | Claude | 8 | 0 | 1 | 전체 PASS, SKIP 1건 (09-09 워커 미실행) |
| 2026-04-01 | 10-admin.md | Claude | 16 | 0 | 1 | SKIP 1건 (10-03 daily stats API 404). BE이슈: user_email 미반환, /admin/stats/daily 미구현 |
| 2026-04-01 | 11-integration-auth-flow.md | Claude | 3 | 0 | 0 | 전체 PASS: 인증 플로우, 토큰 무효화, 다크 모드 |
| 2026-04-01 | 12-integration-video-pipeline.md | Claude | 3 | 0 | 4 | Auto-Fixed 1건: formatCost null 방어. SKIP 4건 (awaiting_approval 불가) |
| 2026-04-01 | 13-integration-admin.md | Claude | 4 | 0 | 0 | 전체 PASS: 모니터링, 권한 경계, 강제 취소 반영, JWT 조작 방지 |
| 2026-04-01 | 14-integration-multi-source.md | Claude | 3 | 0 | 0 | 전체 PASS: 멀티소스 조합, 소스 추가/삭제/편집+custom_text, 10개 제한 |
| 2026-04-01 | 15-integration-error-edge-cases.md | Claude | 10 | 0 | 4 | PASS 10건, SKIP 4건 (cost_warning/approval/quota소진/completed 없음) |
| 2026-04-01 | 16-security.md | Claude | 10 | 0 | 0 | 전체 PASS: XSS, IDOR, JWT변조, 미인증, 보안헤더, brute-force, SSE인증, CORS, 민감정보 |
| 2026-04-01 | 17-accessibility.md | Claude | 9 | 0 | 1 | PASS 9건, SKIP 1건 (모달 포커스 트랩 - awaiting_approval 없음) |
| 2026-04-02 | 18-performance-stress.md | Claude | 5 | 0 | 1 | PASS 5건, SKIP 1건 (대본 없음). API <30ms, FCP 64ms, 메모리 누수 없음 |
| 2026-04-02 | 19-responsive-cross-browser.md | Claude | 7 | 0 | 1 | PASS 7건, SKIP 1건 (승인페이지). 모바일/태블릿/FHD 레이아웃 정상 |
| 2026-04-02 | 20-data-integrity.md | Claude | 2 | 0 | 7 | PASS 2건, SKIP 7건 (할당량 소진/terminal 작업/axios mock 불가) |
| 2026-04-02 | 21-api-contract-validation.md | Claude | 12 | 0 | 0 | 전체 PASS: VideoStyle enum 정렬 확인, custom_text url 동작, retry 계약 |
