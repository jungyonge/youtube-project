# Phase 8: Observability + 마무리

## 목표
Prometheus 메트릭, 구조화 로그(loguru + trace_id), 관리자 통계 API를 구현하여
서비스 운영 가시성을 확보한다.

---

## 구현 항목

### 45. Prometheus 메트릭 엔드포인트

**파일**: `app/api/routes/health.py`에 추가 (또는 별도 metrics.py)

```
GET /metrics
  - prometheus_client의 generate_latest() 사용
  - Content-Type: text/plain; version=0.0.4

메트릭 정의 (app/utils/metrics.py 또는 적절한 위치):

Counter:
  video_jobs_total{status}
    - status: queued, running, completed, failed, cancelled
    - 각 상태 전환 시 increment

  api_call_cost_usd{provider}
    - provider: gemini, openai_chat, openai_tts, openai_dalle
    - cost_tracker에서 비용 기록 시 increment

Histogram:
  video_job_duration_seconds
    - 전체 job 소요 시간 (created_at → completed_at)
    - buckets: 60, 120, 300, 600, 900, 1200, 1800

  api_call_duration_seconds{provider, model}
    - 외부 API 호출 소요 시간
    - buckets: 0.1, 0.5, 1, 2, 5, 10, 30

Gauge:
  active_celery_tasks
    - 현재 실행 중인 Celery task 수
    - task 시작 시 inc(), 종료 시 dec()

  storage_usage_bytes{bucket}
    - MinIO 버킷별 사용량
    - periodic task에서 주기적 갱신
```

### 46. 구조화 로그 설정

**파일**: `app/utils/logging.py` (또는 main.py에서 설정)

```python
"""
loguru 기반 구조화 로그.

모든 로그에 아래 컨텍스트 자동 포함:
- trace_id: 요청별 고유 ID (middleware에서 주입)
- job_id: 파이프라인 작업 ID
- step_name: 현재 실행 중인 step
- user_id: 요청 사용자

로그 포맷:
  {time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | trace={extra[trace_id]} job={extra[job_id]} step={extra[step_name]} | {message}

설정:
- LOG_LEVEL에 따른 레벨 설정 (settings.LOG_LEVEL)
- stdout 출력 (Docker 로그 수집 호환)
- JSON 포맷 옵션 (프로덕션 환경)
- 파일 로테이션 옵션 (로컬 개발)

ContextVar 연동:
- trace middleware에서 trace_id 설정
- pipeline step에서 job_id, step_name 설정
- loguru.bind()로 컨텍스트 자동 주입

사용 예시:
  from loguru import logger
  logger.bind(job_id=job_id, step_name="extract").info("Starting extraction")

에러 로그:
- exception=True 옵션으로 traceback 자동 포함
- 외부 API 에러 시 response body 포함
"""
```

### 47. Admin 통계 API

**파일**: `app/api/routes/admin.py`에 추가

```
GET /admin/stats
  Auth: require_admin
  Query: date (optional, 기본 오늘)
  Response:
  {
    "date": "2026-03-30",
    "jobs": {
      "created": 42,
      "completed": 38,
      "failed": 3,
      "cancelled": 1,
      "active": 2
    },
    "cost": {
      "total_usd": 31.56,
      "by_provider": {
        "gemini": 2.10,
        "openai_chat": 1.14,
        "openai_tts": 3.04,
        "openai_dalle": 25.28
      }
    },
    "performance": {
      "avg_generation_time_sec": 342.5,
      "median_generation_time_sec": 298.0,
      "failure_rate": 0.071
    },
    "storage": {
      "assets_bucket_bytes": 5368709120,
      "outputs_bucket_bytes": 2147483648
    }
  }

구현:
- VideoJob 테이블 집계 (날짜별)
- CostLog 테이블 집계 (provider별)
- 성능 통계 (generation_time_sec)
- S3 사용량 (periodic task에서 캐시된 값)
"""
```

---

## 선행 조건
- Phase 7 완료 (Celery, SSE, Admin 라우트 기본 구조)
- prometheus-client 설치
- loguru 설치

## 완료 기준
- [ ] `GET /metrics` — Prometheus 스크래핑 가능한 메트릭 엔드포인트
- [ ] video_jobs_total — 상태별 카운터 정상 증가
- [ ] api_call_duration_seconds — API 호출 시간 히스토그램
- [ ] 모든 로그에 trace_id, job_id, step_name 포함
- [ ] 에러 로그에 traceback 자동 포함
- [ ] `GET /admin/stats` — 일별 통계 조회 (job 수, 비용, 성능, 스토리지)
