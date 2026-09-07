from __future__ import annotations

import pytest

from embossforge.mechanics.spec import CartridgeSpec, PressSpec


def test_cartridge_defaults_are_self_consistent():
    spec = CartridgeSpec()
    spec.validate()
    assert spec.die_pocket_diameter_mm > spec.die_diameter_mm
    assert spec.receiver_width_mm > spec.outer_width_mm


def test_press_defaults_are_self_consistent():
    spec = PressSpec()
    spec.validate()
    assert spec.nominal_lever_ratio > 5


def test_invalid_cartridge_is_rejected():
    with pytest.raises(ValueError):
        CartridgeSpec(outer_width_mm=40).validate()


def test_invalid_press_gap_is_rejected():
    with pytest.raises(ValueError):
        PressSpec(minimum_closed_gap_mm=20, open_die_gap_mm=18).validate()
