from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .spec import CartridgeSpec, PressSpec


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover - depends on optional CAD extra
        raise RuntimeError(
            "CadQuery is required for mechanical model generation. Install with: pip install -e \".[cad]\""
        ) from exc
    return cq


def build_cartridge(spec: CartridgeSpec, *, upper: bool = False):
    """Build a reusable die cartridge.

    The cartridge is a broad rectangular force-bearing body with a circular die
    pocket, two longitudinal guide rails, a front finger notch, optional magnet
    pockets, and an asymmetric orientation key. The upper variant mirrors the
    key in Y so the matched halves remain visually distinguishable.
    """
    spec.validate()
    cq = _cq()

    w = spec.outer_width_mm
    d = spec.outer_depth_mm
    h = spec.body_thickness_mm

    body = cq.Workplane("XY").box(w, d, h, centered=(True, True, False))

    # Die pocket opens from the working face. It is deliberately shallow enough
    # that embossing load transfers through the cartridge shoulder, not magnets.
    pocket_depth = spec.die_base_thickness_mm + 0.2
    body = (
        body.faces(">Z")
        .workplane()
        .circle(spec.die_pocket_diameter_mm / 2)
        .cutBlind(-pocket_depth)
    )

    # Finger notch at the insertion/front edge (+Y) makes a press-fit die easier
    # to remove without adding fragile tabs.
    notch = (
        cq.Workplane("XZ")
        .center(0, h)
        .circle(spec.front_finger_notch_radius_mm)
        .extrude(d / 2 + 2, both=False)
        .translate((0, d / 2 - 1, 0))
    )
    body = body.cut(notch)

    # Guide rails run along Y and are kept outside the die load path.
    rail_y = 0.0
    rail_x = w / 2 - spec.rail_inset_mm - spec.rail_width_mm / 2
    for x in (-rail_x, rail_x):
        rail = (
            cq.Workplane("XY")
            .center(x, rail_y)
            .box(spec.rail_width_mm, d - 2 * spec.insertion_stop_mm, spec.rail_height_mm,
                 centered=(True, True, False))
            .translate((0, 0, h))
        )
        body = body.union(rail)

    # Asymmetric key. Upper and lower variants place it on opposite Y sides so
    # a cartridge inserted upside-down is immediately obvious.
    key_y = (-1 if upper else 1) * (d / 2 - spec.key_offset_mm)
    key = (
        cq.Workplane("XY")
        .center(-w / 2 + spec.key_depth_mm / 2, key_y)
        .box(spec.key_depth_mm, spec.key_width_mm, spec.rail_height_mm,
             centered=(True, True, False))
        .translate((0, 0, h))
    )
    body = body.union(key)

    # Two magnet pockets are optional retention aids only. They never carry the
    # primary compression load.
    if spec.magnet_diameter_mm > 0 and spec.magnet_depth_mm > 0:
        mx = w / 2 - spec.magnet_edge_offset_mm
        my = -d / 2 + spec.magnet_edge_offset_mm
        for x in (-mx, mx):
            body = (
                body.faces("<Z")
                .workplane()
                .center(x, my)
                .circle(spec.magnet_diameter_mm / 2)
                .cutBlind(spec.magnet_depth_mm)
            )

    return body


def build_receiver(spec: CartridgeSpec, *, upper: bool = False, height_mm: float = 8.0):
    """Build a U-shaped receiver sized to the cartridge guide interface."""
    spec.validate()
    if height_mm <= 0:
        raise ValueError("height_mm must be positive")
    cq = _cq()

    clear = spec.receiver_slide_clearance_mm
    w = spec.receiver_width_mm + 2 * (spec.rail_width_mm + 2.0)
    d = spec.outer_depth_mm + 4.0

    receiver = cq.Workplane("XY").box(w, d, height_mm, centered=(True, True, False))

    # Main cartridge pocket is open at the front (+Y) by extending the cutter.
    cutter = (
        cq.Workplane("XY")
        .box(spec.outer_width_mm + 2 * clear, spec.outer_depth_mm + 2 * clear, height_mm + 2,
             centered=(True, True, False))
        .translate((0, 2.0, 1.0))
    )
    receiver = receiver.cut(cutter)

    # Rail channels capture Z motion without depending on tiny snap features.
    rail_x = spec.outer_width_mm / 2 - spec.rail_inset_mm - spec.rail_width_mm / 2
    channel_w = spec.rail_width_mm + 2 * clear
    channel_h = spec.rail_height_mm + clear
    for x in (-rail_x, rail_x):
        channel = (
            cq.Workplane("XY")
            .center(x, 0)
            .box(channel_w, d + 2, channel_h + 0.5, centered=(True, True, False))
            .translate((0, 0, height_mm - channel_h))
        )
        receiver = receiver.cut(channel)

    # Key channel matches the appropriate cartridge half.
    key_y = (-1 if upper else 1) * (spec.outer_depth_mm / 2 - spec.key_offset_mm)
    key_channel = (
        cq.Workplane("XY")
        .center(-spec.outer_width_mm / 2, key_y)
        .box(spec.key_depth_mm + 2 * clear, spec.key_width_mm + 2 * clear, height_mm + 2,
             centered=(True, True, False))
    )
    receiver = receiver.cut(key_channel)
    return receiver


