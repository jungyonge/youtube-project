"""URL 유형별 콘텐츠 추출 — Strategy 패턴."""
from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from urllib.parse import urlparse

import httpx
from loguru import logger

from app.utils.retry import retry_network


@dataclass
class ExtractedContent:
    source_type: str
    url: str
    title: str | None
    author: str | None
    published_date: datetime | None
    text_content: str
    word_count: int
    extraction_method: str


class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, url: str, **kwargs) -> ExtractedContent:
        ...


class BlogExtractor(BaseExtractor):
    @retry_network
    async def extract(self, url: str, **kwargs) -> ExtractedContent:
        # newspaper3k 먼저 시도
        try:
            return await self._extract_newspaper(url)
        except Exception as e:
            logger.debug("newspaper3k failed for {}: {}, trying BeautifulSoup", url, e)
            return await self._extract_bs4(url)

    async def _extract_newspaper(self, url: str) -> ExtractedContent:
        from newspaper import Article

        loop = asyncio.get_event_loop()
        article = Article(url, language="ko")
        await loop.run_in_executor(None, article.download)
        await loop.run_in_executor(None, article.parse)

        if not article.text or len(article.text.strip()) < 50:
            raise ValueError(f"Insufficient content from newspaper3k: {len(article.text or '')} chars")

        pub_date = None
        if article.publish_date:
            pub_date = article.publish_date if isinstance(article.publish_date, datetime) else None

        return ExtractedContent(
            source_type="blog",
            url=url,
            title=article.title,
            author=", ".join(article.authors) if article.authors else None,
            published_date=pub_date,
            text_content=article.text,
            word_count=len(article.text.split()),
            extraction_method="newspaper3k",
        )

    async def _extract_bs4(self, url: str) -> ExtractedContent:
        from bs4 import BeautifulSoup

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 불필요한 태그 제거
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "ad"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else None

        # 본문 후보 추출
        article_tag = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"content|article|post|entry"))
        text = article_tag.get_text(separator="\n", strip=True) if article_tag else soup.body.get_text(separator="\n", strip=True) if soup.body else ""

        if len(text.strip()) < 50:
            raise ValueError(f"Insufficient content from BS4: {len(text)} chars")

        return ExtractedContent(
            source_type="blog",
            url=url,
            title=title,
            author=None,
            published_date=None,
            text_content=text,
            word_count=len(text.split()),
            extraction_method="beautifulsoup",
        )


class NewsExtractor(BaseExtractor):
    @retry_network
    async def extract(self, url: str, **kwargs) -> ExtractedContent:
        try:
            return await BlogExtractor()._extract_newspaper(url)
        except Exception as e:
            logger.debug("newspaper3k failed for news {}: {}, trying Playwright", url, e)
            return await self._extract_playwright(url)

    async def _extract_playwright(self, url: str) -> ExtractedContent:
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.warning("Playwright not available, falling back to BS4")
            return await BlogExtractor()._extract_bs4(url)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            title = await page.title()
            content = await page.evaluate("""
                () => {
                    const article = document.querySelector('article') ||
                                    document.querySelector('main') ||
                                    document.querySelector('.article-body') ||
                                    document.body;
                    return article ? article.innerText : document.body.innerText;
                }
            """)
            await browser.close()

        if not content or len(content.strip()) < 50:
            raise ValueError(f"Insufficient content from Playwright: {len(content or '')} chars")

        return ExtractedContent(
            source_type="news",
            url=url,
            title=title,
            author=None,
            published_date=None,
            text_content=content,
            word_count=len(content.split()),
            extraction_method="playwright",
        )


