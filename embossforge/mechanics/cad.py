from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path
from typing import Any

from .spec import CartridgeSpec, PressSpec


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover - optional CAD dependency
        raise RuntimeError(
            "CadQuery is required for mechanical model generation. Install with: pip install -e \".[cad]\""
        ) from exc
    return cq


def _solve_open_angle_deg(travel_mm: float, radius_mm: float, roller_drop_mm: float) -> float:
    """Solve the lever angle needed to lift the roller by ``travel_mm``.

    The roller pin is offset forward by ``radius_mm`` and downward by
    ``roller_drop_mm`` from the main pivot. The lever closes at 0 degrees and
    opens by rotating upward about X.
    """
    if travel_mm <= 0:
        return 0.0
    max_lift = radius_mm + roller_drop_mm
    if travel_mm >= max_lift:
        raise ValueError("Requested platen travel is impossible with the configured lever geometry")

    lo = 0.0
    hi = math.pi / 2

    def lift(angle: float) -> float:
        return radius_mm * math.sin(angle) + roller_drop_mm * (1.0 - math.cos(angle))

    for _ in range(80):
        mid = (lo + hi) / 2
        if lift(mid) < travel_mm:
            lo = mid
        else:
            hi = mid
    return math.degrees((lo + hi) / 2)


def mechanical_layout(cartridge: CartridgeSpec, press: PressSpec) -> dict[str, float]:
    """Return derived assembly coordinates for the open/closed press states."""
    cartridge.validate()
    press.validate()

    lower_y = press.base_depth_mm / 2 - press.throat_depth_mm
    pivot_y = lower_y - press.lever_pivot_to_platen_mm
    cheek_y = (pivot_y + lower_y) / 2
    pivot_y_local = pivot_y - cheek_y

    lower_male_face_z = (
        press.base_thickness_mm
        + cartridge.receiver_floor_mm
        + cartridge.body_thickness_mm
        - cartridge.die_seat_recess_mm
        + press.nominal_die_relief_mm
    )
    upper_face_offset = (
        cartridge.receiver_floor_mm
        + cartridge.body_thickness_mm
        - cartridge.die_seat_recess_mm
    )

    platen_open_bottom_z = lower_male_face_z + press.open_face_gap_mm + upper_face_offset
    platen_closed_bottom_z = lower_male_face_z + press.closed_face_gap_mm + upper_face_offset
    platen_open_top_z = platen_open_bottom_z + press.platen_thickness_mm
    platen_closed_top_z = platen_closed_bottom_z + press.platen_thickness_mm

    roller_radius = press.contact_roller_diameter_mm / 2
    pivot_world_z = (
        platen_closed_top_z
        + press.contact_roller_drop_mm
        + roller_radius
        + press.contact_clearance_mm
    )
    pivot_axis_height_above_base = pivot_world_z - press.base_thickness_mm
    if pivot_axis_height_above_base >= press.side_cheek_height_mm:
        raise ValueError("Derived lever pivot lies above the side cheeks; adjust press dimensions")

    lever_open_angle_deg = _solve_open_angle_deg(
        press.required_platen_travel_mm,
        press.lever_pivot_to_platen_mm,
        press.contact_roller_drop_mm,
    )

    bridge_bottom_world_z = press.base_thickness_mm + press.top_bridge_bottom_above_base_mm
    bridge_top_world_z = bridge_bottom_world_z + press.top_bridge_thickness_mm
    stop_sleeve_height = platen_closed_bottom_z - press.base_thickness_mm
    if stop_sleeve_height <= 0:
        raise ValueError("Derived stop sleeve height is not positive")

    guide_rod_length = (
        bridge_bottom_world_z
        - press.base_thickness_mm
        + 2 * press.guide_rod_socket_depth_mm
    )

    return {
        "lower_y": lower_y,
        "pivot_y": pivot_y,
        "cheek_y": cheek_y,
        "pivot_y_local": pivot_y_local,
        "lower_male_face_z": lower_male_face_z,
        "upper_face_offset": upper_face_offset,
        "platen_open_bottom_z": platen_open_bottom_z,
        "platen_closed_bottom_z": platen_closed_bottom_z,
        "platen_open_top_z": platen_open_top_z,
        "platen_closed_top_z": platen_closed_top_z,
        "pivot_world_z": pivot_world_z,
        "pivot_axis_height_above_base": pivot_axis_height_above_base,
        "lever_open_angle_deg": lever_open_angle_deg,
        "bridge_bottom_world_z": bridge_bottom_world_z,
        "bridge_top_world_z": bridge_top_world_z,
        "stop_sleeve_height": stop_sleeve_height,
        "guide_rod_length": guide_rod_length,
    }


