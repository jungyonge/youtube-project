# Phase 8: Observability + 마무리

## 목표
Prometheus 메트릭, 구조화 로그, 관리자 통계 API를 구현하여
서비스의 관측 가능성을 확보한다.

---

## 구현 항목

### 45. prometheus 메트릭 엔드포인트

**파일**: `app/api/routes/health.py` (메트릭 추가)

```python
"""
prometheus 메트릭:
- video_jobs_total (counter, labels: status)
- video_job_duration_seconds (histogram)
- api_call_duration_seconds (histogram, labels: provider, model)
- api_call_cost_usd (counter, labels: provider)
- active_celery_tasks (gauge)
- storage_usage_bytes (gauge, labels: bucket)
"""
```

엔드포인트: `GET /metrics` (Prometheus 메트릭)

### 46. 구조화 로그 설정

```python
"""
모든 로그에 아래 컨텍스트 포함:
- trace_id: 요청별 고유 ID (middleware에서 주입)
- job_id: 파이프라인 작업 ID
- step_name: 현재 실행 중인 step
- user_id: 요청 사용자

loguru 포맷:
  {time} | {level} | trace={trace_id} job={job_id} step={step_name} | {message}
"""
```

### 47. admin 통계 API

- `GET /admin/stats` (일일 생성수, 비용 합계, 실패율)
- 대시보드 데이터 제공

---

## 선행 조건
- Phase 7 완료 (전체 파이프라인 동작)

## 완료 기준
- [ ] Prometheus 메트릭 6종 수집 동작
- [ ] `GET /metrics` 엔드포인트 동작
- [ ] 구조화 로그 (trace_id, job_id, step_name, user_id) 포함
- [ ] loguru 포맷 적용
- [ ] admin 통계 API 동작
