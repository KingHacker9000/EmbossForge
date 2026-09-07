from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from ..config import DieSpec
from ..scad_backend import generate_die_pair
from .cad import export_press_pack, mechanical_layout
from .spec import CartridgeSpec, PressSpec


MINI_TEST_ARTWORK = """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"-10 -10 20 20\">\n  <circle cx=\"0\" cy=\"0\" r=\"7\" fill=\"none\" stroke=\"black\" stroke-width=\"1.8\"/>\n  <rect x=\"-1.25\" y=\"-5.5\" width=\"2.5\" height=\"11\" fill=\"black\"/>\n  <rect x=\"-5.5\" y=\"-1.25\" width=\"11\" height=\"2.5\" fill=\"black\"/>\n</svg>\n"""


def mini_cartridge_spec(*, slide_clearance_mm: float = 0.25) -> CartridgeSpec:
    """Return the filament-saving functional-test cartridge geometry.

    This is intentionally *not* a uniform scale of the production cartridge.
    Macro dimensions are reduced aggressively while printer-fit clearances stay
    at realistic absolute values so the test remains useful on the same FDM
    printer/nozzle.
    """
    spec = CartridgeSpec(
        die_diameter_mm=18.0,
        die_base_thickness_mm=2.2,
        die_key_width_mm=3.5,
        die_key_depth_mm=1.8,
        die_pocket_clearance_mm=0.15,
        die_seat_recess_mm=0.05,
        body_width_mm=26.0,
        body_depth_mm=30.0,
        body_thickness_mm=3.8,
        side_rail_extension_mm=1.8,
        side_rail_height_mm=1.6,
        side_rail_center_z_mm=2.0,
        side_rail_front_setback_mm=1.8,
        side_rail_rear_setback_mm=1.8,
        receiver_slide_clearance_mm=slide_clearance_mm,
        receiver_wall_mm=2.0,
        receiver_floor_mm=1.1,
        receiver_rear_wall_mm=2.2,
        receiver_height_mm=4.4,
        front_finger_notch_radius_mm=4.0,
        front_finger_notch_depth_mm=1.8,
    )
    spec.validate()
    return spec


def mini_press_spec() -> PressSpec:
    """Return a low-force miniature of the V0.2 press architecture.

    The mini press preserves the same kinematic layout (base, two cheeks,
    guide rods, platen, roller, lever, receivers and hard stops) but shrinks the
    force-bearing envelope enough to be a cheap throwaway geometry test. It is
    not a strength qualification article for the full-size press.
    """
    spec = PressSpec(
        base_width_mm=72.0,
        base_depth_mm=80.0,
        base_thickness_mm=6.0,
        side_cheek_thickness_mm=5.0,
        side_cheek_height_mm=42.0,
        side_cheek_depth_mm=38.0,
        cheek_spacing_mm=60.0,
        pivot_diameter_mm=4.2,
        throat_depth_mm=37.0,
        lever_width_mm=14.0,
        lever_thickness_mm=6.0,
        lever_length_mm=95.0,
        lever_rear_overhang_mm=12.0,
        lever_pivot_to_platen_mm=18.0,
        contact_roller_diameter_mm=7.0,
        contact_roller_width_mm=7.5,
        contact_roller_pin_diameter_mm=3.2,
        contact_roller_drop_mm=7.0,
        contact_clearance_mm=0.20,
        lever_ear_thickness_mm=3.0,
        lever_ear_depth_mm=9.0,
        lever_ear_pin_margin_mm=0.7,
        lever_ear_overlap_mm=0.7,
        platen_ear_relief_depth_mm=1.0,
        platen_width_mm=56.0,
        platen_depth_mm=26.0,
        platen_thickness_mm=6.0,
        guide_rod_diameter_mm=4.0,
        guide_rod_spacing_mm=44.0,
        guide_rod_platen_clearance_mm=0.50,
        guide_rod_socket_clearance_mm=0.25,
        guide_rod_socket_depth_mm=4.0,
        top_bridge_depth_mm=18.0,
        top_bridge_thickness_mm=6.0,
        top_bridge_bottom_above_base_mm=42.0,
        stop_sleeve_outer_diameter_mm=7.5,
        stop_sleeve_rod_clearance_mm=0.50,
        open_face_gap_mm=7.0,
        closed_face_gap_mm=0.20,
        nominal_die_relief_mm=0.45,
        mounting_hole_diameter_mm=3.2,
        mounting_hole_edge_offset_mm=7.0,
    )
    spec.validate()
    return spec


def mini_die_spec(*, paper_thickness_mm: float = 0.10) -> DieSpec:
    spec = DieSpec(
        diameter_mm=18.0,
        base_thickness_mm=2.2,
        relief_height_mm=0.45,
        female_xy_clearance_mm=0.20,
        female_extra_depth_mm=0.15,
        paper_thickness_mm=paper_thickness_mm,
        margin_mm=1.5,
        facets=80,
        key_width_mm=3.5,
        key_depth_mm=1.8,
    )
    spec.validate()
    return spec


