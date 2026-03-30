"""Step 1c: 청킹 → 랭킹 → 근거팩(EvidencePack) 생성."""
from __future__ import annotations

import asyncio
import json
import math
import re
import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from app.config import settings
from app.db.models.source import Source
from app.db.models.video_job import VideoJob
from app.db.session import async_session_factory
from app.pipeline.models.evidence import EvidencePack, RankedEvidence, SourceChunk
from app.pipeline.step_utils import begin_step, check_cancelled, complete_step, fail_step
from app.storage.object_store import object_store
from app.workers.celery_app import celery_app

TOP_N_CHUNKS = 30
CHUNK_SIZE_MIN = 300
CHUNK_SIZE_MAX = 500


def _chunk_text(text: str, source_id: str) -> list[SourceChunk]:
    """문단 단위로 텍스트를 청킹 (300~500자)."""
    paragraphs = re.split(r"\n{2,}", text.strip())
    chunks: list[SourceChunk] = []
    buffer = ""
    idx = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(buffer) + len(para) < CHUNK_SIZE_MIN:
            buffer += ("\n" + para) if buffer else para
            continue

        if buffer:
            chunks.append(SourceChunk(source_id=source_id, chunk_index=idx, text=buffer))
            idx += 1
            buffer = ""

        if len(para) > CHUNK_SIZE_MAX:
            # 긴 문단은 문장 단위로 분리
            sentences = re.split(r"(?<=[.!?。\n])\s+", para)
            temp = ""
            for sent in sentences:
                if len(temp) + len(sent) > CHUNK_SIZE_MAX and temp:
                    chunks.append(SourceChunk(source_id=source_id, chunk_index=idx, text=temp))
                    idx += 1
                    temp = sent
                else:
                    temp += (" " + sent) if temp else sent
            if temp:
                buffer = temp
        else:
            buffer = para

    if buffer and len(buffer) >= 30:
        chunks.append(SourceChunk(source_id=source_id, chunk_index=idx, text=buffer))

    return chunks


def _chunk_youtube_text(text: str, source_id: str) -> list[SourceChunk]:
    """YouTube 자막은 줄 단위로 묶어서 청킹."""
    lines = text.strip().split("\n")
    chunks: list[SourceChunk] = []
    buffer = ""
    idx = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(buffer) + len(line) > CHUNK_SIZE_MAX and buffer:
            chunks.append(SourceChunk(source_id=source_id, chunk_index=idx, text=buffer))
            idx += 1
            buffer = line
        else:
            buffer += (" " + line) if buffer else line

    if buffer and len(buffer) >= 30:
        chunks.append(SourceChunk(source_id=source_id, chunk_index=idx, text=buffer))

    return chunks


def _compute_relevance_scores(chunks: list[SourceChunk], topic: str) -> list[float]:
    """TF-IDF 코사인 유사도로 주제 관련성 점수 계산."""
    if not chunks:
        return []

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        texts = [topic] + [c.text for c in chunks]
        vectorizer = TfidfVectorizer(max_features=5000)
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        return similarities.tolist()
    except Exception as e:
        logger.warning("TF-IDF failed (using uniform scores): {}", e)
        return [0.5] * len(chunks)


def _compute_recency_score(published_at: datetime | None) -> float:
    """최신성 점수 (exp decay, 반감기 7일)."""
    if not published_at:
        return 0.5  # 날짜 불명이면 중간값

    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_days = (now - published_at).total_seconds() / 86400

    if age_days < 0:
        return 1.0
    half_life = 7.0
    return math.exp(-0.693 * age_days / half_life)


@celery_app.task(name="pipeline.evidence_pack", bind=True, max_retries=0)
def evidence_pack_task(self, job_id: str) -> str:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_build_evidence_pack(job_id))


