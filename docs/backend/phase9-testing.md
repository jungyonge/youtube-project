# Phase 9: 테스트

## 목표
전체 파이프라인의 정상 경로, 에러 처리, 재시도, 멱등성, 비용 제한, 정책 검수 등을
종합적으로 테스트하여 프로덕션 안정성을 확보한다.

---

## 구현 항목

### 48. conftest.py (테스트 인프라)

**파일**: `tests/conftest.py`

```python
"""
pytest fixture 모음.

DB Fixture:
- async_engine: 테스트용 PostgreSQL (또는 SQLite async)
- async_session: 트랜잭션 격리 세션 (테스트 후 rollback)
- sync_session: Celery task 테스트용 동기 세션 (psycopg2)
- create_tables: 테스트 시작 시 테이블 생성

Redis Fixture:
- redis_client: fakeredis 또는 테스트 Redis 인스턴스
- 각 테스트 후 flush

MinIO/S3 Fixture:
- mock_object_store: moto 또는 mock 기반 S3 모킹
- 테스트용 버킷 자동 생성

API Fixture:
- client: httpx.AsyncClient (FastAPI TestClient)
- auth_headers: 테스트 유저 JWT 포함 헤더
- admin_headers: 관리자 JWT 포함 헤더

Factory Fixture:
- create_user(email, password, role)
- create_job(user, topic, sources)
- create_evidence_pack(topic, chunks)
- create_full_script(scenes_count)

External API Mock:
- mock_gemini: GeminiClient mock (generate, generate_json)
- mock_openai: OpenAIClient mock (chat, tts, generate_image)
"""
```

### 49. 각 Step 정상 경로 테스트

**파일**: `tests/test_extract.py`
```python
"""
- test_extract_blog_url: 블로그 URL → 본문 추출 성공
- test_extract_news_url: 뉴스 URL → 본문 추출 성공
- test_extract_youtube_url: YouTube → 자막 추출 성공
- test_extract_partial_failure: 3개 중 1개 실패 → 나머지 2개 성공, 실패 소스 skip
- test_extract_all_failure: 모든 URL 실패 → step failed
"""
```

**파일**: `tests/test_normalize.py`
```python
"""
- test_canonical_url: UTM 파라미터 제거, www 통일
- test_duplicate_detection: 같은 기사 재배포 → is_duplicate=True
- test_reliability_scoring: 주요 언론사 0.9, 블로그 0.5
- test_ad_filter: 광고성 콘텐츠 warning flag
"""
```

**파일**: `tests/test_evidence_pack.py`
```python
"""
- test_chunking_blog: 블로그 문단 단위 청킹 (300~500자)
- test_chunking_youtube: YouTube 타임스탬프 구간 청킹
- test_ranking: TF-IDF + recency + reliability 종합 점수
- test_top_n_selection: 상위 30개 청크 선택
- test_key_claims_extraction: Gemini Flash로 핵심 주장 요약
"""
```

### 50. 외부 API Step 4종 테스트

**파일**: `tests/test_gemini.py`
```python
"""
각 Gemini 호출 step에 대해:
- test_success: 정상 응답 → FullScript 파싱 성공
- test_retry: 첫 호출 실패 → 재시도 → 성공
- test_fallback: Pro 실패 → Flash로 자동 다운그레이드
- test_final_failure: 3회 재시도 모두 실패 → step failed + 에러 기록
"""
```

**파일**: `tests/test_openai.py`
```python
"""
ChatGPT, TTS, DALL-E 각각에 대해:
- test_chat_success: 검수 정상 완료
- test_chat_retry: rate limit → 재시도 → 성공
- test_tts_success: TTS 오디오 생성 성공
- test_tts_failure: TTS 실패 → 무음 placeholder
- test_dalle_success: 이미지 생성 성공
- test_dalle_fallback: DALL-E 실패 → text_overlay fallback
- test_dalle_final_failure: 3회 실패 → placeholder 이미지
"""
```

### 51. Render Step 통합 테스트

**파일**: `tests/test_render.py`
```python
"""
- test_short_script: 5씬 짧은 대본 → 3분 영상 조립 성공
- test_long_script: 20씬 긴 대본 → 12분 영상 조립 성공
- test_partial_asset_failure: 일부 이미지 fallback → 영상 완성 (is_fallback 포함)
- test_ken_burns_rotation: 4가지 효과 순환 적용 확인
- test_subtitle_burn: SRT 자막 burn-in 포함 확인
- test_bgm_mixing: BGM 볼륨 -20dB 믹싱 확인
- test_temp_cleanup: 조립 후 로컬 temp 파일 삭제 확인
- test_ffmpeg_progress: FFmpeg 진행률 Redis PUBLISH 확인
- test_intermediate_cleanup: 완성 후 중간 산출물(tts, image) S3 삭제 + is_deleted 플래그

FFmpeg/MoviePy Mock:
- MoviePy의 VideoClip/AudioClip을 mock하여 빠른 테스트
- FFmpeg subprocess를 mock하여 진행률 콜백 테스트
- 짧은 테스트 영상(1~3초)으로 실제 인코딩 통합 테스트
"""
```

