from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from ..micro_die import micro_butterfly_spec
from .cad import export_press_pack, mechanical_layout
from .spec import CartridgeSpec, PressSpec


def micro_press_cartridge_spec(
    *,
    slide_clearance_mm: float = 0.25,
    die_pocket_clearance_mm: float = 0.18,
) -> CartridgeSpec:
    """Cartridge sized specifically for the existing 16 mm butterfly-test dies.

    The die diameter, base thickness, key width and key depth are imported from
    ``micro_butterfly_spec`` so the press cannot silently drift away from the
    already-printed test pair. Printer-sensitive pocket/slide clearances remain
    explicit and adjustable.
    """
    die = micro_butterfly_spec()
    spec = CartridgeSpec(
        die_diameter_mm=die.diameter_mm,
        die_base_thickness_mm=die.base_thickness_mm,
        die_key_width_mm=die.key_width_mm,
        die_key_depth_mm=die.key_depth_mm,
        die_pocket_clearance_mm=die_pocket_clearance_mm,
        die_seat_recess_mm=0.05,
        body_width_mm=22.0,
        body_depth_mm=24.0,
        body_thickness_mm=3.2,
        side_rail_extension_mm=1.4,
        side_rail_height_mm=1.2,
        side_rail_center_z_mm=1.7,
        side_rail_front_setback_mm=1.5,
        side_rail_rear_setback_mm=1.5,
        receiver_slide_clearance_mm=slide_clearance_mm,
        receiver_wall_mm=1.6,
        receiver_floor_mm=1.0,
        receiver_rear_wall_mm=1.8,
        receiver_height_mm=3.9,
        front_finger_notch_radius_mm=3.5,
        front_finger_notch_depth_mm=1.3,
    )
    spec.validate()
    return spec


def micro_press_spec() -> PressSpec:
    """Very small, low-force rod-guided press for the 16 mm butterfly pair.

    This intentionally reuses the validated EmbossForge press kinematics rather
    than introducing a separate hand-modelled mechanism. It is a cheap geometry,
    alignment and usability article only; it is not a strength qualification.
    """
    spec = PressSpec(
        base_width_mm=58.0,
        base_depth_mm=65.0,
        base_thickness_mm=5.0,
        side_cheek_thickness_mm=4.5,
        side_cheek_height_mm=34.0,
        side_cheek_depth_mm=30.0,
        cheek_spacing_mm=48.0,
        pivot_diameter_mm=3.4,
        throat_depth_mm=30.0,
        lever_width_mm=11.0,
        lever_thickness_mm=5.0,
        lever_length_mm=80.0,
        lever_rear_overhang_mm=10.0,
        lever_pivot_to_platen_mm=15.0,
        contact_roller_diameter_mm=6.0,
        contact_roller_width_mm=5.5,
        contact_roller_pin_diameter_mm=2.6,
        contact_roller_drop_mm=6.2,
        contact_clearance_mm=0.20,
        lever_ear_thickness_mm=2.2,
        lever_ear_depth_mm=7.0,
        lever_ear_pin_margin_mm=0.6,
        lever_ear_overlap_mm=0.6,
        platen_ear_relief_depth_mm=0.8,
        platen_width_mm=44.0,
        platen_depth_mm=22.0,
        platen_thickness_mm=5.0,
        guide_rod_diameter_mm=3.0,
        guide_rod_spacing_mm=34.0,
        guide_rod_platen_clearance_mm=0.45,
        guide_rod_socket_clearance_mm=0.25,
        guide_rod_socket_depth_mm=3.5,
        top_bridge_depth_mm=15.0,
        top_bridge_thickness_mm=5.0,
        top_bridge_bottom_above_base_mm=34.0,
        stop_sleeve_outer_diameter_mm=6.0,
        stop_sleeve_rod_clearance_mm=0.45,
        open_face_gap_mm=5.5,
        closed_face_gap_mm=0.20,
        nominal_die_relief_mm=0.45,
        mounting_hole_diameter_mm=3.2,
        mounting_hole_edge_offset_mm=6.0,
    )
    spec.validate()
    return spec


