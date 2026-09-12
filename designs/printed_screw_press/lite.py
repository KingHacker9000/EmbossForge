"""Lightweight functional commissioning build of the Astra/Codex screw press.

The mechanism, die trays, guide, power thread, frame envelope, and all mating
interfaces remain the same as Revision A. Material is reduced primarily by the
recommended slicer settings, not by shrinking load-bearing interfaces. The only
CAD change is a smaller 120 mm handwheel, which reduces plastic and increases
required hand force by 80/60 = 1.333x for the same screw output force.

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
    """Production power screw/foot with a smaller, lighter handwheel."""
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

    # Revision A used an 80 mm handwheel radius. The lite wheel keeps the same
    # 10 mm thickness and robust central hub but trims radius to 60 mm.
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
    return {
        "purpose": "low-force functional commissioning prototype",
        "external_hardware_required": 0,
        "existing_42mm_dies_compatible": True,
        "not_a_load_rating": True,
        "global": {
            "material": "ordinary PLA",
            "nozzle_mm": 0.4,
            "scale_percent": 100,
            "note": "Use the exported orientations. Keep supports off unless the layer preview shows a local accessible failure area.",
        },
        "parts": {
            "01_frame_left": {"layer_mm": 0.24, "walls": 5, "infill_percent": 15, "infill": "grid", "top_bottom_layers": 6},
            "02_frame_right": {"layer_mm": 0.24, "walls": 5, "infill_percent": 15, "infill": "grid", "top_bottom_layers": 6},
            "03_power_nut": {"layer_mm": 0.16, "walls": 6, "infill_percent": 100, "infill": "solid"},
            "04_power_screw_wheel": {"layer_mm": 0.16, "walls": 6, "infill_percent": 35, "infill": "grid", "top_bottom_layers": 6},
            "05_guided_ram": {"layer_mm": 0.20, "walls": 5, "infill_percent": 20, "infill": "grid", "top_bottom_layers": 6},
            "06_tray_lower": {"layer_mm": 0.20, "walls": 5, "infill_percent": 30, "infill": "grid", "top_bottom_layers": 6},
            "07_tray_upper": {"layer_mm": 0.20, "walls": 5, "infill_percent": 30, "infill": "grid", "top_bottom_layers": 6},
            "08_die_clamp_wedge": {"layer_mm": 0.20, "walls": 5, "infill_percent": 100, "infill": "solid"},
            "09_die_clamp_screw": {"layer_mm": 0.16, "walls": 6, "infill_percent": 100, "infill": "solid"},
            "10_foot_keeper": {"layer_mm": 0.20, "walls": 5, "infill_percent": 100, "infill": "solid"},
            "11_keeper_screw": {"layer_mm": 0.16, "walls": 6, "infill_percent": 100, "infill": "solid"},
            "12_guide_adjuster": {"layer_mm": 0.16, "walls": 6, "infill_percent": 100, "infill": "solid", "brim_mm": 6},
            "13_tray_retainer": {"layer_mm": 0.16, "walls": 6, "infill_percent": 100, "infill": "solid"},
            "14_frame_tie_bolt": {"layer_mm": 0.20, "walls": 6, "infill_percent": 100, "infill": "solid", "brim_mm": 6},
            "15_frame_tie_nut": {"layer_mm": 0.16, "walls": 6, "infill_percent": 100, "infill": "solid"},
            "16_alignment_gauge_TOOL": {"layer_mm": 0.20, "walls": 3, "infill_percent": 15, "infill": "grid"},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    print("Building lightweight functional screw-press prototype...", flush=True)
    parts = build_lite_parts()
    model.export(parts, args.out)

    plan = print_plan()
    (args.out / "LITE_PRINT_PLAN.json").write_text(json.dumps(plan, indent=2))
    (args.out / "START_LITE.txt").write_text(
        "LIGHTWEIGHT FUNCTIONAL COMMISSIONING BUILD\n\n"
        "This keeps the production frame/ram/tray/thread interfaces and your existing 42 mm dies.\n"
        "The handwheel is reduced from 160 mm to 120 mm diameter. For the same screw output force, "
        "hand force is therefore about 1.33x the Revision A estimate.\n"
        "Use LITE_PRINT_PLAN.json for per-part slicer settings. This article is for mechanism, fit, "
        "alignment, reopening and light paper-emboss trials. It is NOT qualified for the full "
        "300-500 N design target. Do not use a handle extension, drill, hammer, or body weight.\n"
        "Use your existing standard 42 mm keyed dies; no new die pair is required.\n"
    )
    print(f"Lite press exported to: {args.out}")
    print(f"Print plan: {args.out / 'LITE_PRINT_PLAN.json'}")


if __name__ == "__main__":
    main()
