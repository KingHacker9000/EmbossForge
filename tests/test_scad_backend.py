from pathlib import Path

from embossforge.config import DieSpec
from embossforge.scad_backend import _female_scad, _male_scad


def test_male_scad_uses_relief_height():
    scad = _male_scad(Path("mark.svg"), DieSpec(relief_height_mm=0.7))
    assert "relief_h = 0.7000;" in scad
    assert "linear_extrude(height=relief_h)" in scad


def test_female_scad_adds_clearance_and_mirror():
    scad = _female_scad(Path("mark.svg"), DieSpec(female_xy_clearance_mm=0.22))
    assert "offset(delta=0.2200)" in scad
    assert "mirror([0, 1, 0])" in scad
