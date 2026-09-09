from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from .cad import export_part
from .handheld_compact import standard_handheld_die_spec
from .handheld_elegant import (
    PLA_DENSITY_G_CM3,
    build_elegant_assembly,
    build_elegant_body,
    build_elegant_lever,
    build_elegant_upper_cap,
    build_elegant_upper_carriage,
    elegant_lever_spec,
)


DEFAULT_TEST_SCALE = 2.0 / 3.0


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            'CadQuery is required for press generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


def _scaled(part: Any, factor: float):
    cq = _cq()
    if not 0.50 <= factor <= 0.80:
        raise ValueError("test press scale must be between 0.50 and 0.80")
    return cq.Workplane(obj=part.val().scale(factor))


def _solid_mass_g(part: Any) -> float:
    return float(part.val().Volume()) / 1000.0 * PLA_DENSITY_G_CM3


def _test_die_base(*, scale: float = DEFAULT_TEST_SCALE):
    """Low-cost keyed carrier that fits the uniformly scaled press pocket.

    The full 42 mm die contract is intentionally not used here. This throwaway
    test carrier is slightly undersized relative to the scaled pocket so a
    0.4 mm-nozzle prototype is not ruined by an overly tight 0.10 mm scaled fit.
    """
    cq = _cq()
    full_die = standard_handheld_die_spec()
    diameter = full_die.diameter_mm * scale - 0.20
    base_h = full_die.base_thickness_mm * scale
    key_width = full_die.key_width_mm * scale - 0.10
    key_depth = full_die.key_depth_mm * scale - 0.15
    overlap = 0.5 * scale
    tab_depth = key_depth + overlap
    tab_y = diameter / 2.0 + (key_depth - overlap) / 2.0

    disc = cq.Workplane("XY").circle(diameter / 2.0).extrude(base_h)
    tab = (
        cq.Workplane("XY")
        .center(0, tab_y)
        .rect(key_width, tab_depth)
        .extrude(base_h)
    )
    return disc.union(tab), {
        "diameter_mm": diameter,
        "base_thickness_mm": base_h,
        "key_width_mm": key_width,
        "key_depth_mm": key_depth,
    }


def build_test_male_die(*, scale: float = DEFAULT_TEST_SCALE):
    """Simple annular male die for fit, motion, and low-force paper testing."""
    cq = _cq()
    carrier, dims = _test_die_base(scale=scale)
    base_h = dims["base_thickness_mm"]
    ridge = (
        cq.Workplane("XY")
        .circle(7.0 * scale / DEFAULT_TEST_SCALE)
        .circle(5.4 * scale / DEFAULT_TEST_SCALE)
        .extrude(0.80 * scale / DEFAULT_TEST_SCALE)
        .translate((0, 0, base_h))
    )
    return carrier.union(ridge)


def build_test_female_die(*, scale: float = DEFAULT_TEST_SCALE):
    """Permissive annular female mate for the throwaway male test die."""
    cq = _cq()
    carrier, dims = _test_die_base(scale=scale)
    base_h = dims["base_thickness_mm"]
    groove_depth = 0.95 * scale / DEFAULT_TEST_SCALE
    outer = 7.30 * scale / DEFAULT_TEST_SCALE
    inner = 5.10 * scale / DEFAULT_TEST_SCALE
    groove = (
        cq.Workplane("XY")
        .circle(outer)
        .circle(inner)
        .extrude(groove_depth + 0.05)
        .translate((0, 0, base_h - groove_depth))
    )
    return carrier.cut(groove)


def build_elegant_test_parts(*, scale: float = DEFAULT_TEST_SCALE) -> dict[str, Any]:
    """Return a uniformly scaled motion-test version of the V3 elegant press."""
    spec = elegant_lever_spec()
    die = standard_handheld_die_spec()
    return {
        "body": _scaled(build_elegant_body(spec, die), scale),
        "upper_carriage": _scaled(build_elegant_upper_carriage(spec, die), scale),
        "upper_backing_cap": _scaled(build_elegant_upper_cap(spec, die), scale),
        "lever": _scaled(build_elegant_lever(spec), scale),
        "test_male_die": build_test_male_die(scale=scale),
        "test_female_die": build_test_female_die(scale=scale),
    }


