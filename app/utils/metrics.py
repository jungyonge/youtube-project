"""Prometheus 메트릭 정의."""
from prometheus_client import Counter, Gauge, Histogram

# Counters
video_jobs_total = Counter(
    "video_jobs_total",
    "Total number of video jobs by status",
    ["status"],
)

api_call_cost_usd = Counter(
    "api_call_cost_usd",
    "Cumulative API call cost in USD by provider",
    ["provider"],
)

# Histograms
video_job_duration_seconds = Histogram(
    "video_job_duration_seconds",
    "Total video job duration from creation to completion",
    buckets=[60, 120, 300, 600, 900, 1200, 1800],
)

api_call_duration_seconds = Histogram(
    "api_call_duration_seconds",
    "External API call duration in seconds",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)

# Gauges
active_celery_tasks = Gauge(
    "active_celery_tasks",
    "Number of currently running Celery tasks",
)

storage_usage_bytes = Gauge(
    "storage_usage_bytes",
    "Storage usage in bytes by bucket",
    ["bucket"],
)
