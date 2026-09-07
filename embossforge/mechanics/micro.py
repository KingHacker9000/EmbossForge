from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from ..micro_die import micro_butterfly_spec
from .cad import export_part


PLA_DENSITY_G_CM3 = 1.24


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover - optional CAD dependency
        raise RuntimeError(
            'CadQuery is required for micro-tongs generation. Install with: pip install -e ".[cad]"'
        ) from exc
    return cq


@dataclass(frozen=True)
class MicroTongsSpec:
    """Ultra-light one-piece PLA flexure tongs for the 16 mm butterfly dies.

    The two long ladder-style arms act as leaf springs. There is no pivot,
    guide rod, cartridge, roller, screw, or other hardware. Existing male/female
    dies load directly into shallow keyed pockets in the opposing jaws.
    """

    arm_length_mm: float = 72.0
    arm_thickness_mm: float = 3.0
    spring_rail_width_mm: float = 2.0
    spring_rung_depth_mm: float = 1.8
    spring_rung_pitch_mm: float = 12.0
    rear_bridge_depth_mm: float = 8.0
    open_jaw_surface_gap_mm: float = 5.2

    jaw_outer_diameter_mm: float = 20.5
    jaw_center_from_rear_mm: float = 70.0
    die_pocket_depth_mm: float = 1.15
    die_pocket_clearance_mm: float = 0.15
    removal_notch_radius_mm: float = 2.2

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if name.endswith("_mm") and value <= 0:
                raise ValueError(f"{name} must be positive")
        die = micro_butterfly_spec()
        if self.jaw_outer_diameter_mm <= die.diameter_mm + 2 * self.die_pocket_clearance_mm + 2.0:
            raise ValueError("Micro-tongs jaw is too small to leave a useful wall around the die")
        if self.die_pocket_depth_mm >= die.base_thickness_mm:
            raise ValueError("Die pocket must leave part of the die base exposed for removal")
        if self.spring_rail_width_mm * 2 >= self.jaw_outer_diameter_mm:
            raise ValueError("Spring rails leave no open truss area")
        if self.spring_rung_pitch_mm <= self.spring_rung_depth_mm:
            raise ValueError("Spring rung pitch must exceed rung depth")
        if self.arm_length_mm <= self.jaw_center_from_rear_mm - self.jaw_outer_diameter_mm / 2:
            raise ValueError("Arm is too short to support the jaw")
        if self.open_jaw_surface_gap_mm <= self.required_closed_surface_gap_mm:
            raise ValueError("Open jaw gap must exceed the nominal closed jaw gap")

    @property
    def total_stack_height_mm(self) -> float:
        return 2 * self.arm_thickness_mm + self.open_jaw_surface_gap_mm

    @property
    def required_closed_surface_gap_mm(self) -> float:
        die = micro_butterfly_spec()
        exposed_per_die = die.base_thickness_mm - self.die_pocket_depth_mm + die.relief_height_mm
        return 2 * exposed_per_die + die.paper_thickness_mm

    @property
    def required_total_flex_mm(self) -> float:
        return self.open_jaw_surface_gap_mm - self.required_closed_surface_gap_mm

    @property
    def required_flex_per_arm_mm(self) -> float:
        return self.required_total_flex_mm / 2


def micro_tongs_spec(*, die_pocket_clearance_mm: float = 0.15) -> MicroTongsSpec:
    spec = MicroTongsSpec(die_pocket_clearance_mm=die_pocket_clearance_mm)
    spec.validate()
    return spec


def _keyed_pocket(spec: MicroTongsSpec, *, z0: float) -> Any:
    cq = _cq()
    die = micro_butterfly_spec()
    jaw_y = spec.jaw_center_from_rear_mm
    clear = spec.die_pocket_clearance_mm
    depth = spec.die_pocket_depth_mm

    circle = (
        cq.Workplane("XY")
        .center(0, jaw_y)
        .circle((die.diameter_mm + 2 * clear) / 2)
        .extrude(depth)
        .translate((0, 0, z0))
    )

    overlap = 0.5
    tab_depth = die.key_depth_mm + overlap + 2 * clear
    tab_y = jaw_y + die.diameter_mm / 2 + (die.key_depth_mm - overlap) / 2
    tab = (
        cq.Workplane("XY")
        .center(0, tab_y)
        .rect(die.key_width_mm + 2 * clear, tab_depth)
        .extrude(depth)
        .translate((0, 0, z0))
    )
    return circle.union(tab)


