# Phase 9: 테스트

## 목표
전체 파이프라인의 단위/통합 테스트를 작성하고, 프로젝트 문서를 마무리한다.

---

## 구현 항목

### 48. conftest.py (DB, Redis, MinIO fixture)

**파일**: `tests/conftest.py`
- DB fixture (테스트용 PostgreSQL)
- Redis fixture (테스트용 Redis)
- MinIO mock fixture
- 테스트 사용자/JWT fixture

### 49. 각 step 정상 경로 테스트

- `test_extract.py`: 콘텐츠 추출 정상 동작
- `test_normalize.py`: 소스 정규화 + 중복 제거
- `test_evidence_pack.py`: 청킹 + 랭킹 + 근거팩 생성

### 50. 외부 API step 4종 테스트

각 외부 API step에 대해:
- **success**: 정상 응답 처리
- **retry**: 일시적 실패 후 재시도 성공
- **fallback**: 대체 전략 동작
- **final failure**: 최종 실패 처리

대상: `test_gemini.py`, `test_openai.py`

### 51. render step 통합 테스트

**파일**: `test_render.py`
- 짧은 스크립트 (3씬)
- 긴 스크립트 (18씬)
- 일부 asset 실패 (fallback 적용)

### 52. idempotency 테스트

**파일**: `test_idempotency.py`
- 동일 idempotency_key 중복 요청 차단 확인
- 다른 key는 별도 처리 확인

### 53. cancel / resume / retry from step 테스트

- 작업 취소 후 상태 확인
- 특정 step부터 재실행 후 산출물 재사용 확인
- resume 후 정상 완료 확인

### 54. cost budget exceeded 테스트

**파일**: `test_cost_guardrail.py`
- 예산 초과 시 자동 Degrade 4단계 동작 확인
- 최종 초과 시 job 실패 처리 확인

### 55. policy review 테스트

**파일**: `test_policy_review.py`
- 주식 관련 대본 → 투자 disclaimer 삽입 확인
- 정치 관련 대본 → 균형 관점 추가 확인
- 의료 관련 대본 → 전문가 상담 disclaimer 확인

### 56. README.md 작성

- 프로젝트 소개
- 설치 및 실행 방법
- API 문서 링크
- 환경 변수 설명

---

## 중요 제약사항 (전체 프로젝트)

1. **Python 3.11+ 문법** (match-case, type hints, | None 구문)
2. **API 계층은 async(asyncpg)**, Celery Worker는 **sync(psycopg2)** — 절대 혼용 금지
3. **Celery task 안에서 AsyncSession import 금지** — sync_session.py만 사용
4. 각 Step은 독립적으로 테스트 가능 (의존성 주입)
5. 중간 결과물은 S3에 저장하여 재시작/재실행 가능
6. 비용 추적: 모든 AI API 호출 시 CostLog 기록 + cost_budget 체크
7. 한국어 최적화: TTS, 자막, 나레이션
8. Rate Limiting: asyncio.Semaphore + 사용자별 quota
9. 구조화 로그: loguru + trace_id + job_id
10. 타입 힌트: 전체 함수, mypy strict
11. 외부 API 호출은 반드시 retry.py 데코레이터
12. Docker: API(경량) / Worker-default(경량 task) / Worker-render(영상 전용, concurrency=1) 분리
13. 로컬 파일시스템은 temp 전용, 영속 데이터는 Postgres + S3
14. 정치/주식/시사는 별도 policy review, fact/inference/opinion 명시 구분
15. 모든 다운로드 URL은 presigned URL (인증된 사용자만 접근)
16. **Celery 브로커 visibility_timeout = 14400초(4시간)** — 렌더링 중복 실행 방지
17. **Step 5는 render 큐 전용** — assemble_task.s().set(queue='render')
18. **Step 5 FFmpeg 진행률을 10초마다 Redis PUBLISH** — 프론트 멈춤 방지
19. **영상 완성 후 중간 산출물(tts, image) S3 즉시 삭제** — 스토리지 비용 최적화
20. **requirements.txt에 psycopg2-binary 포함** — Celery Worker용 동기 DB 드라이버

---

## 선행 조건
- Phase 8 완료 (전체 서비스 동작)

## 완료 기준
- [ ] conftest.py fixture 설정 완료
- [ ] 각 step 정상 경로 테스트 통과
- [ ] 외부 API 4종 테스트 (success/retry/fallback/failure) 통과
- [ ] render 통합 테스트 3종 통과
- [ ] idempotency 테스트 통과
- [ ] cancel/resume/retry 테스트 통과
- [ ] cost budget exceeded 테스트 통과
- [ ] policy review 테스트 (주식/정치/의료) 통과
- [ ] README.md 작성 완료
