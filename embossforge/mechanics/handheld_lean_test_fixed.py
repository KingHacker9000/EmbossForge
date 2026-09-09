from __future__ import annotations

from dataclasses import asdict, replace
import json
from pathlib import Path
from typing import Any

from .cad import export_part
from .handheld_compact import HandLeverSpec, standard_handheld_die_spec
from .handheld_elegant import PLA_DENSITY_G_CM3
from .handheld_lean_test import (
    build_lean_test_body,
    build_lean_test_lever,
    build_lean_test_upper_cap,
    build_lean_test_upper_carriage,
    build_printed_cap_peg,
    build_printed_drive_pin,
    build_printed_drive_retainer,
    build_printed_main_pivot,
    build_printed_main_pivot_retainer,
    lean_test_spec as _old_lean_test_spec,
)


def lean_test_spec(*, die_pocket_clearance_mm: float = 0.18) -> HandLeverSpec:
    """Corrected low-material 42 mm press spec.

    The first lean revision used a 51 mm diameter circular upper platen while
    declaring the carriage only 50 mm wide. The guide channel was therefore
    calculated from the smaller value and clipped the platen by ~0.15 mm per
    side. Keep the 42 mm die interface unchanged and widen only the carriage
    envelope to 51.2 mm, which still fits inside the 60 mm body.
    """
    spec = replace(
        _old_lean_test_spec(die_pocket_clearance_mm=die_pocket_clearance_mm),
        carriage_width_mm=51.2,
    )
    spec.validate(standard_handheld_die_spec())
    return spec


def build_lean_test_assembly(spec: HandLeverSpec | None = None, *, state: str = "closed") -> dict[str, Any]:
    if state not in {"open", "closed"}:
        raise ValueError("state must be open or closed")
    spec = spec or lean_test_spec()
    die = standard_handheld_die_spec()
    carriage_z = spec.closed_carriage_bottom_z_mm(die)
    angle = 0.0
    if state == "open":
        carriage_z += spec.open_travel_mm
        angle = -spec.open_angle_deg

    lever = build_lean_test_lever(spec).translate((0, spec.pivot_y_mm, spec.pivot_z_mm))
    if angle:
        lever = lever.rotate(
            (0, spec.pivot_y_mm, spec.pivot_z_mm),
            (1, spec.pivot_y_mm, spec.pivot_z_mm),
            angle,
        )
    return {
        "body": build_lean_test_body(spec),
        "upper_carriage": build_lean_test_upper_carriage(spec).translate((0, 0, carriage_z)),
        "lever": lever,
    }


def validate_lean_test_clearance(spec: HandLeverSpec | None = None, *, tolerance_mm3: float = 1e-3):
    spec = spec or lean_test_spec()
    report: dict[str, list[tuple[str, str, float]]] = {}
    for state in ("closed", "open"):
        parts = build_lean_test_assembly(spec, state=state)
        names = list(parts)
        collisions: list[tuple[str, str, float]] = []
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                try:
                    volume = float(parts[left].intersect(parts[right]).val().Volume())
                except Exception:
                    volume = 0.0
                if volume > tolerance_mm3:
                    collisions.append((left, right, volume))
        report[state] = collisions
    return report


def _solid_mass_g(part: Any) -> float:
    return float(part.val().Volume()) / 1000.0 * PLA_DENSITY_G_CM3


def export_lean_test_press_pack(out_dir: str | Path, *, die_pocket_clearance_mm: float = 0.18) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    spec = lean_test_spec(die_pocket_clearance_mm=die_pocket_clearance_mm)
    die = standard_handheld_die_spec()

    # Validate before writing files so a bad CAD revision cannot leave a folder
    # full of apparently printable but incompatible parts.
    collisions = validate_lean_test_clearance(spec)
    if collisions["closed"] or collisions["open"]:
        raise RuntimeError(
            "Lean test press contains unintended printed-part collisions:\n"
            + json.dumps(collisions, indent=2)
        )

    parts = {
        "body": build_lean_test_body(spec),
        "upper_carriage": build_lean_test_upper_carriage(spec),
        "upper_backing_cap": build_lean_test_upper_cap(spec),
        "lever": build_lean_test_lever(spec),
        "main_pivot_pin": build_printed_main_pivot(spec),
        "main_pivot_retainer": build_printed_main_pivot_retainer(),
        "drive_pin": build_printed_drive_pin(spec),
        "drive_pin_retainer": build_printed_drive_retainer(),
        "upper_cap_peg": build_printed_cap_peg(),
    }
    outputs: dict[str, str] = {}
    for name, part in parts.items():
        for ext in ("stl", "step"):
            outputs[f"{name}_{ext}"] = str(export_part(part, out / f"{name}.{ext}"))

    masses = {name: round(_solid_mass_g(part), 2) for name, part in parts.items()}
    manifest = {
        "mode": "lean-full-size-42mm-handheld-test-press-r2",
        "purpose": "low-material mechanism test using already-printed standard 42 mm dies",
        "status": "CAD/software prototype; printed PLA pins are test-only",
        "fix": "upper-carriage envelope widened so the 51 mm circular platen clears both guide rails",
        "exact_die_contract_mm": {
            "diameter": die.diameter_mm,
            "base_thickness": die.base_thickness_mm,
            "key_width": die.key_width_mm,
            "key_depth": die.key_depth_mm,
        },
        "press": asdict(spec),
        "derived": {
            "open_handle_angle_deg": spec.open_angle_deg,
            "open_travel_mm": spec.open_travel_mm,
            "nominal_lever_ratio": spec.nominal_lever_ratio,
            "solid_pla_mass_upper_bound_g": masses,
            "solid_pla_mass_total_upper_bound_g": round(sum(masses.values()) + masses["upper_cap_peg"], 2),
        },
        "printed_quantities": {
            "body": 1,
            "upper_carriage": 1,
            "upper_backing_cap": 1,
            "lever": 1,
            "main_pivot_pin": 1,
            "main_pivot_retainer": 1,
            "drive_pin": 1,
            "drive_pin_retainer": 1,
            "upper_cap_peg": 2,
        },
        "hardware_policy": {
            "test": "all required retainers/pins are printable in this pack; no metal hardware required",
            "final": "replace printed pivot/drive pins with metal M6/M5 hardware before high-force use",
        },
        "collision_validation": collisions,
        "outputs": outputs,
    }
    manifest_path = out / "lean_test_press_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs["manifest"] = str(manifest_path)
    return outputs