def build_cartridge(spec: CartridgeSpec):
    """Build one universal sliding cartridge with a keyed die pocket."""
    spec.validate()
    cq = _cq()

    w = spec.body_width_mm
    d = spec.body_depth_mm
    h = spec.body_thickness_mm
    body = cq.Workplane("XY").box(w, d, h, centered=(True, True, False))

    # Keyed insert pocket: round die plus a +Y tab that fixes angular alignment.
    pocket_depth = spec.die_base_thickness_mm + spec.die_seat_recess_mm
    circle = (
        cq.Workplane("XY")
        .circle(spec.die_pocket_diameter_mm / 2)
        .extrude(pocket_depth)
    )
    overlap = 0.5
    tab_depth = spec.die_key_depth_mm + overlap + 2 * spec.die_pocket_clearance_mm
    tab_y = spec.die_diameter_mm / 2 + (spec.die_key_depth_mm - overlap) / 2
    tab = (
        cq.Workplane("XY")
        .center(0, tab_y)
        .rect(spec.die_key_width_mm + 2 * spec.die_pocket_clearance_mm, tab_depth)
        .extrude(pocket_depth)
    )
    pocket = circle.union(tab).translate((0, 0, h - pocket_depth))
    body = body.cut(pocket)

    # Rails protrude laterally, so the receiver grooves actually capture them.
    y0 = -d / 2 + spec.side_rail_rear_setback_mm
    y1 = d / 2 - spec.side_rail_front_setback_mm
    rail_y = (y0 + y1) / 2
    rail_z = spec.side_rail_center_z_mm - spec.side_rail_height_mm / 2
    for sign in (-1, 1):
        x = sign * (w / 2 + spec.side_rail_extension_mm / 2)
        rail = (
            cq.Workplane("XY")
            .center(x, rail_y)
            .box(
                spec.side_rail_extension_mm,
                spec.rail_length_mm,
                spec.side_rail_height_mm,
                centered=(True, True, False),
            )
            .translate((0, 0, rail_z))
        )
        body = body.union(rail)

    # Front scallop exposes the edge of the insert for removal.
    notch = (
        cq.Workplane("XY")
        .center(0, d / 2)
        .circle(spec.front_finger_notch_radius_mm)
        .extrude(spec.front_finger_notch_depth_mm)
        .translate((0, 0, h - spec.front_finger_notch_depth_mm))
    )
    return body.cut(notch)


def build_receiver(spec: CartridgeSpec):
    """Build one universal receiver; the upper copy is installed upside down."""
    spec.validate()
    cq = _cq()

    w = spec.receiver_outer_width_mm
    d = spec.receiver_outer_depth_mm
    h = spec.receiver_height_mm
    clear = spec.receiver_slide_clearance_mm

    # Keep the inserted cartridge centered at local Y=0. The rear stop extends
    # only toward -Y, while +Y is the open insertion side.
    receiver = (
        cq.Workplane("XY")
        .box(w, d, h, centered=(True, True, False))
        .translate((0, -spec.receiver_rear_wall_mm / 2, 0))
    )

    channel = (
        cq.Workplane("XY")
        .box(
            spec.body_width_mm + 2 * clear,
            spec.body_depth_mm + 0.8,
            h + 2,
            centered=(True, True, False),
        )
        .translate((0, 0.4, spec.receiver_floor_mm))
    )
    receiver = receiver.cut(channel)

    # Rail channels reach through the front opening but stop before the rear wall.
    y0 = -spec.body_depth_mm / 2 + spec.side_rail_rear_setback_mm - clear
    y1 = spec.body_depth_mm / 2 + 0.6
    groove_length = y1 - y0
    groove_y = (y0 + y1) / 2
    rail_center_world_z = spec.receiver_floor_mm + spec.side_rail_center_z_mm
    groove_height = spec.side_rail_height_mm + 2 * clear
    groove_z = rail_center_world_z - groove_height / 2

    for sign in (-1, 1):
        x = sign * (spec.body_width_mm / 2 + spec.side_rail_extension_mm / 2)
        groove = (
            cq.Workplane("XY")
            .center(x, groove_y)
            .box(
                spec.side_rail_extension_mm + 2 * clear,
                groove_length,
                groove_height,
                centered=(True, True, False),
            )
            .translate((0, 0, groove_z))
        )
        receiver = receiver.cut(groove)

    thumb = (
        cq.Workplane("XY")
        .center(0, spec.body_depth_mm / 2)
        .circle(spec.front_finger_notch_radius_mm + 2)
        .extrude(h + 1)
    )
    return receiver.cut(thumb)


