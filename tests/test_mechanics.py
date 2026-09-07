from __future__ import annotations

import pytest

from embossforge.mechanics.spec import CartridgeSpec, PressSpec


def test_cartridge_defaults_are_self_consistent():
    spec = CartridgeSpec()
    spec.validate()
    assert spec.die_pocket_diameter_mm > spec.die_diameter_mm
    assert spec.receiver_outer_width_mm > spec.body_width_mm
    assert spec.receiver_height_mm > spec.receiver_floor_mm


def test_press_defaults_are_self_consistent():
    spec = PressSpec()
    spec.validate()
    assert spec.nominal_lever_ratio > 5
    assert spec.required_platen_travel_mm > 10
    assert spec.top_bridge_width_mm < 220
    assert spec.lever_length_mm < 220


def test_invalid_cartridge_is_rejected():
    with pytest.raises(ValueError):
        CartridgeSpec(body_width_mm=40).validate()


def test_invalid_press_gap_is_rejected():
    with pytest.raises(ValueError):
        PressSpec(closed_face_gap_mm=20, open_face_gap_mm=18).validate()


def test_roller_and_ears_fit_inside_lever():
    spec = PressSpec()
    assert spec.contact_roller_width_mm + 2 * spec.lever_ear_thickness_mm <= spec.lever_width_mm