def build_press_parts(cartridge: CartridgeSpec, press: PressSpec) -> dict[str, Any]:
    """Generate the first conservative V0.2 press as separate CadQuery solids."""
    cartridge.validate()
    press.validate()
    cq = _cq()

    # Base with four mounting holes.
    base = cq.Workplane("XY").box(
        press.base_width_mm,
        press.base_depth_mm,
        press.base_thickness_mm,
        centered=(True, True, False),
    )
    hx = press.base_width_mm / 2 - press.mounting_hole_edge_offset_mm
    hy = press.base_depth_mm / 2 - press.mounting_hole_edge_offset_mm
    for x in (-hx, hx):
        for y in (-hy, hy):
            base = (
                base.faces(">Z")
                .workplane()
                .center(x, y)
                .hole(press.mounting_hole_diameter_mm)
            )

    # Lower cartridge receiver is mounted toward the front of the throat.
    lower_receiver = build_receiver(cartridge, upper=False, height_mm=press.lower_receiver_height_mm)
    lower_y = press.base_depth_mm / 2 - press.throat_depth_mm
    lower_receiver = lower_receiver.translate((0, lower_y, press.base_thickness_mm))

    # Side cheeks straddle the lever and ram. Each cheek is a simple thick plate
    # with a pivot bore; fillets can be added after physical validation.
    cheek_x = press.cheek_spacing_mm / 2 + press.side_cheek_thickness_mm / 2
    cheek_y = -press.base_depth_mm / 2 + press.side_cheek_depth_mm / 2 + 8.0
    cheek = cq.Workplane("XY").box(
        press.side_cheek_thickness_mm,
        press.side_cheek_depth_mm,
        press.side_cheek_height_mm,
        centered=(True, True, False),
    )
    # Pivot axis is X, so drill from YZ plane.
    bore = (
        cq.Workplane("YZ")
        .center(cheek_y, press.pivot_height_mm)
        .circle(press.pivot_diameter_mm / 2)
        .extrude(press.base_width_mm, both=True)
    )
    left_cheek = cheek.translate((-cheek_x, cheek_y, press.base_thickness_mm)).cut(bore)
    right_cheek = cheek.translate((cheek_x, cheek_y, press.base_thickness_mm)).cut(bore)

    # Lever lies along Y in the neutral/open configuration. Pivot bore is near
    # the rear end; the long front portion provides mechanical advantage.
    lever = cq.Workplane("XY").box(
        press.lever_width_mm,
        press.lever_length_mm,
        press.lever_thickness_mm,
        centered=(True, False, True),
    )
    lever = lever.translate((0, cheek_y, press.base_thickness_mm + press.pivot_height_mm))
    lever_bore = (
        cq.Workplane("YZ")
        .center(cheek_y, press.base_thickness_mm + press.pivot_height_mm)
        .circle(press.pivot_diameter_mm / 2)
        .extrude(press.lever_width_mm + 4, both=True)
    )
    lever = lever.cut(lever_bore)

    # Ram is kept as a separate solid so the final guide/contact geometry can be
    # revised after visual/physical inspection without reworking the whole press.
    ram_y = cheek_y + press.lever_pivot_to_ram_mm
    ram = cq.Workplane("XY").box(
        press.ram_width_mm,
        press.ram_depth_mm,
        press.ram_height_mm,
        centered=(True, True, False),
    )
    ram_z = press.base_thickness_mm + press.minimum_closed_gap_mm + press.upper_receiver_height_mm
    ram = ram.translate((0, ram_y, ram_z))

    upper_receiver = build_receiver(cartridge, upper=True, height_mm=press.upper_receiver_height_mm)
    upper_receiver = upper_receiver.rotate((0, 0, 0), (1, 0, 0), 180)
    upper_receiver = upper_receiver.translate((0, lower_y, ram_z))

    return {
        "base": base,
        "left_cheek": left_cheek,
        "right_cheek": right_cheek,
        "lever": lever,
        "ram": ram,
        "lower_receiver": lower_receiver,
        "upper_receiver": upper_receiver,
    }


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


def export_press_pack(out_dir: str | Path, cartridge: CartridgeSpec | None = None,
                      press: PressSpec | None = None) -> dict[str, str]:
    """Export cartridges, receivers, and press parts to both STEP and STL."""
    cartridge = cartridge or CartridgeSpec()
    press = press or PressSpec()
    cartridge.validate()
    press.validate()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    parts: dict[str, Any] = {
        "cartridge_lower": build_cartridge(cartridge, upper=False),
        "cartridge_upper": build_cartridge(cartridge, upper=True),
        "receiver_lower": build_receiver(cartridge, upper=False, height_mm=press.lower_receiver_height_mm),
        "receiver_upper": build_receiver(cartridge, upper=True, height_mm=press.upper_receiver_height_mm),
    }
    parts.update(build_press_parts(cartridge, press))

    outputs: dict[str, str] = {}
    for name, part in parts.items():
        for ext in ("step", "stl"):
            p = export_part(part, out_dir / f"{name}.{ext}")
            outputs[f"{name}_{ext}"] = str(p)

    manifest = out_dir / "mechanics_manifest.json"
    import json
    manifest.write_text(
        json.dumps(
            {
                "cartridge": asdict(cartridge),
                "press": {**asdict(press), "nominal_lever_ratio": press.nominal_lever_ratio},
                "outputs": outputs,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    outputs["manifest"] = str(manifest)
    return outputs
