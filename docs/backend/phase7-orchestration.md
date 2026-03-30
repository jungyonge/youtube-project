# Phase 7: 오케스트레이션 + 인프라

## 목표
Celery task 체인으로 전체 파이프라인을 오케스트레이션하고,
SSE 실시간 상태 스트리밍, 작업 취소/재시도, 관리자 API를 구현한다.

---

## 구현 항목

### 39. orchestrator.py (Celery task 체인)

**파일**: `app/pipeline/orchestrator.py`

```python
"""
파이프라인 전체를 Celery task 체인으로 구성.

체인 구조:
  extract_task.s(job_id)
  | normalize_task.s()
  | evidence_pack_task.s()
  | research_task.s()
  | review_task.s()
  | policy_review_task.s()
  | human_gate_task.s()          # 필요시 여기서 중단
  | asset_generation_group       # group()으로 4a, 4b, 4d 병렬
  | subtitle_task.s()            # 4c는 TTS 완료 후
  | render_manifest_task.s()     # 렌더 지시서 생성
  | assemble_task.s()            # sync worker에서 실행

def start_pipeline(job_id: str) -> AsyncResult:
    전체 체인 시작.

def resume_pipeline(job_id: str, from_step: str) -> AsyncResult:
    특정 step부터 재개 (human gate 승인 후, retry from step).
    - from_step 이전 산출물은 S3에서 재사용
    - from_step부터 새 체인 구성

각 task 공통 동작:
1. 시작 시 JobStepExecution 생성 (status="running")
2. 완료 시 status="completed", 산출물 S3 업로드, Asset 등록
3. 실패 시 status="failed", error_message + error_traceback 기록
4. Redis PUBLISH로 SSE 진행 상태 전송
5. job.is_cancelled 체크 → True면 즉시 중단 (CancelledError)

비동기/동기 분리:
- 네트워크 I/O (AI API, S3): async 가능 task
  (openai, google-genai SDK 자체가 sync이므로 그대로 사용 가능)
  (async SDK 사용 시 asgiref.sync.async_to_sync 래퍼 필수)
- 렌더/FFmpeg/MoviePy: sync worker task (CPU 바운드)
  → task_routes로 render 큐에 라우팅

⚠️ DB 접근 규칙:
- **모든 Celery task에서 반드시 sync_session.py의 SyncSession 사용**
- 절대로 Celery task 안에서 AsyncSession을 import하지 말 것
- Event Loop 충돌/Deadlock 발생 원인

Cost Guardrail 통합:
- 각 AI API 호출 후 cost_tracker.record_cost()
- degrade_level에 따라 자동 조정
"""
```

### 40. celery_app.py

**파일**: `app/workers/celery_app.py`

```python
"""
Celery 앱 설정.

기본 설정:
- broker: Redis (settings.REDIS_URL)
- result_backend: Redis
- task_serializer: json
- result_serializer: json
- accept_content: ["json"]
- task_track_started: True
- task_acks_late: True (장애 복구)

⚠️ 필수 설정 (치명적 중복 렌더링 방지):

# 브로커 타임아웃
# 15분 영상 렌더링에 10~20분 소요.
# 기본 visibility_timeout(1시간)이 지나면 Redis가
# "워커가 죽었다"고 판단하여 다른 워커에 작업을 재할당한다.
# → 동일 영상을 2번 렌더링 = 비용/자원 2배 폭발
# 따라서 넉넉하게 4시간(14400초)으로 설정.
broker_transport_options = {
    'visibility_timeout': 14400,  # 4시간
}

# 큐 라우팅
task_routes = {
    'app.pipeline.steps.step5_assemble.*': {'queue': 'render'},
    # 나머지는 default 큐 자동
}

# 렌더 큐 prefetch 제한 (한 번에 1개만 가져옴)
worker_prefetch_multiplier = 1  # render worker용

# Task 결과 만료 (24시간)
result_expires = 86400

# 직렬화
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']

Task autodiscover:
- app.pipeline.steps 패키지의 모든 task 자동 발견
"""
```

### 41. periodic_tasks.py

**파일**: `app/workers/periodic_tasks.py`

```python
"""
Celery Beat 주기적 작업.

1. cleanup_expired_assets (매 1시간)
   - OUTPUT_TTL_HOURS 초과 산출물 S3 삭제 + DB 삭제
   - FAILED_TEMP_TTL_HOURS 초과 실패 job 산출물 삭제

2. cleanup_stale_jobs (매 30분)
   - 24시간 이상 "running" 상태인 job → "failed"로 전환
   - 24시간 이상 "awaiting_approval" → 자동 취소

3. api_health_check (매 5분)
   - Gemini API 키 유효성 체크
   - OpenAI API 키 유효성 체크
   - 실패 시 loguru warning + Prometheus 메트릭 갱신

4. storage_usage_report (매 1시간)
   - MinIO 버킷별 사용량 조회
   - Prometheus storage_usage_bytes 메트릭 갱신
"""
```