def export_mini_test_pack(
    out_dir: str | Path,
    *,
    slide_clearance_mm: float = 0.25,
    paper_thickness_mm: float = 0.10,
) -> dict[str, str]:
    """Generate a miniature, low-filament, functionally representative pack."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cartridge = mini_cartridge_spec(slide_clearance_mm=slide_clearance_mm)
    press = mini_press_spec()
    die = mini_die_spec(paper_thickness_mm=paper_thickness_mm)
    layout = mechanical_layout(cartridge, press)

    mechanics_dir = out / "mechanics"
    die_dir = out / "die"
    mechanics = export_press_pack(mechanics_dir, cartridge=cartridge, press=press)

    # export_press_pack describes the production default M6/M5 hardware by name.
    # The miniature deliberately uses smaller bores, so correct those labels in
    # the mini mechanics manifest while retaining the dimensions generated by
    # the same source model.
    mechanics_manifest_path = Path(mechanics["manifest"])
    mechanics_manifest = json.loads(mechanics_manifest_path.read_text(encoding="utf-8"))
    mechanics_manifest["status"] = "Mini functional throwaway prototype - low force only"
    mechanics_manifest["hardware"]["main_pivot"]["nominal"] = "M4 bolt or ~4 mm smooth pin"
    mechanics_manifest["hardware"]["roller_pin"]["nominal"] = "M3 bolt or ~3 mm smooth pin"
    mechanics_manifest_path.write_text(json.dumps(mechanics_manifest, indent=2) + "\n", encoding="utf-8")

    die_dir.mkdir(parents=True, exist_ok=True)
    artwork = die_dir / "mini_test_mark.svg"
    artwork.write_text(MINI_TEST_ARTWORK, encoding="utf-8")
    dies = generate_die_pair(artwork, die_dir, "mini_test", die, render_stl=True)

    manifest_path = out / "mini_test_manifest.json"
    manifest = {
        "mode": "mini-functional-throwaway",
        "purpose": (
            "Low-filament test of assembly, motion, cartridge insertion, alignment and light embossing. "
            "It is not a strength validation of the full-size press."
        ),
        "not_uniform_scale": True,
        "critical_absolute_dimensions_preserved": {
            "cartridge_receiver_slide_clearance_mm": slide_clearance_mm,
            "die_pocket_clearance_mm": cartridge.die_pocket_clearance_mm,
            "female_xy_clearance_mm": die.female_xy_clearance_mm,
            "paper_thickness_mm": paper_thickness_mm,
        },
        "nominal_dimensions_mm": {
            "base": [press.base_width_mm, press.base_depth_mm, press.base_thickness_mm],
            "die_diameter": die.diameter_mm,
            "cartridge_body": [cartridge.body_width_mm, cartridge.body_depth_mm, cartridge.body_thickness_mm],
            "guide_rod_diameter": press.guide_rod_diameter_mm,
            "guide_rod_length": layout["guide_rod_length"],
            "pivot_bore_diameter": press.pivot_diameter_mm,
            "roller_pin_bore_diameter": press.contact_roller_pin_diameter_mm,
            "lever_length": press.lever_length_mm,
            "nominal_lever_ratio": press.nominal_lever_ratio,
        },
        "recommended_print_order": [
            "1) cartridge.stl + receiver.stl only; verify slide fit before spending more filament",
            "2) mini_test_male.stl + mini_test_female.stl; verify die seating and light paper emboss",
            "3) remaining miniature press parts",
        ],
        "budget_slicer_starting_point": {
            "layer_height_mm": 0.20,
            "walls": 2,
            "top_layers": 3,
            "bottom_layers": 3,
            "infill_percent": 6,
            "note": "Use the slicer's filament-grams estimate before printing. Increase walls/infill only if the throwaway model is too flexible.",
        },
        "hardware_note": (
            "For a working low-force test, use two 4 mm smooth guide rods (length in this manifest), "
            "an approximately 4 mm main pivot pin/bolt, and an approximately 3 mm roller pin/bolt. "
            "Do not use the miniature for high-force embossing."
        ),
        "cartridge_spec": asdict(cartridge),
        "press_spec": asdict(press),
        "die_spec": asdict(die),
        "mechanics_outputs": mechanics,
        "die_outputs": {key: str(value) for key, value in dies.items()},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    outputs = {f"mechanics_{key}": value for key, value in mechanics.items()}
    outputs.update({f"die_{key}": str(value) for key, value in dies.items()})
    outputs["artwork"] = str(artwork)
    outputs["mini_manifest"] = str(manifest_path)
    return outputs
