from __future__ import annotations

import pytest

pytest.importorskip("cadquery")

from embossforge.mechanics.cad import (
    build_cartridge,
    build_press_parts,
    build_receiver,
    mechanical_layout,
    validate_assembly_clearance,
)
from embossforge.mechanics.spec import CartridgeSpec, PressSpec


def test_cartridge_and_receiver_are_valid_solids():
    cartridge = CartridgeSpec()
    carrier = build_cartridge(cartridge).val()
    receiver = build_receiver(cartridge).val()
    assert carrier.isValid()
    assert receiver.isValid()
    assert carrier.Volume() > 0
    assert receiver.Volume() > 0


def test_default_cartridge_slides_into_receiver_without_intersection():
    spec = CartridgeSpec()
    carrier = build_cartridge(spec).translate((0, 0, spec.receiver_floor_mm))
    receiver = build_receiver(spec)
    assert carrier.intersect(receiver).val().Volume() == pytest.approx(0.0, abs=1e-6)


def test_default_press_parts_fit_ad5m_build_volume_individually():
    cartridge = CartridgeSpec()
    press = PressSpec()
    for name, part in build_press_parts(cartridge, press).items():
        box = part.val().BoundingBox()
        assert box.xlen <= 220, name
        assert box.ylen <= 220, name
        assert box.zlen <= 220, name


def test_default_open_and_closed_assemblies_have_no_printed_part_collisions():
    report = validate_assembly_clearance(CartridgeSpec(), PressSpec())
    assert report == {"open": [], "closed": []}


def test_layout_has_expected_motion_and_hardware_scale():
    layout = mechanical_layout(CartridgeSpec(), PressSpec())
    assert layout["platen_open_bottom_z"] > layout["platen_closed_bottom_z"]
    assert layout["lever_open_angle_deg"] > 0
    assert 90 <= layout["guide_rod_length"] <= 110