class YouTubeExtractor(BaseExtractor):
    _VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|/embed/|/v/)([a-zA-Z0-9_-]{11})")

    def _parse_video_id(self, url: str) -> str:
        m = self._VIDEO_ID_RE.search(url)
        if not m:
            raise ValueError(f"Cannot parse YouTube video ID from: {url}")
        return m.group(1)

    @retry_network
    async def extract(self, url: str, **kwargs) -> ExtractedContent:
        video_id = self._parse_video_id(url)
        try:
            return await self._extract_transcript_api(url, video_id)
        except Exception as e:
            logger.debug("youtube-transcript-api failed for {}: {}, trying yt-dlp", video_id, e)
            return await self._extract_ytdlp(url, video_id)

    async def _extract_transcript_api(self, url: str, video_id: str) -> ExtractedContent:
        from youtube_transcript_api import YouTubeTranscriptApi

        loop = asyncio.get_event_loop()
        fetcher = YouTubeTranscriptApi()
        transcript = await loop.run_in_executor(
            None,
            partial(fetcher.fetch, video_id, languages=["ko", "en"]),
        )

        text_parts = []
        for snippet in transcript:
            text_parts.append(snippet.text)

        full_text = "\n".join(text_parts)
        if len(full_text.strip()) < 30:
            raise ValueError("Transcript too short")

        return ExtractedContent(
            source_type="youtube",
            url=url,
            title=None,
            author=None,
            published_date=None,
            text_content=full_text,
            word_count=len(full_text.split()),
            extraction_method="youtube-transcript-api",
        )

    async def _extract_ytdlp(self, url: str, video_id: str) -> ExtractedContent:
        import tempfile
        import json as _json
        import os

        loop = asyncio.get_event_loop()

        with tempfile.TemporaryDirectory() as tmpdir:
            import yt_dlp

            ydl_opts = {
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["ko", "en"],
                "subtitlesformat": "json3",
                "skip_download": True,
                "outtmpl": os.path.join(tmpdir, "%(id)s"),
                "quiet": True,
            }

            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=True)

            info = await loop.run_in_executor(None, _download)
            title = info.get("title")
            author = info.get("uploader")

            # 자막 파일 찾기
            text_parts = []
            for fname in os.listdir(tmpdir):
                if fname.endswith(".json3"):
                    with open(os.path.join(tmpdir, fname)) as f:
                        data = _json.load(f)
                    for event in data.get("events", []):
                        segs = event.get("segs", [])
                        for seg in segs:
                            t = seg.get("utf8", "").strip()
                            if t:
                                text_parts.append(t)
                    break

            if not text_parts:
                raise ValueError("No subtitles found via yt-dlp")

            full_text = " ".join(text_parts)

        return ExtractedContent(
            source_type="youtube",
            url=url,
            title=title,
            author=author,
            published_date=None,
            text_content=full_text,
            word_count=len(full_text.split()),
            extraction_method="yt-dlp",
        )


class CustomTextExtractor(BaseExtractor):
    async def extract(self, url: str, **kwargs) -> ExtractedContent:
        custom_text = kwargs.get("custom_text", "")
        if not custom_text:
            raise ValueError("custom_text is required for custom_text source type")
        return ExtractedContent(
            source_type="custom_text",
            url=url,
            title=None,
            author=None,
            published_date=None,
            text_content=custom_text,
            word_count=len(custom_text.split()),
            extraction_method="user_input",
        )


_EXTRACTORS: dict[str, BaseExtractor] = {
    "blog": BlogExtractor(),
    "news": NewsExtractor(),
    "youtube": YouTubeExtractor(),
    "custom_text": CustomTextExtractor(),
}


def _detect_source_type(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    return "blog"


class ContentExtractorService:
    async def extract(self, url: str, source_type: str = "blog", **kwargs) -> ExtractedContent:
        if source_type == "blog" and url:
            detected = _detect_source_type(url)
            if detected != "blog":
                source_type = detected

        extractor = _EXTRACTORS.get(source_type)
        if not extractor:
            raise ValueError(f"Unknown source_type: {source_type}")

        logger.info("Extracting content: url={} type={}", url[:80], source_type)
        result = await extractor.extract(url, **kwargs)
        logger.info("Extracted {} chars via {}", result.word_count, result.extraction_method)
        return result
