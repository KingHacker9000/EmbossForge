from pathlib import Path
import struct

import cv2
import numpy as np
import pytest

from embossforge.config import DieSpec, adventurer_5m_profile
from embossforge.heightmap import HeightMapResult, build_female_surface_map, build_height_map
from embossforge.relief import ReliefPolarity, ReliefSpec, ReliefStyle, ValidationFinding, ValidationReport, ValidationSeverity
from embossforge.relief_backend import _female_scad, _surface_module
from embossforge.scad_backend import _stl_has_triangles
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
    assert spec.levels == 4
    assert spec.max_relief_mm == pytest.approx(1.20)
    assert spec.min_relief_mm == pytest.approx(0.40)
    assert spec.polarity == ReliefPolarity.DARK_HIGH

    with pytest.raises(ValueError):
        ReliefSpec(style=ReliefStyle.STEPPED, levels=1).validate()
    with pytest.raises(ValueError):
        ReliefSpec(max_relief_mm=0.4, min_relief_mm=0.4).validate()


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
    die = DieSpec(female_extra_depth_mm=0.03)
    relief = ReliefSpec(max_relief_mm=1.2, min_relief_mm=0.4, style=ReliefStyle.STEPPED, levels=4)
    profile = adventurer_5m_profile()

    male = build_height_map(source, tmp_path, "mark", die, relief, profile)
    female_path, max_cavity, female = build_female_surface_map(male, tmp_path, "mark", die, relief)

    assert male.machine_heightmap.exists()
    assert male.male_surface_map.exists()
    assert female_path.exists()
    assert 0 < male.mm_per_sample < profile.min_feature_mm
    assert float(male.relief.max()) == pytest.approx(1.0)
    assert max_cavity == pytest.approx(1.23)

    report = validate_heightfield_mating(male, female, max_cavity, die, relief)
    assert not report.has_errors


def test_stepped_relief_never_quantizes_active_tones_below_print_floor(tmp_path: Path):
    image = np.full((64, 64), 255, dtype=np.uint8)
    image[16:48, 8:24] = 220
    image[16:48, 24:40] = 128
    image[16:48, 40:56] = 0
    source = tmp_path / "tiers.png"
    assert cv2.imwrite(str(source), image)

    die = DieSpec(margin_mm=0.0)
    relief = ReliefSpec(
        max_relief_mm=1.2,
        min_relief_mm=0.4,
        style=ReliefStyle.STEPPED,
        levels=4,
        zero_threshold=0.02,
        auto_filter_subresolution=False,
    )
    result = build_height_map(source, tmp_path, "tiers", die, relief, None)
    physical = result.relief * relief.max_relief_mm
    active_values = np.unique(np.round(physical[physical > 0], 4))
    assert set(active_values.tolist()).issubset({0.4, 0.8, 1.2})
    assert active_values.min() >= 0.4
    assert active_values.max() == pytest.approx(1.2)


def test_female_cavity_uses_extra_depth_not_paper_thickness(tmp_path: Path):
    source = _heightmap(tmp_path / "map.png")
    relief = ReliefSpec(max_relief_mm=1.2, min_relief_mm=0.4, style=ReliefStyle.STEPPED, levels=4)

    thin = DieSpec(paper_thickness_mm=0.10, female_extra_depth_mm=0.03)
    thick = DieSpec(paper_thickness_mm=0.25, female_extra_depth_mm=0.03)
    male_thin = build_height_map(source, tmp_path / "thin", "mark", thin, relief, None)
    male_thick = build_height_map(source, tmp_path / "thick", "mark", thick, relief, None)
    _, thin_depth, _ = build_female_surface_map(male_thin, tmp_path / "thin", "mark", thin, relief)
    _, thick_depth, _ = build_female_surface_map(male_thick, tmp_path / "thick", "mark", thick, relief)
    assert thin_depth == pytest.approx(1.23)
    assert thick_depth == pytest.approx(1.23)


def test_heightfield_validator_rejects_old_double_counted_paper_gap(tmp_path: Path):
    source = _heightmap(tmp_path / "map.png")
    die = DieSpec(paper_thickness_mm=0.10, female_extra_depth_mm=0.03)
    relief = ReliefSpec(max_relief_mm=1.2, min_relief_mm=0.4)
    male = build_height_map(source, tmp_path, "mark", die, relief, None)

    # Simulate the historical bug: max cavity had paper thickness added again.
    bad_max = relief.max_relief_mm + die.female_extra_depth_mm + die.paper_thickness_mm
    bad_field = np.fliplr(
        np.where(male.relief > 0, (male.relief * relief.max_relief_mm + die.female_extra_depth_mm + die.paper_thickness_mm) / bad_max, 0.0)
    ).astype(np.float32)
    report = validate_heightfield_mating(male, bad_field, bad_max, die, relief)
    assert report.has_errors
    assert any(f.code == "mating.excess_or_missing_z_allowance" for f in report.findings)


def test_light_high_polarity_reverses_mapping(tmp_path: Path):
    image = np.zeros((64, 64), dtype=np.uint8)
    image[:, 32:] = 255
    source = tmp_path / "polarity.png"
    assert cv2.imwrite(str(source), image)
    die = DieSpec(margin_mm=0.0)
    relief = ReliefSpec(
        max_relief_mm=0.6,
        min_relief_mm=0.0,
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


def test_openscad_surface_scale_uses_native_zero_to_100_range(tmp_path: Path):
    image = tmp_path / "surface.png"
    assert cv2.imwrite(str(image), np.array([[0, 255], [255, 0]], dtype=np.uint8))
    result = HeightMapResult(
        relief=np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        machine_heightmap=image,
        male_surface_map=image,
        width_px=2,
        height_px=2,
        mm_per_sample=1.0,
    )
    scad = _surface_module(image, result, DieSpec(), 0.65)
    assert "0.00650000" in scad


def test_female_cutter_has_non_degenerate_backing_slab(tmp_path: Path):
    image = tmp_path / "surface.png"
    assert cv2.imwrite(str(image), np.array([[0, 255], [255, 0]], dtype=np.uint8))
    result = HeightMapResult(
        relief=np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        machine_heightmap=image,
        male_surface_map=image,
        width_px=2,
        height_px=2,
        mm_per_sample=1.0,
    )
    scad = _female_scad(result, image, 1.25, DieSpec())
    assert "cutter_eps = 0.0200" in scad
    assert "cube([art_box, art_box, cutter_eps]" in scad
    assert "base_h + cutter_eps" in scad


def test_empty_ascii_stl_is_rejected(tmp_path: Path):
    empty = tmp_path / "empty.stl"
    empty.write_text("solid OpenSCAD_Model\nendsolid OpenSCAD_Model\n", encoding="ascii")
    assert not _stl_has_triangles(empty)

    populated = tmp_path / "populated.stl"
    populated.write_text(
        "solid x\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid x\n",
        encoding="ascii",
    )
    assert _stl_has_triangles(populated)


def test_binary_stl_triangle_count_is_checked(tmp_path: Path):
    empty = tmp_path / "empty-binary.stl"
    empty.write_bytes(b"x" * 80 + struct.pack("<I", 0))
    assert not _stl_has_triangles(empty)

    populated = tmp_path / "one-triangle.stl"
    populated.write_bytes(b"x" * 80 + struct.pack("<I", 1) + b"\x00" * 50)
    assert _stl_has_triangles(populated)
