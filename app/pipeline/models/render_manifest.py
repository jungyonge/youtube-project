from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RenderSceneInstruction(BaseModel):
    scene_id: int
    audio_object_key: str
    audio_duration_sec: float
    image_object_key: str
    ken_burns_effect: Literal["zoom_in", "zoom_out", "pan_left", "pan_right"] = "zoom_in"
    transition_in: str | None = None
    transition_out: str | None = None
    silence_after_sec: float = 0.5


class RenderManifest(BaseModel):
    job_id: str
    total_scenes: int
    resolution: str = "1920x1080"
    fps: int = 30
    codec: str = "libx264"
    crf: int = 23
    audio_codec: str = "aac"
    audio_bitrate: str = "192k"
    scenes: list[RenderSceneInstruction] = []
    bgm_object_key: str | None = None
    bgm_volume_db: float = -20.0
    subtitle_srt_key: str | None = None
    burn_subtitles: bool = True
    intro_template_key: str | None = None
    outro_template_key: str | None = None
