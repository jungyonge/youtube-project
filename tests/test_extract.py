"""콘텐츠 추출 테스트."""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.content_extractor import (
    ContentExtractorService,
    CustomTextExtractor,
    ExtractedContent,
    _detect_source_type,
)


def test_detect_youtube_url():
    assert _detect_source_type("https://www.youtube.com/watch?v=abc123") == "youtube"
    assert _detect_source_type("https://youtu.be/abc123") == "youtube"


def test_detect_blog_url():
    assert _detect_source_type("https://blog.example.com/post") == "blog"
    assert _detect_source_type("https://news.example.com/article") == "blog"


@pytest.mark.asyncio
async def test_custom_text_extractor():
    extractor = CustomTextExtractor()
    result = await extractor.extract("http://custom", custom_text="사용자가 입력한 텍스트입니다.")
    assert result.source_type == "custom_text"
    assert result.text_content == "사용자가 입력한 텍스트입니다."
    assert result.extraction_method == "user_input"
    assert result.word_count > 0


@pytest.mark.asyncio
async def test_custom_text_empty_raises():
    extractor = CustomTextExtractor()
    with pytest.raises(ValueError, match="custom_text is required"):
        await extractor.extract("http://custom")


@pytest.mark.asyncio
async def test_content_extractor_service_auto_detect():
    service = ContentExtractorService()
    # custom_text로 직접 추출 (외부 네트워크 없이)
    result = await service.extract(
        url="http://custom",
        source_type="custom_text",
        custom_text="테스트 콘텐츠",
    )
    assert result.text_content == "테스트 콘텐츠"
