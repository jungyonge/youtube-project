"""영상 처리 유틸리티 — Ken Burns, 전환 효과, BGM 믹싱, 자막 burn-in, 인코딩."""
from __future__ import annotations

import os
import re
from typing import Literal

from loguru import logger

KEN_BURNS_CYCLE: list[str] = ["zoom_in", "pan_right", "zoom_out", "pan_left"]
TARGET_W, TARGET_H = 1920, 1080


def get_ken_burns_effect(scene_index: int) -> str:
    return KEN_BURNS_CYCLE[scene_index % len(KEN_BURNS_CYCLE)]


def apply_ken_burns(image_clip, effect: str, duration: float):
    """MoviePy ImageClip에 Ken Burns 효과 적용."""
    from moviepy.video.fx import Resize, Crop

    w, h = image_clip.size
    scale = 1.2

    if effect == "zoom_in":
        def make_frame(get_frame, t):
            progress = t / max(duration, 0.1)
            s = 1.0 + (scale - 1.0) * progress
            new_w, new_h = int(w * s), int(h * s)
            from PIL import Image
            import numpy as np
            frame = get_frame(t)
            img = Image.fromarray(frame).resize((new_w, new_h))
            left = (new_w - w) // 2
            top = (new_h - h) // 2
            cropped = img.crop((left, top, left + w, top + h))
            return np.array(cropped)
        return image_clip.transform(make_frame)

    elif effect == "zoom_out":
        def make_frame(get_frame, t):
            progress = t / max(duration, 0.1)
            s = scale - (scale - 1.0) * progress
            new_w, new_h = int(w * s), int(h * s)
            from PIL import Image
            import numpy as np
            frame = get_frame(t)
            img = Image.fromarray(frame).resize((new_w, new_h))
            left = (new_w - w) // 2
            top = (new_h - h) // 2
            cropped = img.crop((left, top, left + w, top + h))
            return np.array(cropped)
        return image_clip.transform(make_frame)

    elif effect in ("pan_left", "pan_right"):
        extra_w = int(w * 0.2)
        def make_frame(get_frame, t):
            progress = t / max(duration, 0.1)
            from PIL import Image
            import numpy as np
            frame = get_frame(t)
            img = Image.fromarray(frame).resize((w + extra_w, h))
            if effect == "pan_right":
                left = int(extra_w * progress)
            else:
                left = int(extra_w * (1.0 - progress))
            cropped = img.crop((left, 0, left + w, h))
            return np.array(cropped)
        return image_clip.transform(make_frame)

    return image_clip


def apply_transition(clip, transition_type: str | None, duration: float = 0.5):
    """전환 효과 적용."""
    if not transition_type:
        return clip

    if transition_type == "fade_in":
        return clip.with_effects([__import__("moviepy.video.fx", fromlist=["FadeIn"]).FadeIn(duration)])
    elif transition_type == "fade_out":
        return clip.with_effects([__import__("moviepy.video.fx", fromlist=["FadeOut"]).FadeOut(duration)])

    return clip


def create_scene_clip(
    image_path: str,
    audio_path: str | None,
    duration: float,
    ken_burns_effect: str = "zoom_in",
    silence_after: float = 0.5,
):
    """이미지 + 오디오 → 씬 클립 생성."""
    from moviepy import ImageClip, AudioFileClip, concatenate_audioclips, AudioClip

    total_duration = duration + silence_after

    # 이미지 클립
    img_clip = ImageClip(image_path).with_duration(total_duration).resized((TARGET_W, TARGET_H))

    # Ken Burns 효과
    img_clip = apply_ken_burns(img_clip, ken_burns_effect, total_duration)

    # 오디오
    if audio_path and os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        if silence_after > 0:
            silence = AudioClip(lambda t: [0, 0], duration=silence_after, fps=44100)
            audio = concatenate_audioclips([audio, silence])
        img_clip = img_clip.with_audio(audio)

    return img_clip


def mix_bgm(main_clip, bgm_path: str, bgm_volume_db: float = -20.0):
    """나레이션 + BGM 믹싱."""
    from moviepy import AudioFileClip, CompositeAudioClip
    import numpy as np

    if not bgm_path or not os.path.exists(bgm_path):
        return main_clip

    bgm = AudioFileClip(bgm_path)

    # BGM 루프: 영상 길이에 맞춤
    total_dur = main_clip.duration
    if bgm.duration < total_dur:
        loops = int(total_dur / bgm.duration) + 1
        from moviepy import concatenate_audioclips
        bgm = concatenate_audioclips([bgm] * loops)
    bgm = bgm.subclipped(0, total_dur)

    # 볼륨 조절 (dB → 배율)
    volume_factor = 10 ** (bgm_volume_db / 20)
    bgm = bgm.with_volume_scaled(volume_factor)

    # 합성
    if main_clip.audio:
        combined = CompositeAudioClip([main_clip.audio, bgm])
        return main_clip.with_audio(combined)
    else:
        return main_clip.with_audio(bgm)


def parse_srt(srt_path: str) -> list[dict]:
    """SRT 파일 파싱 → [{start, end, text}, ...]."""
    if not os.path.exists(srt_path):
        return []

    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    entries = []
    blocks = re.split(r"\n\n+", content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        time_line = lines[1]
        text = " ".join(lines[2:])

        match = re.match(
            r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
            time_line,
        )
        if match:
            g = [int(x) for x in match.groups()]
            start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
            end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
            entries.append({"start": start, "end": end, "text": text})

    return entries


def burn_subtitles(video_clip, srt_path: str, font_path: str | None = None):
    """자막 burn-in (TextClip 오버레이)."""
    from moviepy import TextClip, CompositeVideoClip

    subs = parse_srt(srt_path)
    if not subs:
        return video_clip

    # 폰트 결정
    if not font_path:
        for p in [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/nanum/NanumGothic.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        ]:
            if os.path.exists(p):
                font_path = p
                break

    clips = [video_clip]
    for sub in subs:
        try:
            txt_clip = (
                TextClip(
                    text=sub["text"],
                    font_size=42,
                    color="white",
                    font=font_path or "Arial",
                    stroke_color="black",
                    stroke_width=2,
                    size=(TARGET_W - 200, None),
                    method="caption",
                )
                .with_start(sub["start"])
                .with_duration(sub["end"] - sub["start"])
                .with_position(("center", TARGET_H - 120))
            )
            clips.append(txt_clip)
        except Exception as e:
            logger.warning("Subtitle clip failed: {}", e)

    return CompositeVideoClip(clips)


def encode_final(
    video_clip,
    output_path: str,
    codec: str = "libx264",
    crf: int = 23,
    fps: int = 30,
    audio_codec: str = "aac",
    audio_bitrate: str = "192k",
) -> None:
    """FFmpeg 최종 인코딩."""
    video_clip.write_videofile(
        output_path,
        codec=codec,
        fps=fps,
        audio_codec=audio_codec,
        audio_bitrate=audio_bitrate,
        ffmpeg_params=["-crf", str(crf)],
        logger=None,  # MoviePy 내부 로그 억제
    )
    logger.info("Encoded video: {} ({:.1f}s)", output_path, video_clip.duration)