def _spring_arm(spec: MicroTongsSpec, *, z0: float):
    """Build one symmetric ladder spring arm."""
    cq = _cq()
    radius = spec.jaw_outer_diameter_mm / 2
    rail = spec.spring_rail_width_mm
    t = spec.arm_thickness_mm
    y_center = spec.arm_length_mm / 2

    arm = None
    for sign in (-1, 1):
        x = sign * (radius - rail / 2)
        piece = (
            cq.Workplane("XY")
            .center(x, y_center)
            .box(rail, spec.arm_length_mm, t, centered=(True, True, False))
            .translate((0, 0, z0))
        )
        arm = piece if arm is None else arm.union(piece)

    y = spec.rear_bridge_depth_mm + spec.spring_rung_pitch_mm / 2
    while y < spec.jaw_center_from_rear_mm - radius * 0.55:
        rung = (
            cq.Workplane("XY")
            .center(0, y)
            .box(
                spec.jaw_outer_diameter_mm,
                spec.spring_rung_depth_mm,
                t,
                centered=(True, True, False),
            )
            .translate((0, 0, z0))
        )
        arm = arm.union(rung)
        y += spec.spring_rung_pitch_mm
    return arm


def _rear_flexure(spec: MicroTongsSpec):
    cq = _cq()
    radius = spec.jaw_outer_diameter_mm / 2
    rail = spec.spring_rail_width_mm
    total_h = spec.total_stack_height_mm

    flex = None
    for sign in (-1, 1):
        x = sign * (radius - rail / 2)
        column = (
            cq.Workplane("XY")
            .center(x, spec.rear_bridge_depth_mm / 2)
            .box(rail, spec.rear_bridge_depth_mm, total_h, centered=(True, True, False))
        )
        flex = column if flex is None else flex.union(column)

    web = (
        cq.Workplane("XY")
        .center(0, spec.spring_rung_depth_mm / 2)
        .box(
            spec.jaw_outer_diameter_mm,
            spec.spring_rung_depth_mm,
            total_h,
            centered=(True, True, False),
        )
    )
    return flex.union(web)


def build_micro_tongs(spec: MicroTongsSpec | None = None):
    """Build the one-piece flexure tongs in use orientation."""
    spec = spec or micro_tongs_spec()
    spec.validate()
    cq = _cq()

    t = spec.arm_thickness_mm
    upper_z = t + spec.open_jaw_surface_gap_mm
    jaw_y = spec.jaw_center_from_rear_mm

    lower_arm = _spring_arm(spec, z0=0.0)
    upper_arm = _spring_arm(spec, z0=upper_z)
    bridge = _rear_flexure(spec)

    # Compact flat-sided jaw pads make the side-oriented STL sit positively on
    # the bed. The sockets themselves remain exact circular/keyed die pockets.
    lower_jaw = (
        cq.Workplane("XY")
        .center(0, jaw_y)
        .box(
            spec.jaw_outer_diameter_mm,
            spec.jaw_outer_diameter_mm,
            t,
            centered=(True, True, False),
        )
    )
    upper_jaw = lower_jaw.translate((0, 0, upper_z))

    body = lower_arm.union(upper_arm).union(bridge).union(lower_jaw).union(upper_jaw)
    body = body.cut(_keyed_pocket(spec, z0=t - spec.die_pocket_depth_mm))
    body = body.cut(_keyed_pocket(spec, z0=upper_z))

    notch_y = jaw_y + spec.jaw_outer_diameter_mm / 2
    lower_notch = (
        cq.Workplane("XY")
        .center(0, notch_y)
        .circle(spec.removal_notch_radius_mm)
        .extrude(spec.die_pocket_depth_mm + 0.4)
        .translate((0, 0, t - spec.die_pocket_depth_mm))
    )
    upper_notch = (
        cq.Workplane("XY")
        .center(0, notch_y)
        .circle(spec.removal_notch_radius_mm)
        .extrude(spec.die_pocket_depth_mm + 0.4)
        .translate((0, 0, upper_z))
    )
    return body.cut(lower_notch).cut(upper_notch)


