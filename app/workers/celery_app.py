from celery import Celery

from app.config import settings

celery_app = Celery(
    "video_pipeline",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.pipeline.steps.step5_assemble.*": {"queue": "sync"},
    },
)

celery_app.autodiscover_tasks(["app.pipeline.steps"])
