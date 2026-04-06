"""씬 keywords에서 영상 파이프라인용 메타데이터를 파싱하는 유틸리티.

keywords 배열에 `bg:`, `char:`, `bubble:` 접두사로 인코딩된 메타데이터를 추출한다.
나머지는 SEO 태그로 분류한다.

예시 입력:
    ["bg:뉴욕증권거래소 혼란", "char:concerned", "bubble:금리가 문제야", "금리", "월가"]

예시 출력:
    {
        "bg_query": "뉴욕증권거래소 혼란",
        "char_expression": "concerned",
        "bubble_text": "금리가 문제야",
        "seo_tags": ["금리", "월가"],
    }
"""
from __future__ import annotations

from typing import Literal

VALID_EXPRESSIONS = {"neutral", "surprised", "serious", "happy", "concerned", "angry"}


def parse_scene_metadata(keywords: list[str]) -> dict:
    """keywords 배열에서 bg:/char:/bubble: 메타데이터를 추출한다.

    Returns:
        dict with keys: bg_query, char_expression, bubble_text, seo_tags
    """
    meta: dict = {
        "bg_query": None,
        "char_expression": "neutral",
        "bubble_text": None,
        "seo_tags": [],
    }

    for kw in keywords:
        if kw.startswith("bg:"):
            meta["bg_query"] = kw[3:].strip()
        elif kw.startswith("char:"):
            expr = kw[5:].strip()
            if expr in VALID_EXPRESSIONS:
                meta["char_expression"] = expr
        elif kw.startswith("bubble:"):
            meta["bubble_text"] = kw[7:].strip()
        else:
            meta["seo_tags"].append(kw)

    return meta