def build_micro_tongs_print_orientation(spec: MicroTongsSpec | None = None):
    """Rotate onto a trussed flat side that is intended to print without large supports."""
    spec = spec or micro_tongs_spec()
    part = build_micro_tongs(spec)
    return part.rotate((0, 0, 0), (0, 1, 0), 90).translate(
        (0, 0, spec.jaw_outer_diameter_mm / 2)
    )


def _solid_mass_g(part: Any) -> float:
    return float(part.val().Volume()) / 1000.0 * PLA_DENSITY_G_CM3


def export_micro_press_pack(
    out_dir: str | Path,
    *,
    slide_clearance_mm: float = 0.25,
    die_pocket_clearance_mm: float = 0.15,
) -> dict[str, str]:
    """Export the ultra-light one-piece butterfly flexure tongs."""
    del slide_clearance_mm  # obsolete cartridge-era compatibility argument
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    die = micro_butterfly_spec()
    spec = micro_tongs_spec(die_pocket_clearance_mm=die_pocket_clearance_mm)
    use_part = build_micro_tongs(spec)
    print_part = build_micro_tongs_print_orientation(spec)

    stl = export_part(print_part, out / "micro_butterfly_tongs.stl")
    step = export_part(use_part, out / "micro_butterfly_tongs.step")
    solid_mass = _solid_mass_g(use_part)

    manifest_path = out / "micro_press_manifest.json"
    manifest = {
        "mode": "micro-butterfly-flexure-tongs",
        "purpose": (
            "Ultra-low-material hand embosser for the already-printed 16 mm butterfly-test pair. "
            "The PLA ladder arms flex like tongs; there is no pivot, guide rod, cartridge, roller, screw, or other hardware."
        ),
        "physical_status": "unvalidated prototype / light hand force only",
        "compatible_die_command": "embossforge butterfly-test",
        "exact_die_contract_mm": {
            "diameter": die.diameter_mm,
            "base_thickness": die.base_thickness_mm,
            "key_width": die.key_width_mm,
            "key_depth": die.key_depth_mm,
            "relief": die.relief_height_mm,
        },
        "tongs_spec": asdict(spec),
        "derived": {
            "required_closed_surface_gap_mm": spec.required_closed_surface_gap_mm,
            "required_total_flex_mm": spec.required_total_flex_mm,
            "required_flex_per_arm_mm": spec.required_flex_per_arm_mm,
            "solid_pla_mass_upper_bound_g": round(solid_mass, 2),
        },
        "print": {
            "stl_orientation": "pre-rotated onto a flat/trussed side; jaw and one outer rail provide continuous bed contact",
            "recommended_layer_height_mm": 0.20,
            "recommended_walls": 3,
            "recommended_infill_percent": 10,
            "supports": "normally off; inspect the shallow sideways die sockets in slicer preview",
            "important": "Use the slicer's own grams estimate before printing.",
        },
        "use": [
            "Press the male butterfly die into the lower keyed socket and the female die into the opposing upper socket.",
            "The rectangular tabs must sit in the matching +Y key extensions; do not rotate the dies independently.",
            "Insert paper between the die faces and squeeze the two long arms together like tongs.",
            "Stop once the emboss forms. Do not fold the arms flat together or repeatedly over-flex PLA.",
            "Use the front scallops to remove the dies with a fingernail or thin plastic pick.",
        ],
        "outputs": {"stl": str(stl), "step": str(step)},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    return {
        "stl": str(stl),
        "step": str(step),
        "micro_manifest": str(manifest_path),
        "solid_pla_mass_upper_bound_g": f"{solid_mass:.2f}",
    }