### 52. Idempotency 테스트

**파일**: `tests/test_idempotency.py`
```python
"""
- test_same_key_returns_existing: 같은 idempotency_key → 기존 job_id 반환
- test_different_key_creates_new: 다른 key → 새 job 생성
- test_no_key_always_creates: key 미지정 → 매번 새 job
- test_key_expired: TTL 만료 후 같은 key → 새 job 생성
- test_concurrent_same_key: 동시 요청 → 하나만 생성 (race condition)
"""
```

### 53. Cancel / Resume / Retry from Step 테스트

**파일**: `tests/test_pipeline.py`
```python
"""
Cancel:
- test_cancel_running_job: 실행 중 취소 → is_cancelled=True, Celery revoke
- test_cancel_queued_job: 대기 중 취소 → 즉시 cancelled
- test_cancel_completed_job: 완료된 job 취소 → 400 에러

Resume (Human Gate):
- test_approve_resumes_pipeline: 승인 → asset_generation부터 재개
- test_reject_stops_pipeline: 거부 → phase="rejected"
- test_auto_cancel_timeout: 24시간 미승인 → 자동 취소

Retry:
- test_retry_from_step: review에서 재시도 → review부터 재실행
- test_retry_reuses_previous_assets: 이전 step 산출물 재사용
- test_retry_cleans_subsequent_assets: 이후 step 산출물 삭제
- test_retry_max_attempts: max_attempts 초과 → 403 에러
"""
```

### 54. Cost Budget 테스트

**파일**: `tests/test_cost_guardrail.py`
```python
"""
- test_normal_budget: 예산 내 정상 완료
- test_degrade_level_1: 80% 초과 → DALL-E 이미지 50% 감소
- test_degrade_level_2: 90% 초과 → Gemini Flash 다운그레이드
- test_degrade_level_3: 95% 초과 → 모든 이미지 text_overlay
- test_degrade_level_4: 100% 초과 → job 실패 + 사용자 알림
- test_cost_logging: 모든 API 호출 → CostLog 레코드 생성
- test_budget_check_before_api_call: 호출 전 잔여 예산 확인
- test_sse_cost_warning: 예산 80% 시 SSE cost_warning 이벤트
"""
```

### 55. Policy Review 테스트

**파일**: `tests/test_policy_review.py`
```python
"""
주식:
- test_stock_prediction_softened: "반드시 오른다" → "가능성이 있습니다"
- test_stock_disclaimer_added: 투자 면책 disclaimer 씬 자동 삽입

정치:
- test_political_balance: 일방적 지지 → 반대 관점 추가
- test_defamation_removed: 명예훼손 소지 표현 제거

의료:
- test_medical_disclaimer: "~하면 낫는다" → "전문가 상담" disclaimer
- test_medical_advice_flagged: 의료 조언 policy_flag 설정

공통:
- test_sensitivity_upgrade: policy_flags 기반 sensitivity 재판정
- test_no_flags_skip: policy_flags 없으면 skip (pass-through)
- test_fact_opinion_labeling: claim_type별 나레이션 표현 확인
"""
```

### 56. README.md 작성

**파일**: `README.md`

```
# AI Video Generation Service

## 개요
- 서비스 설명
- 아키텍처 다이어그램 (텍스트)

## Quick Start
- Docker Compose로 전체 실행
- 환경변수 설정 (.env)

## API 문서
- 인증 (register, login)
- 영상 생성/조회/스트림
- 관리자 API
- Swagger UI: /docs

## 기술 스택
- 요약

## 개발 가이드
- 로컬 개발 환경 설정
- 테스트 실행
- Alembic 마이그레이션
```

---

## 선행 조건
- Phase 1~8 모두 완료
- 테스트 의존성: pytest, pytest-asyncio, httpx, fakeredis, moto

## 완료 기준
- [ ] `conftest.py` — DB, Redis, S3 fixture 동작
- [ ] 각 step 정상 경로 테스트 통과
- [ ] 외부 API 4종 테스트 (success/retry/fallback/failure) 통과
- [ ] 렌더 통합 테스트 3종 통과
- [ ] 멱등성 테스트 통과 (race condition 포함)
- [ ] cancel/resume/retry 테스트 통과
- [ ] 비용 예산 테스트 통과 (4단계 degradation)
- [ ] 정책 검수 테스트 통과 (주식/정치/의료)
- [ ] README.md 작성 완료
- [ ] 전체 테스트 스위트 `pytest` 통과