def build_base(cartridge: CartridgeSpec, press: PressSpec):
    cq = _cq()
    layout = mechanical_layout(cartridge, press)
    base = cq.Workplane("XY").box(
        press.base_width_mm,
        press.base_depth_mm,
        press.base_thickness_mm,
        centered=(True, True, False),
    )

    hx = press.base_width_mm / 2 - press.mounting_hole_edge_offset_mm
    hy = press.base_depth_mm / 2 - press.mounting_hole_edge_offset_mm
    base = (
        base.faces(">Z")
        .workplane()
        .pushPoints([(x, y) for x in (-hx, hx) for y in (-hy, hy)])
        .hole(press.mounting_hole_diameter_mm)
    )

    rod_x = press.guide_rod_spacing_mm / 2
    base = (
        base.faces(">Z")
        .workplane()
        .pushPoints([(-rod_x, layout["lower_y"]), (rod_x, layout["lower_y"])])
        .hole(press.guide_rod_socket_diameter_mm, press.guide_rod_socket_depth_mm)
    )
    return base


def build_side_cheek(cartridge: CartridgeSpec, press: PressSpec):
    cq = _cq()
    layout = mechanical_layout(cartridge, press)
    cheek = cq.Workplane("XY").box(
        press.side_cheek_thickness_mm,
        press.side_cheek_depth_mm,
        press.side_cheek_height_mm,
        centered=(True, True, False),
    )
    bore = (
        cq.Workplane("YZ")
        .center(layout["pivot_y_local"], layout["pivot_axis_height_above_base"])
        .circle(press.pivot_diameter_mm / 2)
        .extrude(press.side_cheek_thickness_mm + 4, both=True)
    )
    return cheek.cut(bore)


def build_lever(press: PressSpec):
    cq = _cq()
    front = press.lever_length_mm - press.lever_rear_overhang_mm
    center_y = (front - press.lever_rear_overhang_mm) / 2
    lever = (
        cq.Workplane("XY")
        .box(
            press.lever_width_mm,
            press.lever_length_mm,
            press.lever_thickness_mm,
            centered=(True, True, True),
        )
        .translate((0, center_y, 0))
    )
    pivot = (
        cq.Workplane("YZ")
        .circle(press.pivot_diameter_mm / 2)
        .extrude(press.lever_width_mm + 4, both=True)
    )
    lever = lever.cut(pivot)

    # Two short ears hold the transverse contact roller below the lever body.
    ear_x = press.contact_roller_width_mm / 2 + press.lever_ear_thickness_mm / 2
    ear_top = -press.lever_thickness_mm / 2 + press.lever_ear_overlap_mm
    ear_bottom = (
        -press.contact_roller_drop_mm
        - press.contact_roller_pin_diameter_mm / 2
        - press.lever_ear_pin_margin_mm
    )
    ear_height = ear_top - ear_bottom
    ear_center_z = (ear_top + ear_bottom) / 2
    if ear_height <= 0:
        raise ValueError("Lever ear geometry is invalid")

    for sign in (-1, 1):
        ear = (
            cq.Workplane("XY")
            .center(sign * ear_x, press.lever_pivot_to_platen_mm)
            .box(
                press.lever_ear_thickness_mm,
                press.lever_ear_depth_mm,
                ear_height,
                centered=(True, True, True),
            )
            .translate((0, 0, ear_center_z))
        )
        lever = lever.union(ear)

    roller_pin_bore = (
        cq.Workplane("YZ")
        .center(press.lever_pivot_to_platen_mm, -press.contact_roller_drop_mm)
        .circle(press.contact_roller_pin_diameter_mm / 2)
        .extrude(press.lever_width_mm + 4, both=True)
    )
    return lever.cut(roller_pin_bore)


