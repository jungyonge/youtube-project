"""비용 예산 테스트."""
from app.services.cost_tracker import CostTracker


def test_degrade_level_0_normal():
    assert CostTracker._calc_degrade_level(50.0) == 0
    assert CostTracker._calc_degrade_level(79.9) == 0


def test_degrade_level_1_reduce_images():
    assert CostTracker._calc_degrade_level(80.0) == 1
    assert CostTracker._calc_degrade_level(89.9) == 1


def test_degrade_level_2_flash_model():
    assert CostTracker._calc_degrade_level(90.0) == 2
    assert CostTracker._calc_degrade_level(94.9) == 2


def test_degrade_level_3_all_text_overlay():
    assert CostTracker._calc_degrade_level(95.0) == 3
    assert CostTracker._calc_degrade_level(99.9) == 3


def test_degrade_level_4_fail():
    assert CostTracker._calc_degrade_level(100.0) == 4
    assert CostTracker._calc_degrade_level(150.0) == 4
