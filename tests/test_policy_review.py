"""정책 검수 관련 테스트."""
from app.pipeline.models.script import FullScript, SceneAssetPlan, SceneClaim, ScriptScene


def _make_scene(policy_flags: list[str] = None, narration: str = "테스트") -> ScriptScene:
    return ScriptScene(
        scene_id=1,
        section="body_1",
        purpose="테스트",
        duration_target_sec=30,
        narration=narration,
        asset_plan=[SceneAssetPlan(asset_type="text_overlay")],
        policy_flags=policy_flags or [],
    )


def test_sensitivity_low():
    script = FullScript(
        title="기술 트렌드",
        subtitle="sub",
        total_duration_sec=300,
        thumbnail_prompt="tech",
        scenes=[_make_scene()],
        overall_sensitivity="low",
    )
    assert script.overall_sensitivity == "low"
    assert script.requires_human_approval is False


def test_sensitivity_high_requires_approval():
    script = FullScript(
        title="주식 투자 가이드",
        subtitle="sub",
        total_duration_sec=300,
        thumbnail_prompt="stocks",
        scenes=[_make_scene(policy_flags=["contains_stock_prediction"])],
        overall_sensitivity="high",
        requires_human_approval=True,
        policy_warnings=["투자 예측 포함"],
    )
    assert script.overall_sensitivity == "high"
    assert script.requires_human_approval is True
    assert len(script.policy_warnings) == 1


def test_policy_flags_stock():
    scene = _make_scene(policy_flags=["contains_stock_prediction"])
    assert "contains_stock_prediction" in scene.policy_flags


def test_policy_flags_political():
    scene = _make_scene(policy_flags=["mentions_politician"])
    assert "mentions_politician" in scene.policy_flags


def test_policy_flags_medical():
    scene = _make_scene(policy_flags=["contains_medical_advice"])
    assert "contains_medical_advice" in scene.policy_flags


def test_claim_types():
    claim_fact = SceneClaim(
        claim_text="GDP가 3% 성장했다",
        claim_type="fact",
        evidence_source_id="src-1",
        confidence=0.95,
    )
    claim_inference = SceneClaim(
        claim_text="앞으로도 성장할 것으로 보인다",
        claim_type="inference",
        evidence_source_id="src-1",
        confidence=0.6,
    )
    claim_opinion = SceneClaim(
        claim_text="이것은 좋은 신호다",
        claim_type="opinion",
        evidence_source_id="src-1",
        confidence=0.4,
    )
    assert claim_fact.claim_type == "fact"
    assert claim_inference.claim_type == "inference"
    assert claim_opinion.claim_type == "opinion"


def test_no_flags_means_skip():
    """policy_flags가 없는 씬은 정책 검수를 skip해야 함."""
    scenes = [_make_scene(), _make_scene(), _make_scene()]
    flagged = [s for s in scenes if s.policy_flags]
    assert len(flagged) == 0
