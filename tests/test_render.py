"""렌더 관련 테스트."""
from app.pipeline.models.render_manifest import RenderManifest, RenderSceneInstruction
from app.pipeline.steps.step4c_subtitles import _build_srt, _format_srt_time, _split_text_to_chunks
from app.pipeline.models.script import FullScript, SceneAssetPlan, ScriptScene


def test_render_manifest_defaults():
    manifest = RenderManifest(job_id="test", total_scenes=0)
    assert manifest.resolution == "1920x1080"
    assert manifest.fps == 30
    assert manifest.codec == "libx264"
    assert manifest.crf == 23
    assert manifest.audio_codec == "aac"
    assert manifest.audio_bitrate == "192k"
    assert manifest.bgm_volume_db == -20.0
    assert manifest.burn_subtitles is True


def test_render_scene_instruction():
    scene = RenderSceneInstruction(
        scene_id=1,
        audio_object_key="job/audio/scene_1.mp3",
        audio_duration_sec=30.0,
        image_object_key="job/images/scene_1.png",
        ken_burns_effect="zoom_in",
    )
    assert scene.silence_after_sec == 0.5
    assert scene.transition_in is None


def test_srt_time_format():
    assert _format_srt_time(0) == "00:00:00,000"
    assert _format_srt_time(61.5) == "00:01:01,500"
    assert _format_srt_time(3661.123) == "01:01:01,123"


def test_subtitle_chunking_korean():
    text = "이것은 한국어 자막 테스트입니다 적절한 길이로 분절됩니다"
    chunks = _split_text_to_chunks(text, 20)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 25  # some tolerance


def test_build_srt_from_script():
    scenes = [
        ScriptScene(
            scene_id=1,
            section="hook",
            purpose="오프닝",
            duration_target_sec=10,
            duration_actual_sec=10,
            narration="첫 번째 나레이션입니다",
            asset_plan=[SceneAssetPlan(asset_type="text_overlay")],
        ),
        ScriptScene(
            scene_id=2,
            section="body_1",
            purpose="본문",
            duration_target_sec=15,
            duration_actual_sec=15,
            narration="두 번째 나레이션입니다",
            asset_plan=[SceneAssetPlan(asset_type="text_overlay")],
        ),
    ]
    script = FullScript(
        title="test",
        subtitle="sub",
        total_duration_sec=25,
        thumbnail_prompt="test",
        scenes=scenes,
    )
    srt = _build_srt(script)
    assert "00:00:00" in srt
    assert "나레이션" in srt
    lines = srt.strip().split("\n")
    assert len(lines) > 0
