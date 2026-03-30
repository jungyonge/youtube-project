"""근거팩 생성 테스트."""
import pytest

from app.pipeline.models.evidence import EvidencePack, RankedEvidence, SourceChunk
from app.pipeline.steps.step1c_evidence_pack import (
    _chunk_text,
    _chunk_youtube_text,
    _compute_recency_score,
    _compute_relevance_scores,
)
from datetime import datetime, timezone, timedelta


def test_chunk_text_produces_chunks():
    text = ("문단 1. " * 50 + "\n\n" + "문단 2. " * 50)
    chunks = _chunk_text(text, "src1")
    assert len(chunks) >= 2
    for c in chunks:
        assert c.source_id == "src1"
        assert len(c.text) >= 30


def test_chunk_text_short_text():
    text = "짧은 텍스트"
    chunks = _chunk_text(text, "src1")
    # Very short text might not produce chunks
    assert isinstance(chunks, list)


def test_chunk_youtube():
    text = "\n".join([f"자막 라인 {i}" for i in range(50)])
    chunks = _chunk_youtube_text(text, "yt1")
    assert len(chunks) >= 1
    assert chunks[0].source_id == "yt1"


def test_relevance_scores():
    chunks = [
        SourceChunk(source_id="s1", chunk_index=0, text="인공지능 머신러닝 딥러닝 기술 발전"),
        SourceChunk(source_id="s1", chunk_index=1, text="오늘 날씨가 좋고 꽃이 핀다"),
    ]
    scores = _compute_relevance_scores(chunks, "인공지능 기술 동향")
    assert len(scores) == 2
    assert scores[0] > scores[1]


def test_recency_score_recent():
    recent = datetime.now(timezone.utc) - timedelta(hours=1)
    score = _compute_recency_score(recent)
    assert score > 0.9


def test_recency_score_old():
    old = datetime.now(timezone.utc) - timedelta(days=30)
    score = _compute_recency_score(old)
    assert score < 0.2


def test_recency_score_none():
    score = _compute_recency_score(None)
    assert score == 0.5


def test_evidence_pack_model():
    chunk = SourceChunk(source_id="s1", chunk_index=0, text="test")
    ranked = RankedEvidence(
        chunk=chunk,
        relevance_score=0.8,
        recency_score=0.7,
        reliability_score=0.9,
        composite_score=0.8,
    )
    pack = EvidencePack(
        topic="test",
        total_sources=1,
        deduplicated_sources=1,
        ranked_chunks=[ranked],
        key_claims=["claim1"],
        source_metadata=[{"domain": "test.com"}],
    )
    assert pack.topic == "test"
    assert len(pack.ranked_chunks) == 1
    json_str = pack.model_dump_json()
    assert "test" in json_str
