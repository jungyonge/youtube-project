# Phase 7: 오케스트레이션 + 인프라

## 목표
Celery task 체인 오케스트레이션, Job 생명주기 관리(취소/재시도/승인),
SSE 실시간 상태 스트리밍, 주기적 정리 작업을 구현한다.

---

## 구현 항목

### 39. orchestrator.py (Celery task 체인 + 큐 라우팅)

**파일**: `app/pipeline/orchestrator.py`

```python
"""
Celery task 체인으로 파이프라인을 구성한다.
하나의 거대한 async orchestrator가 아니라, step 단위로 task를 분리.

큐 라우팅:
  - default 큐: extract, normalize, evidence_pack, research, review,
                policy_review, human_gate, tts, images, subtitles, bgm,
                render_manifest
  - render 큐: assemble (Step 5만 전용 큐)

  체인 내 라우팅 예시:
    extract_task.s(job_id)
    | normalize_task.s()
    | evidence_pack_task.s()
    | research_task.s()
    | review_task.s()
    | policy_review_task.s()
    | human_gate_task.s()
    | asset_generation_group       # group()으로 4a,4b,4d 병렬
    | subtitle_task.s()
    | render_manifest_task.s()
    | assemble_task.s().set(queue='render')  # render 큐로 라우팅

각 task는:
1. 시작 시 JobStepExecution 레코드 생성 (status=running)
2. 완료 시 status=completed, 산출물 S3 업로드, Asset 등록
3. 실패 시 status=failed, error 기록
4. Redis PUBLISH로 SSE 상태 전송
5. job.is_cancelled 체크 → True면 즉시 중단
6. DB 접근 시 반드시 sync_session 사용 (Celery 내 async 금지)

비동기/동기 분리:
- API 계층: async (FastAPI + asyncpg)
- Celery task 내 AI API 호출: sync 래퍼 사용
  (openai, google-genai SDK 자체가 sync이므로 그대로 사용 가능)
  (async SDK 사용 시 asgiref.sync.async_to_sync 래퍼 필수)
- 렌더/FFmpeg/MoviePy: sync worker task (render 큐, concurrency=1)

Cost Guardrail:
- 각 AI API 호출 후 cost_tracker로 비용 기록
- 누적 비용이 cost_budget_usd 초과 시:
  1. 이미지 생성 → priority 낮은 씬부터 placeholder로 대체
  2. 고가 모델 → flash 모델로 자동 다운그레이드
  3. 그래도 초과 → 나머지 이미지 전부 text_overlay로 대체
  4. 최종 초과 → job 실패 처리 + 사용자에게 예산 부족 알림
"""
```

### 40. celery_app.py

**파일**: `app/workers/celery_app.py`

```python
"""
celery_app.py 필수 설정:

# 브로커 타임아웃 (치명적 중복 렌더링 방지)
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
"""
```

### 41. periodic_tasks.py

**파일**: `app/workers/periodic_tasks.py`
- 파일 정리 (TTL 만료 산출물 삭제)
- API 헬스체크
- stale job 정리 (오래 걸리는 job 감지)

### 42. stream.py (SSE)

**파일**: `app/api/routes/stream.py`

```python
"""
GET /api/v1/videos/{job_id}/stream

인증 필요: JWT Bearer token (해당 job의 소유자만 구독 가능)

이벤트 타입:
- progress: { phase, progress_percent, current_step_detail, cost_usd }
- approval_required: { script_preview_url, sensitivity_level }
- cost_warning: { current_cost, budget, message }
- completed: { download_url, thumbnail_url, duration_sec, total_cost }
- failed: { error_message, last_completed_step, can_retry }
- cancelled: {}

구현: Redis Pub/Sub → sse-starlette EventSourceResponse
fallback: GET /api/v1/videos/{job_id} polling (SSE 미지원 클라이언트)
"""
```

### 43. cancel/retry API 라우트

**작업 취소 (Cancel)**:
```python
"""
POST /api/v1/videos/{job_id}/cancel

1. job.is_cancelled = True (DB 업데이트)
2. 현재 실행 중인 Celery task revoke
3. 이미 생성된 asset은 유지 (24시간 TTL 후 자동 삭제)
4. SSE로 "cancelled" 이벤트 전송
5. 진행 중이던 step의 JobStepExecution.status = "cancelled"
"""
```

**특정 Step부터 재실행 (Retry from Step)**:
```python
"""
POST /api/v1/videos/{job_id}/retry?from_step=review

1. job.last_completed_step 확인
2. 해당 step 이후의 JobStepExecution 레코드 초기화
3. 해당 step 이후의 Asset 삭제 (S3 + DB)
4. attempt_count 증가
5. 해당 step부터 Celery 체인 재시작
6. 이전 step의 산출물은 재사용 (S3에서 다시 다운로드)

사용 사례:
- policy_review에서 수정 후 다시 asset 생성
- 이미지 품질이 마음에 안 들어서 step4b만 재실행
"""
```

**Human Approval**:
```python
"""
POST /api/v1/videos/{job_id}/approve
POST /api/v1/videos/{job_id}/reject

approve:
1. job.human_approved = True
2. 대기 중이던 파이프라인 재개 (Celery task 트리거)

reject:
1. job.human_approved = False
2. job.phase = "rejected"
3. 사용자에게 대본 수정 후 재요청 안내
"""
```

### 44. admin 라우트

**파일**: `app/api/routes/admin.py`
- `GET /admin/jobs` (전체 job 목록, 필터링)
- `POST /admin/jobs/{job_id}/force-cancel` (강제 취소)
- `GET /admin/stats` (일일 생성수, 비용 합계, 실패율)

---

## 선행 조건
- Phase 6 완료 (영상 조립 가능)

## 완료 기준
- [ ] Celery task 체인 오케스트레이션 동작
- [ ] default/render 큐 라우팅 동작
- [ ] celery_app.py 필수 설정 (visibility_timeout, prefetch) 적용
- [ ] periodic_tasks (TTL 정리, stale job) 동작
- [ ] SSE 실시간 상태 스트리밍 동작
- [ ] 6종 이벤트 타입 (progress, approval_required, cost_warning, completed, failed, cancelled) 전송
- [ ] cancel API 동작 (Celery revoke + DB + SSE)
- [ ] retry from step API 동작 (산출물 재사용 + 체인 재시작)
- [ ] admin 라우트 동작 (jobs, force-cancel, stats)
