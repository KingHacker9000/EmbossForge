from pathlib import Path

import cv2
import numpy as np
import pytest

from embossforge.config import DieSpec, adventurer_5m_profile
from embossforge.heightmap import build_female_surface_map, build_height_map
from embossforge.relief import ReliefPolarity, ReliefSpec, ReliefStyle, ValidationFinding, ValidationReport, ValidationSeverity
from embossforge.validation import validate_heightfield_mating


def _heightmap(path: Path) -> Path:
    image = np.full((128, 128), 255, dtype=np.uint8)
    cv2.circle(image, (64, 64), 35, 0, -1)
    assert cv2.imwrite(str(path), image)
    return path


def test_relief_spec_validation():
    spec = ReliefSpec()
    spec.validate()
    assert spec.style == ReliefStyle.STEPPED
    assert spec.levels == 6
    assert spec.polarity == ReliefPolarity.DARK_HIGH

    with pytest.raises(ValueError):
        ReliefSpec(style=ReliefStyle.STEPPED, levels=1).validate()


def test_validation_report_orders_severity():
    report = ValidationReport(
        findings=(
            ValidationFinding("a", ValidationSeverity.INFO, "info"),
            ValidationFinding("b", ValidationSeverity.HIGH, "high"),
        )
    )
    assert report.highest_severity == ValidationSeverity.HIGH
    assert report.has_high_risk
    assert not report.has_errors


def test_heightmap_and_female_are_derived_from_same_field(tmp_path: Path):
    source = _heightmap(tmp_path / "map.png")
    die = DieSpec()
    relief = ReliefSpec(max_relief_mm=0.45, style=ReliefStyle.STEPPED, levels=5)
    profile = adventurer_5m_profile()

    male = build_height_map(source, tmp_path, "mark", die, relief, profile)
    female_path, max_cavity, female = build_female_surface_map(male, tmp_path, "mark", die, relief)

    assert male.machine_heightmap.exists()
    assert male.male_surface_map.exists()
    assert female_path.exists()
    assert 0 < male.mm_per_sample < profile.min_feature_mm
    assert float(male.relief.max()) == pytest.approx(1.0)

    report = validate_heightfield_mating(male, female, max_cavity, die, relief)
    assert not report.has_errors


def test_light_high_polarity_reverses_mapping(tmp_path: Path):
    image = np.zeros((64, 64), dtype=np.uint8)
    image[:, 32:] = 255
    source = tmp_path / "polarity.png"
    assert cv2.imwrite(str(source), image)
    die = DieSpec(margin_mm=0.0)
    relief = ReliefSpec(
        max_relief_mm=0.3,
        style=ReliefStyle.CONTINUOUS,
        polarity=ReliefPolarity.LIGHT_HIGH,
        zero_threshold=0.0,
        auto_filter_subresolution=False,
    )
    result = build_height_map(source, tmp_path, "polarity", die, relief, None)
    cy = result.height_px // 2
    left = result.width_px // 4
    right = 3 * result.width_px // 4
    assert result.relief[cy, right] > result.relief[cy, left]
