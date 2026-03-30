from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SourceInput(BaseModel):
    url: str = Field(..., min_length=1)
    source_type: Literal["blog", "news", "youtube", "custom_text"] = "blog"
    custom_text: str | None = None


class VideoStyle(str, Enum):
    INFORMATIVE = "informative"
    ENTERTAINING = "entertaining"
    EDUCATIONAL = "educational"
    NEWS = "news"


class VideoGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    sources: list[SourceInput] = Field(..., min_length=1, max_length=10)
    style: VideoStyle = VideoStyle.INFORMATIVE
    target_duration_minutes: int = Field(default=12, ge=10, le=15)
    language: str = "ko"
    tts_voice: str = "alloy"
    include_subtitles: bool = True
    include_bgm: bool = True
    additional_instructions: str | None = None
    cost_budget_usd: float | None = Field(default=None, ge=0.1, le=50.0)
    auto_approve: bool = True
    idempotency_key: str | None = None


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str