async def _build_evidence_pack(job_id: str) -> str:
    step_name = "evidence_pack"
    step_id = await begin_step(job_id, step_name)

    try:
        if await check_cancelled(job_id):
            raise RuntimeError("Job cancelled")

        # Job + Sources 로드
        async with async_session_factory() as db:
            job_result = await db.execute(
                select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
            )
            job = job_result.scalar_one()

            src_result = await db.execute(
                select(Source).where(
                    Source.job_id == uuid.UUID(job_id),
                    Source.content_snapshot_key.isnot(None),
                )
            )
            sources = list(src_result.scalars().all())

        topic = job.topic
        dedup_sources = [s for s in sources if not s.is_duplicate]

        # 1. 청킹
        all_chunks: list[SourceChunk] = []
        source_meta: dict[str, dict] = {}

        for source in dedup_sources:
            snapshot_bytes = await object_store.download(
                settings.S3_ASSETS_BUCKET, source.content_snapshot_key  # type: ignore[arg-type]
            )
            snapshot = json.loads(snapshot_bytes.decode("utf-8"))
            text = snapshot.get("text_content", "")

            sid = str(source.id)
            if source.source_type == "youtube":
                chunks = _chunk_youtube_text(text, sid)
            else:
                chunks = _chunk_text(text, sid)

            all_chunks.extend(chunks)
            source_meta[sid] = {
                "source_id": sid,
                "domain": source.domain,
                "title": source.title,
                "author": source.author,
                "published_at": source.published_at.isoformat() if source.published_at else None,
                "reliability_score": source.reliability_score or 0.3,
                "source_type": source.source_type,
            }

        if not all_chunks:
            raise ValueError("No chunks produced from sources")

        # 2. 랭킹
        relevance_scores = _compute_relevance_scores(all_chunks, topic)

        # source별 recency / reliability 매핑
        source_recency: dict[str, float] = {}
        source_reliability: dict[str, float] = {}
        for source in dedup_sources:
            sid = str(source.id)
            source_recency[sid] = _compute_recency_score(source.published_at)
            source_reliability[sid] = source.reliability_score or 0.3

        ranked: list[RankedEvidence] = []
        for i, chunk in enumerate(all_chunks):
            rel = relevance_scores[i] if i < len(relevance_scores) else 0.5
            rec = source_recency.get(chunk.source_id, 0.5)
            ria = source_reliability.get(chunk.source_id, 0.3)
            composite = 0.5 * rel + 0.3 * rec + 0.2 * ria

            ranked.append(RankedEvidence(
                chunk=chunk,
                relevance_score=round(rel, 4),
                recency_score=round(rec, 4),
                reliability_score=round(ria, 4),
                composite_score=round(composite, 4),
            ))

        # 3. 상위 N개 선택
        ranked.sort(key=lambda r: r.composite_score, reverse=True)
        top_chunks = ranked[:TOP_N_CHUNKS]

        # 4. 핵심 주장 요약 (Gemini가 없으면 상위 청크에서 추출)
        key_claims = await _extract_key_claims(topic, top_chunks)

        # EvidencePack 생성
        evidence_pack = EvidencePack(
            topic=topic,
            total_sources=len(sources),
            deduplicated_sources=len(dedup_sources),
            ranked_chunks=top_chunks,
            key_claims=key_claims,
            source_metadata=list(source_meta.values()),
        )

        # S3 저장
        pack_key = f"{job_id}/evidence_pack.json"
        await object_store.upload(
            settings.S3_ASSETS_BUCKET,
            pack_key,
            evidence_pack.model_dump_json(indent=2).encode("utf-8"),
            content_type="application/json",
        )

        await complete_step(
            step_id, job_id, step_name,
            progress_percent=20,
            artifact_keys=[pack_key],
            metadata={
                "total_chunks": len(all_chunks),
                "selected_chunks": len(top_chunks),
                "key_claims": len(key_claims),
            },
        )
        logger.info(
            "Evidence pack created: job={} chunks={}/{} claims={}",
            job_id, len(top_chunks), len(all_chunks), len(key_claims),
        )
        return job_id

    except Exception as e:
        await fail_step(step_id, job_id, step_name, e)
        raise


async def _extract_key_claims(topic: str, chunks: list[RankedEvidence]) -> list[str]:
    """Gemini Flash로 핵심 주장 추출. 실패 시 상위 청크 첫 문장으로 대체."""
    try:
        from app.services.gemini_client import GeminiClient
        client = GeminiClient()

        combined_text = "\n\n".join(c.chunk.text[:300] for c in chunks[:10])
        prompt = (
            f"주제: {topic}\n\n"
            f"아래 자료에서 핵심 주장 5~10개를 한 줄씩 추출하세요. "
            f"번호를 붙이지 말고, 한 줄에 하나씩만 작성하세요.\n\n"
            f"{combined_text}"
        )
        response = await client.generate(prompt, temperature=0.3)
        claims = [line.strip() for line in response.text.strip().split("\n") if line.strip()]
        if claims:
            return claims[:10]
    except Exception as e:
        logger.warning("Gemini key claims extraction failed (using fallback): {}", e)

    # Fallback: 상위 청크 첫 문장
    claims = []
    for c in chunks[:8]:
        first_sentence = re.split(r"[.!?。]", c.chunk.text)[0].strip()
        if first_sentence and len(first_sentence) > 10:
            claims.append(first_sentence)
    return claims
