"""멱등성 테스트."""
import pytest

from app.pipeline.models.script import FullScript, SceneAssetPlan, ScriptScene


def test_idempotency_key_in_request_schema():
    from app.api.schemas.request import VideoGenerationRequest, SourceInput

    req = VideoGenerationRequest(
        topic="테스트",
        sources=[SourceInput(url="https://example.com")],
        idempotency_key="unique-key-123",
    )
    assert req.idempotency_key == "unique-key-123"


def test_idempotency_key_optional():
    from app.api.schemas.request import VideoGenerationRequest, SourceInput

    req = VideoGenerationRequest(
        topic="테스트",
        sources=[SourceInput(url="https://example.com")],
    )
    assert req.idempotency_key is None
