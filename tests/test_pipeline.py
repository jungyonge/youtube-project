"""파이프라인 오케스트레이션 테스트."""
from app.pipeline.orchestrator import STEP_ORDER, resume_pipeline, start_pipeline
from app.utils.video_utils import get_ken_burns_effect, parse_srt


def test_step_order_has_all_steps():
    step_names = [name for name, _ in STEP_ORDER]
    assert "extract" in step_names
    assert "normalize" in step_names
    assert "evidence_pack" in step_names
    assert "research" in step_names
    assert "review" in step_names
    assert "policy_review" in step_names
    assert "human_gate" in step_names
    assert "tts" in step_names
    assert "images" in step_names
    assert "bgm" in step_names
    assert "subtitles" in step_names
    assert "assemble" in step_names
    assert len(STEP_ORDER) == 12


def test_ken_burns_rotation():
    effects = [get_ken_burns_effect(i) for i in range(8)]
    assert effects[0] == "zoom_in"
    assert effects[1] == "pan_right"
    assert effects[2] == "zoom_out"
    assert effects[3] == "pan_left"
    assert effects[4] == "zoom_in"  # cycle repeats


def test_srt_parser_valid():
    import tempfile
    import os

    srt = """1
00:00:00,000 --> 00:00:02,500
첫 번째

2
00:00:02,500 --> 00:00:05,000
두 번째
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False, encoding="utf-8") as f:
        f.write(srt)
        path = f.name

    entries = parse_srt(path)
    os.unlink(path)
    assert len(entries) == 2
    assert entries[0]["text"] == "첫 번째"
    assert entries[1]["start"] == 2.5


def test_srt_parser_empty():
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False) as f:
        f.write("")
        path = f.name

    entries = parse_srt(path)
    os.unlink(path)
    assert entries == []


def test_resume_pipeline_invalid_step():
    import pytest
    with pytest.raises(ValueError, match="Unknown step"):
        resume_pipeline("fake-job-id", from_step="nonexistent_step")
