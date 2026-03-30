"""소스 정규화 테스트."""
from app.pipeline.steps.step1b_normalize import (
    _canonicalize_url,
    _check_ad_ratio,
    _content_hash,
    _get_reliability_score,
)


def test_canonicalize_removes_utm():
    url = "https://www.example.com/page?utm_source=google&utm_medium=cpc&id=42"
    result = _canonicalize_url(url)
    assert "utm_source" not in result
    assert "id=42" in result


def test_canonicalize_removes_www():
    url = "https://www.example.com/page"
    result = _canonicalize_url(url)
    assert result == "https://example.com/page"


def test_canonicalize_removes_fragment():
    url = "https://example.com/page#section"
    result = _canonicalize_url(url)
    assert "#" not in result


def test_canonicalize_trailing_slash():
    url = "https://example.com/page/"
    result = _canonicalize_url(url)
    assert result == "https://example.com/page"


def test_content_hash_same_text():
    h1 = _content_hash("Hello world")
    h2 = _content_hash("Hello  world")  # extra space
    assert h1 == h2  # normalized


def test_content_hash_different_text():
    h1 = _content_hash("Hello world")
    h2 = _content_hash("Goodbye world")
    assert h1 != h2


def test_reliability_major_news():
    assert _get_reliability_score("chosun.com") == 0.9
    assert _get_reliability_score("news.nytimes.com") == 0.9


def test_reliability_tech_blog():
    assert _get_reliability_score("techcrunch.com") == 0.7


def test_reliability_general_blog():
    assert _get_reliability_score("tistory.com") == 0.5
    assert _get_reliability_score("myblog.naver.com") == 0.5


def test_reliability_unknown():
    assert _get_reliability_score("random-site.xyz") == 0.3
    assert _get_reliability_score("") == 0.3


def test_ad_ratio_low():
    text = "인공지능 기술이 빠르게 발전하고 있다 최근 연구에 따르면"
    assert _check_ad_ratio(text) < 0.2


def test_ad_ratio_high():
    text = "광고 협찬 할인 쿠폰 이벤트 무료체험 가입하세요 스폰서 제휴 promotion"
    assert _check_ad_ratio(text) >= 0.2
