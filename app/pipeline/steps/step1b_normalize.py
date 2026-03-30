"""Step 1b: 소스 정규화 + 중복 제거 + 메타데이터 보강."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import uuid
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from loguru import logger
from sqlalchemy import select, update

from app.config import settings
from app.db.models.source import Source
from app.db.sync_session import SyncSessionLocal
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app

# 도메인별 신뢰도 점수
_MAJOR_NEWS = {
    "chosun.com", "donga.com", "joongang.co.kr", "hani.co.kr", "khan.co.kr",
    "mk.co.kr", "hankyung.com", "sedaily.com", "edaily.co.kr", "mt.co.kr",
    "reuters.com", "apnews.com", "bbc.com", "nytimes.com", "bloomberg.com",
    "yna.co.kr", "yonhapnews.co.kr", "sbs.co.kr", "kbs.co.kr", "mbc.co.kr",
}
_TECH_BLOGS = {
    "techcrunch.com", "theverge.com", "wired.com", "arstechnica.com",
    "zdnet.co.kr", "bloter.net", "itworld.co.kr",
}

_UTM_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}

_AD_KEYWORDS = {
    "광고", "협찬", "제휴", "스폰서", "sponsored", "advertisement", "promotion",
    "할인", "쿠폰", "이벤트", "무료체험", "가입하세요",
}


def _run_async(coro):
    """Run an async coroutine from sync Celery task context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


def _canonicalize_url(url: str) -> str:
    parsed = urlparse(url)

    # www 제거
    host = parsed.hostname or ""
    if host.startswith("www."):
        host = host[4:]

    # UTM 파라미터 제거
    qs = parse_qs(parsed.query, keep_blank_values=False)
    filtered_qs = {k: v for k, v in qs.items() if k.lower() not in _UTM_PARAMS}
    clean_query = urlencode(filtered_qs, doseq=True)

    # fragment 제거, trailing slash 정규화
    path = parsed.path.rstrip("/") or "/"

    return urlunparse((
        parsed.scheme or "https",
        host,
        path,
        "",
        clean_query,
        "",
    ))


def _content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def _get_reliability_score(domain: str) -> float:
    if not domain:
        return 0.3
    for d in _MAJOR_NEWS:
        if domain.endswith(d):
            return 0.9
    for d in _TECH_BLOGS:
        if domain.endswith(d):
            return 0.7
    if any(kw in domain for kw in ("blog", "tistory", "naver", "velog", "medium")):
        return 0.5
    return 0.3


def _check_ad_ratio(text: str) -> float:
    words = text.split()
    if not words:
        return 0.0
    ad_count = sum(1 for w in words if w in _AD_KEYWORDS)
    return ad_count / len(words)


@celery_app.task(name="pipeline.normalize", bind=True, max_retries=0)
def normalize_task(self, job_id: str) -> str:
    step_name = "normalize"
    step_id = begin_step(job_id, step_name)

    try:
        if check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        with SyncSessionLocal() as db:
            result = db.execute(
                select(Source).where(Source.job_id == uuid.UUID(job_id))
            )
            sources = list(result.scalars().all())

        # 1. 정규화 + 해시 계산
        seen_hashes: dict[str, uuid.UUID] = {}
        duplicates = 0

        for source in sources:
            if not source.content_snapshot_key:
                continue

            # S3에서 스냅샷 로드 (async → _run_async)
            snapshot_bytes = _run_async(object_store.download(
                settings.S3_ASSETS_BUCKET, source.content_snapshot_key
            ))
            snapshot = json.loads(snapshot_bytes.decode("utf-8"))
            text_content = snapshot.get("text_content", "")

            # Canonical URL
            canonical = _canonicalize_url(source.original_url)
            parsed = urlparse(canonical)
            domain = parsed.hostname or ""

            # Content hash + 중복 탐지
            c_hash = _content_hash(text_content)
            is_dup = False
            if c_hash in seen_hashes:
                is_dup = True
                duplicates += 1
            else:
                seen_hashes[c_hash] = source.id

            # 신뢰도
            reliability = _get_reliability_score(domain)

            # 광고 비율 체크
            ad_ratio = _check_ad_ratio(text_content)
            if ad_ratio >= 0.2:
                logger.warning("High ad ratio ({:.0%}) for source: {}", ad_ratio, source.original_url[:60])

            # DB 업데이트 (sync)
            with SyncSessionLocal() as db:
                db.execute(
                    update(Source)
                    .where(Source.id == source.id)
                    .values(
                        canonical_url=canonical,
                        domain=domain,
                        content_hash=c_hash,
                        is_duplicate=is_dup,
                        reliability_score=reliability,
                    )
                )
                db.commit()

        complete_step(
            step_id, job_id, step_name,
            progress_percent=15,
            metadata={"total_sources": len(sources), "duplicates": duplicates},
        )
        return job_id

    except Exception as e:
        fail_step(step_id, job_id, step_name, e)
        raise
