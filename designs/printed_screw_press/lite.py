"""Lightweight functional commissioning build of the Astra/Codex screw press.

This keeps the production mechanism, 42 mm die interface, guide, power thread,
and mating geometry, but intentionally targets a cheap first functional article.
The mechanism is not scaled. Material savings come from a smaller handwheel and
low infill with enough walls around load paths and threads.

This is a low-force commissioning article, not a 300-500 N rated press.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cadquery as cq

import model

DEFAULT_OUT = model.ROOT / "build" / "printed_screw_press_lite"


def build_lite_power_screw_wheel():
    """Production power screw/foot with a smaller 120 mm handwheel."""
    power = model.thread(28, 6, 80).translate((0, 0, 14))
    power = power.union(model.cyl(8, 8, (0, 0, 6)))

    foot = model.cyl(12, 2)
    foot = foot.union(
        cq.Workplane("XY")
        .workplane(offset=2)
        .circle(12)
        .workplane(offset=4)
        .circle(8)
        .loft()
    )
    power = power.union(foot)

    wheel = model.cyl(60, 10, (0, 0, 94)).cut(model.cyl(49, 12, (0, 0, 93)))
    wheel = wheel.union(model.cyl(23, 10, (0, 0, 94)))
    for angle in (0, 60, 120):
        spoke = model.box(110, 14, 10, (0, 0, 94)).rotate(
            (0, 0, 0), (0, 0, 1), angle
        )
        wheel = wheel.union(spoke)

    return power.union(wheel)


def build_lite_parts():
    parts = model.build()
    parts["04_power_screw_wheel"] = build_lite_power_screw_wheel()
    return parts


def print_plan():
    # Empirical note: the user's compact production-profile thread coupon printed
    # cleanly at 15% infill. For the commissioning build we therefore use wall
    # count as the primary strength control and keep infill sparse.
    return {
        "purpose": "cheap low-force functional commissioning prototype",
        "external_hardware_required": 0,
        "existing_42mm_dies_compatible": True,
        "not_a_load_rating": True,
        "stop_if_slicer_total_exceeds_g": 250,
        "global": {
            "material": "ordinary PLA",
            "nozzle_mm": 0.4,
            "scale_percent": 100,
            "supports": "off unless a local accessible area clearly needs them",
            "note": "Use exported orientations. Prefer walls over infill. This is a prototype, not a proof-load machine.",
        },
        "parts": {
            "01_frame_left": {"layer_mm": 0.28, "walls": 4, "infill_percent": 10, "infill": "grid", "top_bottom_layers": 5},
            "02_frame_right": {"layer_mm": 0.28, "walls": 4, "infill_percent": 10, "infill": "grid", "top_bottom_layers": 5},
            "03_power_nut": {"layer_mm": 0.20, "walls": 5, "infill_percent": 15, "infill": "grid"},
            "04_power_screw_wheel": {"layer_mm": 0.20, "walls": 5, "infill_percent": 15, "infill": "grid", "top_bottom_layers": 5},
            "05_guided_ram": {"layer_mm": 0.24, "walls": 4, "infill_percent": 12, "infill": "grid", "top_bottom_layers": 5},
            "06_tray_lower": {"layer_mm": 0.20, "walls": 4, "infill_percent": 15, "infill": "grid", "top_bottom_layers": 5},
            "07_tray_upper": {"layer_mm": 0.20, "walls": 4, "infill_percent": 15, "infill": "grid", "top_bottom_layers": 5},
            "08_die_clamp_wedge": {"layer_mm": 0.20, "walls": 4, "infill_percent": 15, "infill": "grid"},
            "09_die_clamp_screw": {"layer_mm": 0.16, "walls": 4, "infill_percent": 20, "infill": "grid"},
            "10_foot_keeper": {"layer_mm": 0.20, "walls": 4, "infill_percent": 10, "infill": "grid"},
            "11_keeper_screw": {"layer_mm": 0.16, "walls": 4, "infill_percent": 20, "infill": "grid"},
            "12_guide_adjuster": {"layer_mm": 0.20, "walls": 4, "infill_percent": 15, "infill": "grid", "brim_mm": 6},
            "13_tray_retainer": {"layer_mm": 0.16, "walls": 4, "infill_percent": 20, "infill": "grid"},
            "14_frame_tie_bolt": {"layer_mm": 0.20, "walls": 4, "infill_percent": 15, "infill": "grid", "brim_mm": 6},
            "15_frame_tie_nut": {"layer_mm": 0.20, "walls": 4, "infill_percent": 15, "infill": "grid"},
            "16_alignment_gauge_TOOL": {"layer_mm": 0.28, "walls": 2, "infill_percent": 5, "infill": "grid"},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    print("Building cheap lightweight functional screw-press prototype...", flush=True)
    parts = build_lite_parts()
    model.export(parts, args.out)

    plan = print_plan()
    (args.out / "LITE_PRINT_PLAN.json").write_text(json.dumps(plan, indent=2))
    (args.out / "START_LITE.txt").write_text(
        "CHEAP LIGHTWEIGHT FUNCTIONAL COMMISSIONING BUILD\n\n"
        "External hardware: 0. Existing standard 42 mm keyed dies are compatible.\n"
        "The mechanism is full size; do not scale any STL. The handwheel is 120 mm diameter.\n"
        "This variant deliberately uses sparse infill and relies on 4-5 walls for local strength.\n"
        "The user's production-profile thread coupon printed cleanly at 15% infill, so 100% infill is not required for this commissioning article.\n"
        "Use LITE_PRINT_PLAN.json for per-part settings.\n\n"
        "IMPORTANT: if FlashPrint estimates more than 250 g total for the complete mechanism, STOP and do not print it; the CAD should be skeletonized further instead of wasting filament.\n"
        "This build is for fit, motion, alignment, die retention, reopening and light paper emboss trials only. It is not rated for the original 300-500 N target.\n"
        "Do not use a handle extension, drill, hammer or body weight.\n"
    )
    print(f"Lite press exported to: {args.out}")
    print(f"Print plan: {args.out / 'LITE_PRINT_PLAN.json'}")
    print("STOP if the complete slicer estimate exceeds 250 g; reduce CAD mass before printing.")


if __name__ == "__main__":
    main()
