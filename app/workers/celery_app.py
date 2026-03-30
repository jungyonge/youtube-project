from celery import Celery

from app.config import settings

celery_app = Celery(
    "video_pipeline",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    # 직렬화
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # 장애 복구
    task_track_started=True,
    task_acks_late=True,

    # 렌더 큐 prefetch 제한 (한 번에 1개만 가져옴)
    worker_prefetch_multiplier=1,

    # 브로커 타임아웃 (치명적 중복 렌더링 방지)
    # 15분 영상 렌더링에 10~20분 소요.
    # 기본 visibility_timeout(1시간)이 지나면 Redis가
    # "워커가 죽었다"고 판단하여 다른 워커에 작업을 재할당한다.
    # → 동일 영상을 2번 렌더링 = 비용/자원 2배 폭발
    # 따라서 넉넉하게 4시간(14400초)으로 설정.
    broker_transport_options={
        "visibility_timeout": 14400,  # 4시간
    },

    # 큐 라우팅: Step 5만 render 큐, 나머지는 default 큐 자동
    task_routes={
        "app.pipeline.steps.step5_assemble.*": {"queue": "render"},
    },

    # Task 결과 만료 (24시간)
    result_expires=86400,
)

celery_app.autodiscover_tasks(["app.pipeline.steps"])