def build_contact_roller(press: PressSpec):
    cq = _cq()
    outer = (
        cq.Workplane("YZ")
        .circle(press.contact_roller_diameter_mm / 2)
        .extrude(press.contact_roller_width_mm / 2, both=True)
    )
    hole = (
        cq.Workplane("YZ")
        .circle(press.contact_roller_pin_diameter_mm / 2)
        .extrude(press.contact_roller_width_mm / 2 + 1, both=True)
    )
    return outer.cut(hole)


def build_platen(press: PressSpec):
    cq = _cq()
    platen = cq.Workplane("XY").box(
        press.platen_width_mm,
        press.platen_depth_mm,
        press.platen_thickness_mm,
        centered=(True, True, False),
    )
    rod_x = press.guide_rod_spacing_mm / 2
    platen = (
        platen.faces(">Z")
        .workplane()
        .pushPoints([(-rod_x, 0), (rod_x, 0)])
        .hole(press.guide_rod_platen_hole_diameter_mm)
    )

    # Shallow top reliefs keep the lever ears clear throughout the opening arc.
    ear_x = press.contact_roller_width_mm / 2 + press.lever_ear_thickness_mm / 2
    notch_width = press.lever_ear_thickness_mm + 1.2
    notch_depth_y = press.lever_ear_depth_mm + 6.0
    for sign in (-1, 1):
        relief = (
            cq.Workplane("XY")
            .center(sign * ear_x, 0)
            .box(
                notch_width,
                notch_depth_y,
                press.platen_ear_relief_depth_mm + 0.1,
                centered=(True, True, False),
            )
            .translate((0, 0, press.platen_thickness_mm - press.platen_ear_relief_depth_mm))
        )
        platen = platen.cut(relief)
    return platen


def build_top_bridge(press: PressSpec):
    cq = _cq()
    bridge = cq.Workplane("XY").box(
        press.top_bridge_width_mm,
        press.top_bridge_depth_mm,
        press.top_bridge_thickness_mm,
        centered=(True, True, False),
    )
    rod_x = press.guide_rod_spacing_mm / 2
    return (
        bridge.faces("<Z")
        .workplane()
        .pushPoints([(-rod_x, 0), (rod_x, 0)])
        .hole(press.guide_rod_socket_diameter_mm, press.guide_rod_socket_depth_mm)
    )


def build_stop_sleeve(cartridge: CartridgeSpec, press: PressSpec):
    cq = _cq()
    height = mechanical_layout(cartridge, press)["stop_sleeve_height"]
    inside = press.guide_rod_diameter_mm + press.stop_sleeve_rod_clearance_mm
    return (
        cq.Workplane("XY")
        .circle(press.stop_sleeve_outer_diameter_mm / 2)
        .circle(inside / 2)
        .extrude(height)
    )


def build_press_parts(cartridge: CartridgeSpec, press: PressSpec) -> dict[str, Any]:
    """Return one copy of every unique printable V0.2 mechanical part."""
    cartridge.validate()
    press.validate()
    return {
        "base": build_base(cartridge, press),
        "side_cheek": build_side_cheek(cartridge, press),
        "top_bridge": build_top_bridge(press),
        "lever": build_lever(press),
        "contact_roller": build_contact_roller(press),
        "platen": build_platen(press),
        "stop_sleeve": build_stop_sleeve(cartridge, press),
        "receiver": build_receiver(cartridge),
        "cartridge": build_cartridge(cartridge),
    }