def export_micro_press_pack(
    out_dir: str | Path,
    *,
    slide_clearance_mm: float = 0.25,
    die_pocket_clearance_mm: float = 0.18,
) -> dict[str, str]:
    """Export a tiny press that directly accepts ``butterfly-test`` dies.

    The pack deliberately does not regenerate the butterfly dies. Its purpose is
    to reuse the already-printed 16 mm male/female pair and validate a real lever
    press with as little additional material as practical.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    die = micro_butterfly_spec()
    cartridge = micro_press_cartridge_spec(
        slide_clearance_mm=slide_clearance_mm,
        die_pocket_clearance_mm=die_pocket_clearance_mm,
    )
    press = micro_press_spec()
    layout = mechanical_layout(cartridge, press)
    mechanics_dir = out / "mechanics"
    outputs = export_press_pack(mechanics_dir, cartridge=cartridge, press=press)

    # Correct generic production hardware labels emitted by export_press_pack.
    mechanics_manifest_path = Path(outputs["manifest"])
    mechanics_manifest = json.loads(mechanics_manifest_path.read_text(encoding="utf-8"))
    mechanics_manifest["status"] = (
        "Micro Embosser - exact 16 mm butterfly-test compatibility; low force only"
    )
    mechanics_manifest["hardware"]["main_pivot"]["nominal"] = (
        "M3 bolt / ~3.2-3.4 mm smooth pin"
    )
    mechanics_manifest["hardware"]["roller_pin"]["nominal"] = (
        "M2.5 bolt / ~2.5 mm smooth pin"
    )
    mechanics_manifest_path.write_text(
        json.dumps(mechanics_manifest, indent=2) + "\n", encoding="utf-8"
    )

    manifest_path = out / "micro_press_manifest.json"
    manifest = {
        "mode": "micro-butterfly-press",
        "purpose": (
            "Tiny low-force lever press for the already-printed EmbossForge 16 mm butterfly-test die pair. "
            "Validates die seating, cartridge insertion, alignment, lever motion and light embossing."
        ),
        "strength_status": "prototype / low force only",
        "compatible_die_command": "embossforge butterfly-test",
        "exact_die_contract_mm": {
            "diameter": die.diameter_mm,
            "base_thickness": die.base_thickness_mm,
            "key_width": die.key_width_mm,
            "key_depth": die.key_depth_mm,
            "nominal_relief": die.relief_height_mm,
        },
        "fit_clearances_mm": {
            "die_pocket_per_side": die_pocket_clearance_mm,
            "cartridge_receiver_per_side": slide_clearance_mm,
        },
        "nominal_dimensions_mm": {
            "base": [press.base_width_mm, press.base_depth_mm, press.base_thickness_mm],
            "lever_length": press.lever_length_mm,
            "cartridge_body": [
                cartridge.body_width_mm,
                cartridge.body_depth_mm,
                cartridge.body_thickness_mm,
            ],
            "guide_rod_diameter": press.guide_rod_diameter_mm,
            "guide_rod_length": layout["guide_rod_length"],
            "pivot_bore": press.pivot_diameter_mm,
            "roller_pin_bore": press.contact_roller_pin_diameter_mm,
            "nominal_lever_ratio": press.nominal_lever_ratio,
        },
        "recommended_print_order": [
            "1) Print ONE cartridge.stl first and confirm the existing 16 mm butterfly die drops into the keyed pocket without force.",
            "2) If the die fit is good, print the second cartridge plus the two receivers and confirm sliding fit.",
            "3) Only then print the base, cheeks, bridge, platen, lever, roller and stops.",
        ],
        "assembly_notes": [
            "Male die goes in the lower cartridge; female die goes in the upper cartridge.",
            "Keep the rectangular die key seated in the matching cartridge key pocket; do not rotate either die independently.",
            "The upper cartridge/receiver is installed flipped by the same transform used by the full EmbossForge press.",
            "Use two 3 mm smooth guide rods, one M3-class main pivot, and one M2.5-class roller pin.",
            "Start with ordinary paper and very light lever force. This micro press is not intended for strength testing.",
        ],
        "press_spec": asdict(press),
        "cartridge_spec": asdict(cartridge),
        "mechanics_outputs": outputs,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    result = dict(outputs)
    result["micro_manifest"] = str(manifest_path)
    return result
