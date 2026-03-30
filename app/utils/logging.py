"""loguru 기반 구조화 로그 설정."""
from __future__ import annotations

import sys

from loguru import logger

from app.config import settings

LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level:<8}</level> | "
    "trace={extra[trace_id]} job={extra[job_id]} step={extra[step_name]} | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "{message}"
)

LOG_FORMAT_JSON = (
    '{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}",'
    '"level":"{level}",'
    '"trace_id":"{extra[trace_id]}",'
    '"job_id":"{extra[job_id]}",'
    '"step_name":"{extra[step_name]}",'
    '"module":"{name}",'
    '"message":"{message}"}}'
)


def setup_logging(json_format: bool = False) -> None:
    """로그 설정 초기화. main.py lifespan에서 호출."""
    # 기본 핸들러 제거
    logger.remove()

    # 기본 컨텍스트 값 설정 (바인딩 전에 사용될 수 있으므로)
    logger.configure(extra={"trace_id": "", "job_id": "", "step_name": ""})

    fmt = LOG_FORMAT_JSON if json_format else LOG_FORMAT

    # stdout 핸들러 (Docker 로그 수집 호환)
    logger.add(
        sys.stdout,
        format=fmt,
        level=settings.LOG_LEVEL,
        colorize=not json_format,
        backtrace=True,
        diagnose=True,
    )

    logger.info("Logging initialized: level={} json={}", settings.LOG_LEVEL, json_format)