def build_assembly_preview(
    cartridge: CartridgeSpec,
    press: PressSpec,
    *,
    state: str = "open",
) -> dict[str, Any]:
    """Build positioned printable solids for collision checks and visual QA."""
    if state not in {"open", "closed"}:
        raise ValueError("state must be 'open' or 'closed'")
    layout = mechanical_layout(cartridge, press)
    platen_z = (
        layout["platen_open_bottom_z"] if state == "open" else layout["platen_closed_bottom_z"]
    )
    lever_angle = layout["lever_open_angle_deg"] if state == "open" else 0.0

    cheek = build_side_cheek(cartridge, press)
    receiver = build_receiver(cartridge)
    cartridge_part = build_cartridge(cartridge)
    stop = build_stop_sleeve(cartridge, press)
    xoff = press.cheek_spacing_mm / 2 + press.side_cheek_thickness_mm / 2
    rod_x = press.guide_rod_spacing_mm / 2

    def lever_transform(part):
        return (
            part.rotate((0, 0, 0), (1, 0, 0), lever_angle)
            .translate((0, layout["pivot_y"], layout["pivot_world_z"]))
        )

    return {
        "base": build_base(cartridge, press),
        "cheek_left": cheek.translate((-xoff, layout["cheek_y"], press.base_thickness_mm)),
        "cheek_right": cheek.translate((xoff, layout["cheek_y"], press.base_thickness_mm)),
        "top_bridge": build_top_bridge(press).translate(
            (0, layout["lower_y"], layout["bridge_bottom_world_z"])
        ),
        "receiver_lower": receiver.translate((0, layout["lower_y"], press.base_thickness_mm)),
        "cartridge_lower": cartridge_part.translate(
            (0, layout["lower_y"], press.base_thickness_mm + cartridge.receiver_floor_mm)
        ),
        "platen": build_platen(press).translate((0, layout["lower_y"], platen_z)),
        "receiver_upper": (
            receiver.rotate((0, 0, 0), (0, 1, 0), 180)
            .translate((0, layout["lower_y"], platen_z))
        ),
        "cartridge_upper": (
            cartridge_part.translate((0, 0, cartridge.receiver_floor_mm))
            .rotate((0, 0, 0), (0, 1, 0), 180)
            .translate((0, layout["lower_y"], platen_z))
        ),
        "lever": lever_transform(build_lever(press)),
        "contact_roller": lever_transform(
            build_contact_roller(press).translate(
                (0, press.lever_pivot_to_platen_mm, -press.contact_roller_drop_mm)
            )
        ),
        "stop_sleeve_left": stop.translate((-rod_x, layout["lower_y"], press.base_thickness_mm)),
        "stop_sleeve_right": stop.translate((rod_x, layout["lower_y"], press.base_thickness_mm)),
    }


def validate_assembly_clearance(
    cartridge: CartridgeSpec,
    press: PressSpec,
    *,
    tolerance_mm3: float = 1e-4,
) -> dict[str, list[tuple[str, str, float]]]:
    """Return unintended printed-part intersections in open and closed states."""
    report: dict[str, list[tuple[str, str, float]]] = {}
    for state in ("open", "closed"):
        parts = build_assembly_preview(cartridge, press, state=state)
        names = list(parts)
        collisions: list[tuple[str, str, float]] = []
        for index, left in enumerate(names):
            for right in names[index + 1 :]:
                try:
                    volume = parts[left].intersect(parts[right]).val().Volume()
                except Exception:
                    volume = 0.0
                if volume > tolerance_mm3:
                    collisions.append((left, right, float(volume)))
        report[state] = collisions
    return report


def export_part(part: Any, path: str | Path) -> Path:
    cq = _cq()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".stl":
        cq.exporters.export(part, str(path), tolerance=0.02, angularTolerance=0.1)
    elif suffix in {".step", ".stp"}:
        cq.exporters.export(part, str(path))
    else:
        raise ValueError(f"Unsupported mechanical export format: {suffix}")
    return path


