from pydantic import BaseModel


class SourceChunk(BaseModel):
    source_id: str
    chunk_index: int
    text: str
    timestamp_start: float | None = None
    timestamp_end: float | None = None


class RankedEvidence(BaseModel):
    chunk: SourceChunk
    relevance_score: float
    recency_score: float
    reliability_score: float
    composite_score: float
    is_duplicate: bool = False


class EvidencePack(BaseModel):
    topic: str
    total_sources: int
    deduplicated_sources: int
    ranked_chunks: list[RankedEvidence]
    key_claims: list[str]
    source_metadata: list[dict]
