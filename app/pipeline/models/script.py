from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SceneClaim(BaseModel):
    claim_text: str
    claim_type: Literal["fact", "inference", "opinion"]
    evidence_source_id: str
    evidence_quote: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class SceneCitation(BaseModel):
    source_domain: str
    source_title: str
    display_text: str


class SceneAssetPlan(BaseModel):
    asset_type: Literal[
        "generated_image",
        "quote_card",
        "data_chart",
        "timeline_card",
        "title_card",
        "web_capture",
        "text_overlay",
        "split_screen",
    ]
    generation_prompt: str | None = None
    template_id: str | None = None
    template_data: dict | None = None
    fallback_strategy: Literal["placeholder", "text_overlay", "skip"] = "placeholder"
    priority: int = 1


class ScriptScene(BaseModel):
    scene_id: int
    section: str
    purpose: str
    duration_target_sec: int
    duration_actual_sec: int | None = None
    narration: str
    subtitle_chunks: list[str] = []
    asset_plan: list[SceneAssetPlan] = []
    transition_in: str | None = None
    transition_out: str | None = None
    claims: list[SceneClaim] = []
    citations: list[SceneCitation] = []
    policy_flags: list[str] = []
    keywords: list[str] = []


class FullScript(BaseModel):
    title: str
    subtitle: str
    total_duration_sec: int
    thumbnail_prompt: str
    scenes: list[ScriptScene]
    tags: list[str] = []
    description: str = ""
    overall_sensitivity: Literal["low", "medium", "high"] = "low"
    requires_human_approval: bool = False
    policy_warnings: list[str] = []