def validate_elegant_test_clearance(*, scale: float = DEFAULT_TEST_SCALE) -> dict[str, list[tuple[str, str, float]]]:
    """Uniform scaling preserves the full-size assembly's clearance relationships."""
    report: dict[str, list[tuple[str, str, float]]] = {}
    for state in ("closed", "open"):
        assembly = build_elegant_assembly(state=state)
        parts = {name: _scaled(part, scale) for name, part in assembly.items()}
        names = list(parts)
        collisions: list[tuple[str, str, float]] = []
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                try:
                    volume = float(parts[left].intersect(parts[right]).val().Volume())
                except Exception:
                    volume = 0.0
                if volume > 1e-3:
                    collisions.append((left, right, volume))
        report[state] = collisions
    return report


def export_elegant_test_press_pack(
    out_dir: str | Path,
    *,
    scale: float = DEFAULT_TEST_SCALE,
) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    parts = build_elegant_test_parts(scale=scale)

    collisions = validate_elegant_test_clearance(scale=scale)
    if collisions["closed"] or collisions["open"]:
        raise RuntimeError(
            "Scaled elegant test press contains unintended printed-part collisions:\n"
            + json.dumps(collisions, indent=2)
        )

    outputs: dict[str, str] = {}
    for name, part in parts.items():
        outputs[f"{name}_stl"] = str(export_part(part, out / f"{name}.stl"))
        outputs[f"{name}_step"] = str(export_part(part, out / f"{name}.step"))

    masses = {name: round(_solid_mass_g(part), 2) for name, part in parts.items()}
    full_parts = {
        "body": build_elegant_body(),
        "upper_carriage": build_elegant_upper_carriage(),
        "upper_backing_cap": build_elegant_upper_cap(),
        "lever": build_elegant_lever(),
    }
    full_mass = sum(_solid_mass_g(part) for part in full_parts.values())
    scaled_press_mass = sum(masses[name] for name in full_parts)
    die_dims = _test_die_base(scale=scale)[1]

    # The 2/3 scale was chosen deliberately: the original M6/M5/M3-class holes
    # land close to convenient M4/M3/M2 prototype hardware sizes.
    hardware = {
        "main_pivot": "1 x M4 bolt/pin (scaled M6-class pivot)",
        "drive_pin": "1 x M3 bolt/pin (scaled M5-class drive)",
        "upper_die_cap": "2 x M2 screws, or temporary small self-tapping screws",
    }

    manifest = {
        "mode": "low-material-elegant-handheld-motion-test",
        "scale": scale,
        "purpose": "fit/motion/ergonomics and gentle paper-engagement test only; not strength validation",
        "approx_linear_size_fraction": scale,
        "approx_volume_fraction_vs_full_scale": round(scale**3, 4),
        "solid_model_mass_g": masses,
        "solid_press_mass_reduction_percent": round((1.0 - scaled_press_mass / full_mass) * 100.0, 1),
        "test_die_contract_mm": die_dims,
        "test_die_relief": {
            "shape": "annular ridge/groove",
            "male_nominal_relief_mm": 0.80 * scale / DEFAULT_TEST_SCALE,
            "female_nominal_groove_depth_mm": 0.95 * scale / DEFAULT_TEST_SCALE,
            "purpose": "make a simple visible circular paper mark while testing mechanism engagement",
        },
        "hardware": hardware,
        "collision_validation": collisions,
        "print_guidance": {
            "scale_in_slicer": "100% — geometry is already scaled",
            "layer_height_mm": "0.24 to 0.28 for the throwaway press parts; 0.20 for the two tiny test dies",
            "shells": 2,
            "infill": "5-10% for motion test; do not use this reduced article for high force",
            "supports": "avoid unless slicer preview identifies an actual unsupported region",
        },
        "important": [
            "This pack is not compatible with the final 42 mm die cartridges.",
            "Use the included small male/female test dies only.",
            "Do not infer full-size press strength from this scaled prototype.",
            "The full-size elegant press remains the source of truth for final hardware geometry.",
        ],
        "outputs": outputs,
    }
    manifest_path = out / "elegant_test_press_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs["manifest"] = str(manifest_path)
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m embossforge.mechanics.elegant_test",
        description="Generate a 2/3-scale low-material motion test of the elegant handheld embosser",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("build") / "elegant-lever-press-test",
        help="Output directory",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=DEFAULT_TEST_SCALE,
        help="Uniform prototype scale; default 0.667",
    )
    args = parser.parse_args(argv)
    outputs = export_elegant_test_press_pack(args.out, scale=args.scale)
    print(f"Generated low-material elegant press test at {args.scale:.3f}x")
    print("  This is a motion/fit prototype, not a strength test.")
    print("  Suggested hardware at default scale: M4 pivot, M3 drive pin, 2 x M2 cap screws.")
    for key, value in outputs.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