### 42. stream.py (SSE 실시간 상태)

**파일**: `app/api/routes/stream.py`

```python
"""
GET /api/v1/videos/{job_id}/stream

Auth: Bearer JWT (해당 job의 소유자만 구독 가능)

SSE 토큰 처리 (중요):
  EventSource API는 커스텀 헤더를 지원하지 않으므로,
  SSE 엔드포인트는 쿼리 파라미터로도 JWT를 받을 수 있어야 한다.

  GET /api/v1/videos/{job_id}/stream?token={jwt}

  stream.py에서:
  1. Authorization 헤더에서 토큰 추출 시도
  2. 없으면 query parameter 'token'에서 추출
  3. 둘 다 없으면 401 반환

구현: Redis Pub/Sub → sse-starlette EventSourceResponse

이벤트 타입:
- progress:
  { phase, progress_percent, current_step_detail, cost_usd }
- approval_required:
  { script_preview_url, sensitivity_level }
- cost_warning:
  { current_cost, budget, message }
- completed:
  { download_url, thumbnail_url, duration_sec, total_cost }
- failed:
  { error_message, last_completed_step, can_retry }
- cancelled: {}

Redis 채널: video_job:{job_id}

SSE 발행 (pipeline step에서):
async def publish_progress(job_id, event_type, data):
    Redis PUBLISH video_job:{job_id} {event_type}:{json_data}

Heartbeat: 15초마다 ping 전송 (연결 유지)
Timeout: 클라이언트 연결 30분 후 자동 종료

Fallback: SSE 미지원 클라이언트 → GET /api/v1/videos/{job_id} polling
"""
```

### 43. Cancel/Retry API 라우트

**파일**: `app/api/routes/video.py`에 추가

```
POST /api/v1/videos/{job_id}/cancel
  Auth: 소유자
  Flow:
    1. job.is_cancelled = True (DB)
    2. 현재 Celery task revoke (SIGTERM)
    3. 실행 중 step → JobStepExecution.status = "cancelled"
    4. 생성된 asset 유지 (TTL 후 자동 삭제)
    5. SSE "cancelled" 이벤트
    6. Response: { job_id, phase: "cancelled" }

POST /api/v1/videos/{job_id}/retry
  Auth: 소유자
  Query: from_step (optional)
  Flow:
    1. job.last_completed_step 확인
    2. from_step 이후 JobStepExecution 초기화
    3. from_step 이후 Asset 삭제 (S3 + DB)
    4. attempt_count 증가
    5. max_attempts 초과 체크 (초과 시 403)
    6. resume_pipeline(job_id, from_step) 호출
    7. Response: { job_id, phase: "running", attempt_count }

GET /api/v1/videos/{job_id}/download
  Auth: 소유자
  Flow:
    1. job.phase == "completed" 확인
    2. output_video_key로 presigned URL 생성
    3. 302 Redirect → presigned URL

GET /api/v1/videos/{job_id}/script
  Auth: 소유자
  Flow:
    1. output_script_key로 presigned URL 생성
    2. 302 Redirect → presigned URL (또는 JSON 직접 반환)
```

### 44. Admin 라우트

**파일**: `app/api/routes/admin.py`

```
GET /admin/jobs
  Auth: require_admin
  Query: page, per_page, status, user_id, date_from, date_to
  Response: { items: [JobStatusResponse], total, page, per_page }

POST /admin/jobs/{job_id}/force-cancel
  Auth: require_admin
  Flow: cancel과 동일 + 소유자 제한 없음

GET /admin/stats
  Auth: require_admin
  Response:
    {
      daily_jobs_created: int,
      daily_jobs_completed: int,
      daily_jobs_failed: int,
      daily_total_cost_usd: float,
      failure_rate: float,
      avg_generation_time_sec: float,
      active_jobs: int
    }
```

---

## 선행 조건
- Phase 1~6 완료 (모든 pipeline step 구현)
- Redis 실행 중 (Celery broker + PubSub)

## 완료 기준
- [ ] Celery task 체인 — 전체 파이프라인 순차 실행
- [ ] asset_generation 병렬 실행 (TTS + 이미지 + BGM)
- [ ] SSE — 실시간 진행 상태 수신 가능
- [ ] 작업 취소 — Celery task revoke + DB 상태 갱신
- [ ] 특정 step 재시도 — from_step부터 체인 재개
- [ ] Human gate 승인 후 파이프라인 자동 재개
- [ ] Admin — 전체 job 목록, 강제 취소, 통계 조회
- [ ] Periodic tasks — 만료 산출물 정리, stale job 처리