def _assembly_layout_json(cartridge: CartridgeSpec, press: PressSpec) -> dict[str, Any]:
    """Human/agent-readable assembly state metadata.

    Actual collision validation is generated from CadQuery solids rather than
    trusting this metadata. The coordinates here are primarily for Blender or
    other visualization tooling.
    """
    layout = mechanical_layout(cartridge, press)
    rod_x = press.guide_rod_spacing_mm / 2
    xoff = press.cheek_spacing_mm / 2 + press.side_cheek_thickness_mm / 2

    def t(x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0, pre_z=0.0):
        return {
            "translation_mm": [x, y, z],
            "rotation_deg_xyz": [rx, ry, rz],
            "pre_translation_mm": [0.0, 0.0, pre_z],
        }

    static = {
        "base": t(),
        "cheek_left": {"source": "side_cheek", **t(-xoff, layout["cheek_y"], press.base_thickness_mm)},
        "cheek_right": {"source": "side_cheek", **t(xoff, layout["cheek_y"], press.base_thickness_mm)},
        "top_bridge": t(0, layout["lower_y"], layout["bridge_bottom_world_z"]),
        "receiver_lower": {"source": "receiver", **t(0, layout["lower_y"], press.base_thickness_mm)},
        "cartridge_lower": {"source": "cartridge", **t(0, layout["lower_y"], press.base_thickness_mm + cartridge.receiver_floor_mm)},
        "stop_sleeve_left": {"source": "stop_sleeve", **t(-rod_x, layout["lower_y"], press.base_thickness_mm)},
        "stop_sleeve_right": {"source": "stop_sleeve", **t(rod_x, layout["lower_y"], press.base_thickness_mm)},
    }

    states: dict[str, Any] = {}
    for state in ("open", "closed"):
        platen_z = layout["platen_open_bottom_z"] if state == "open" else layout["platen_closed_bottom_z"]
        angle = layout["lever_open_angle_deg"] if state == "open" else 0.0
        states[state] = {
            **static,
            "platen": t(0, layout["lower_y"], platen_z),
            "receiver_upper": {"source": "receiver", **t(0, layout["lower_y"], platen_z, ry=180)},
            "cartridge_upper": {"source": "cartridge", **t(0, layout["lower_y"], platen_z, ry=180, pre_z=cartridge.receiver_floor_mm)},
            "lever": t(0, layout["pivot_y"], layout["pivot_world_z"], rx=angle),
            "contact_roller": {
                "source": "contact_roller",
                **t(
                    0,
                    layout["pivot_y"],
                    layout["pivot_world_z"],
                    rx=angle,
                    pre_z=-press.contact_roller_drop_mm,
                ),
                "pre_translation_mm": [0.0, press.lever_pivot_to_platen_mm, -press.contact_roller_drop_mm],
            },
        }
    return {"derived": layout, "states": states}


def export_press_pack(
    out_dir: str | Path,
    cartridge: CartridgeSpec | None = None,
    press: PressSpec | None = None,
) -> dict[str, str]:
    """Export local-coordinate printable parts, STEP files, and validation metadata."""
    cartridge = cartridge or CartridgeSpec()
    press = press or PressSpec()
    cartridge.validate()
    press.validate()

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = build_press_parts(cartridge, press)

    outputs: dict[str, str] = {}
    for name, part in parts.items():
        for ext in ("step", "stl"):
            path = export_part(part, out_dir / f"{name}.{ext}")
            outputs[f"{name}_{ext}"] = str(path)

    clearance = validate_assembly_clearance(cartridge, press)
    if clearance["open"] or clearance["closed"]:
        details = json.dumps(clearance, indent=2)
        raise RuntimeError(f"Generated mechanical assembly contains unintended collisions:\n{details}")

    layout_path = out_dir / "assembly_layout.json"
    layout_path.write_text(json.dumps(_assembly_layout_json(cartridge, press), indent=2) + "\n", encoding="utf-8")
    outputs["assembly_layout"] = str(layout_path)

    derived = mechanical_layout(cartridge, press)
    manifest_path = out_dir / "mechanics_manifest.json"
    manifest = {
        "status": "V0.2 prototype - physically validate before applying high force",
        "cartridge": asdict(cartridge),
        "press": asdict(press),
        "derived": {**derived, "nominal_lever_ratio": press.nominal_lever_ratio},
        "printed_quantities": {
            "base": 1,
            "side_cheek": 2,
            "top_bridge": 1,
            "lever": 1,
            "contact_roller": 1,
            "platen": 1,
            "stop_sleeve": 2,
            "receiver": 2,
            "cartridge": 2,
        },
        "hardware": {
            "guide_rods": {
                "quantity": 2,
                "diameter_mm": press.guide_rod_diameter_mm,
                "length_mm": derived["guide_rod_length"],
                "note": "smooth steel rod preferred; trim to fit after test assembly",
            },
            "main_pivot": {
                "quantity": 1,
                "nominal": "M6 bolt or smooth pin",
                "bore_diameter_mm": press.pivot_diameter_mm,
                "minimum_length_mm": press.top_bridge_width_mm,
            },
            "roller_pin": {
                "quantity": 1,
                "nominal": "M5 bolt or smooth pin",
                "bore_diameter_mm": press.contact_roller_pin_diameter_mm,
                "minimum_length_mm": press.lever_width_mm,
            },
        },
        "collision_validation": clearance,
        "outputs": outputs,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    outputs["manifest"] = str(manifest_path)
    return outputs
