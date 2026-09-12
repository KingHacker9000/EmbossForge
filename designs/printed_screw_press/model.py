"""Original all-PLA screw embosser. Millimetres; CadQuery 2.8.

No existing EmbossForge press geometry is imported. Only the published keyed
42 x 3 mm die interface is reproduced as non-printing assembly envelopes.
Run: .venv/Scripts/python designs/printed_screw_press/model.py
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from functools import lru_cache
from pathlib import Path
import cadquery as cq

SOURCE_DIR = Path(__file__).resolve().parent
ROOT = SOURCE_DIR.parent if SOURCE_DIR.name == "source" else SOURCE_DIR.parents[1]
OUT = ROOT if SOURCE_DIR.name == "source" else ROOT / "build" / "printed_screw_press"
PITCH = 6.0
RAM_Z = 53.1
STROKE = 10.0
RAM_Y = -.7
FOOT_Z = RAM_Z + 26.0
PHASE_Z = FOOT_Z + 14


def box(x, y, z, at=(0, 0, 0)):
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, False)).translate(at)


def cyl(r, h, at=(0, 0, 0)):
    return cq.Workplane("XY").circle(r).extrude(h).translate(at)


def poly_z(points, z, h):
    return cq.Workplane("XY").polyline(points).close().extrude(h).translate((0, 0, z))


def xz_prism(points, y0, length):
    # XZ normal is -Y.
    return cq.Workplane("XZ").polyline(points).close().extrude(length).translate((0, y0 + length, 0))


def diamond(v, z, h):
    return poly_z([(v, 0), (0, v), (-v, 0), (0, -v)], z, h)


@lru_cache(maxsize=64)
def thread(major, pitch, length, radial=0.0, axial=0.0):
    """Single-start, truncated 45-degree thread, with explicit fit allowances.

    Sweep starts below the clipping plane so both end faces are complete.
    Clearance cutters expand both radial and axial flanks, not uniform scale.
    """
    depth = 2.0 if major >= 20 else (1.5 if major >= 14 else (1.0 if major >= 8 else .8))
    root = major / 2 - depth
    crest = pitch - 2 * depth - 1.0
    if crest < .35:
        crest = .4
    half = crest / 2
    path = cq.Wire.makeHelix(pitch, (math.ceil(length / pitch) + 2) * pitch, root)
    profile = cq.Workplane("XZ").polyline([
        (root - .2, -half - depth - axial),
        (major / 2 + radial, -half - axial),
        (major / 2 + radial, half + axial),
        (root - .2, half + depth + axial),
    ]).close()
    ridge = profile.sweep(cq.Workplane(obj=path), isFrenet=True).translate((0, 0, -pitch))
    core = cyl(root + radial, (math.ceil(length / pitch) + 4) * pitch, (0, 0, -2 * pitch))
    return core.union(ridge).intersect(box(major + 4, major + 4, length))


def bolt(major, pitch, length, head_d, head_h):
    # Head below Z=0; thread extends toward +Z. Print the head on the bed.
    return thread(major, pitch, length).union(
        cq.Workplane("XY").polygon(6, head_d).extrude(head_h).translate((0, 0, -head_h)))


def axis_x(shape):
    return shape.rotate((0, 0, 0), (0, 1, 0), 90)


def axis_y(shape):
    return shape.rotate((0, 0, 0), (1, 0, 0), -90)


def flip(shape):
    return shape.rotate((0, 0, 0), (0, 1, 0), 180)


def shape_value(shape):
    return shape.val() if isinstance(shape, cq.Workplane) else shape


def build():
    parts = {}
    # C profile; inside corners have a 10 mm radius, rather than sharp notches.
    frame = box(72, 110, 140, (0, 21, 0))
    opening = box(80, 84, 80, (0, -6, 32))
    opening = opening.edges("|X").fillet(10)
    # Extend through the nose, preserving only the two rear inside radii.
    opening = opening.union(box(80, 44, 80, (0, -34, 32)))
    frame = frame.cut(opening)
    frame = frame.cut(diamond(28.45, 105, 40)).cut(diamond(34.45, 105.9, 6.1))
    guide = [(14.35, 35.65), (30.35, 51.65), (30.35, 52.35),
             (-30.35, 52.35), (-30.35, 51.65), (-14.35, 35.65)]
    frame = frame.cut(poly_z(guide, 31.9, 80.2))
    lower_slot = xz_prism([(-26.4, 23.6), (26.4, 23.6), (18.4, 32.01), (-18.4, 32.01)], -35, 61)
    frame = frame.cut(lower_slot)
    tie_positions = [(65, 16), (65, 66), (65, 124)]
    for y, z in tie_positions:
        frame = frame.cut(axis_x(cyl(7.35, 80)).translate((-40, y, z)))
    # Tray retaining screw: recessed entirely below the die working face.
    small_cut = thread(8, 3, 14, .3, .16)
    frame = frame.cut(small_cut.translate((27, -25, 18)))
    left = frame.intersect(box(36, 160, 160, (-18, 10, 0)))
    right = frame.intersect(box(36, 160, 160, (18, 10, 0)))
    for y, z in [(-18, 12), (65, 91)]:
        peg = axis_x(cyl(4, 3.0)).translate((0, y, z))
        left = left.union(peg)
        right = right.cut(axis_x(cyl(4.3, 3.4)).translate((0, y, z)))
    parts["01_frame_left"] = left
    parts["02_frame_right"] = right

    nut = diamond(28, 112, 28).union(diamond(34, 106, 6))
    nut = nut.cut(thread(28, 6, 65, .3, .18).translate((0, 0, PHASE_Z)))
    parts["03_power_nut"] = nut

    # Inverted for printing: wheel on bed, broad thread below and pointed foot last.
    power = thread(28, 6, 80).translate((0, 0, 14))
    power = power.union(cyl(8, 8, (0, 0, 6)))
    foot = cyl(12, 2)
    foot = foot.union(cq.Workplane("XY").workplane(offset=2).circle(12)
                      .workplane(offset=4).circle(8).loft())
    power = power.union(foot)
    wheel = cyl(80, 10, (0, 0, 94)).cut(cyl(68, 12, (0, 0, 93)))
    wheel = wheel.union(cyl(23, 10, (0, 0, 94)))
    for a in [0, 60, 120]:
        wheel = wheel.union(box(150, 14, 10, (0, 0, 94)).rotate((0, 0, 0), (0, 0, 1), a))
    power = power.union(wheel)
    parts["04_power_screw_wheel"] = power

    # Tray native orientation: die faces up, base at Z=0; body 10 mm thick.
    tray = box(68, 56, 10, (0,-2,0))
    tongue = xz_prism([(-25.5, -7.6), (25.5, -7.6), (17.9, 0), (-17.9, 0)], -29.6, 55.6)
    tray = tray.union(tongue)
    pocket = cyl(21.3, 4, (0, 0, 7.5)).union(box(6.6, 4.3, 4, (0, 21.65, 7.5)))
    tray = tray.cut(pocket)
    tray = tray.cut(cyl(4.4, 20, (27, -25, -8)))
    tray = tray.cut(cyl(7.5, 7, (27, -25, 4)))
    # Captive, screw-driven radial wedge. 2:1 slope; toe stays below die face.
    wedge_channel = xz_prism([(-31, 2), (-20.6, 2), (-20.6, 10.4), (-35.2, 10.4)], -6.4, 12.8)
    tray = tray.cut(wedge_channel)
    tray = tray.cut(thread(6, 2, 5, .25, .14).translate((-29, 0, -1)))
    tray = tray.cut(cyl(6.3,4,(-29,0,7.1)))
    parts["06_tray_lower"] = tray
    # Reflect the locating/clamping side, but rebuild its thread right-handed.
    upper_tray = tray.mirror("YZ").union(cyl(3.5,2,(29,0,0)))
    upper_tray = upper_tray.cut(thread(6,2,5,.25,.14).translate((29,0,-1)))
    parts["07_tray_upper"] = upper_tray
    wedge = xz_prism([(-32, 4), (-24, 4), (-20.7, 7.5), (-20.7, 10.2), (-35.1, 10.2)], -6, 12)
    wedge = wedge.cut(cyl(3.35, 12, (-29, 0, 0)))
    wedge = wedge.cut(cyl(6.3, 5, (-29, 0, 7.1)))
    # Remove nonfunctional knife-edge horns around the recessed screw head.
    wedge = wedge.cut(box(30,20,5,(-38,0,7.1)))
    parts["08_die_clamp_wedge"] = wedge
    parts["09_die_clamp_screw"] = bolt(6, 2, 7, 12, 3)

    # Guided ram. The front-facing diagonal rail surfaces are biased into contact
    # by two rear thrust screws. Seat datum Y is compensated for this take-up.
    ram = box(68, 68, 32, (0, 2, 0))
    tongue_xy = [(-14, 36), (14, 36), (30, 52), (-30, 52)]
    ram = ram.union(poly_z(tongue_xy, 0, 32))
    # Dedicated opening stops contact the nut flange at 10 mm die opening.
    for x in [-27,27]:
        ram = ram.union(cyl(4,10.9,(x,.7,32)))
    # Upper tray insertion slot (working face downward), offset Y=+0.35.
    ram = ram.cut(xz_prism([(-18.6, -.01), (18.6, -.01), (26.6, 8.4), (-26.6, 8.4)], -35, 61.7))
    # Foot recess is a 24.6 mm bearing pocket and 4 mm keeper shelf.
    ram = ram.cut(cyl(12.35, 8, (0, .7, 26)))
    for x in [-16, 16]:
        ram = ram.cut(thread(8, 3, 14, .3, .16).translate((x, 16.7, 18)))
    for x in [-10, 10]:
        ram = ram.cut(axis_y(cyl(5.4, 68.1)).translate((x, -32.1, 16)))
        ram = ram.cut(axis_y(thread(10, 3, 18, .3, .16)).translate((x, 36, 16)))
    ram = ram.cut(flip(small_cut).translate((27, -24.3, 14)))
    parts["05_guided_ram"] = ram
    keeper = box(42, 42, 4, (0, .7, 32.2))
    keeper = keeper.cut(box(16.7, 30, 6, (0, -14.3, 31.5)))
    keeper = keeper.cut(cyl(8.35, 6, (0, .7, 31.5)))
    for x in [-16, 16]:
        keeper = keeper.cut(cyl(4.4, 6, (x, 16.7, 31.5)))
    parts["10_foot_keeper"] = keeper
    parts["11_keeper_screw"] = bolt(8, 3, 14, 14, 5)
    parts["12_guide_adjuster"] = cyl(4, 68).union(thread(10, 3, 17.05).translate((0, 0, 68))).union(
        cq.Workplane("XY").polygon(6, 17).extrude(6).translate((0, 0, -6)))
    parts["13_tray_retainer"] = bolt(8, 3, 14, 14, 6)
    parts["14_frame_tie_bolt"] = bolt(14, 4, 84, 25, 10)
    nut_tie = cq.Workplane("XY").polygon(6, 25).extrude(12)
    nut_tie = nut_tie.cut(thread(14, 4, 12, .3, .16))
    parts["15_frame_tie_nut"] = nut_tie
    parts["16_alignment_gauge_TOOL"] = cyl(21,16).union(box(6,3.3,16,(0,21.85,0)))

    return parts


def die_envelope():
    # Exact source interface (0.8 mm overlap), plus asymmetric reference marks
    # are documented, not added to the dimensional mating envelope.
    return cyl(21, 3).union(box(6, 3.3, 3, (0, 21.85, 0)))


def assembly(parts, opening=0, exploded=False):
    if exploded:
        normal=assembly(parts,opening,False)
        offsets={"frame_left":(-90,0,0),"frame_right":(90,0,0),
            "power_nut":(0,0,85),"power_screw":(0,0,150),
            "guided_ram":(0,-85,40),"foot_keeper":(0,-110,85),
            "lower_tray":(0,-105,-10),"upper_tray":(0,-105,25),
            "lower_die_ENVELOPE_NOT_PRINT":(0,-150,-10),
            "upper_die_ENVELOPE_NOT_PRINT":(0,-150,35),
            "lower_clamp":(-50,-105,-10),"upper_clamp":(-50,-105,25),
            "lower_clamp_screw":(-75,-105,-10),"upper_clamp_screw":(-75,-105,25),
            "lower_tray_retainer":(40,-105,-20),"upper_tray_retainer":(40,-105,45)}
        for name in normal:
            if name.startswith("keeper_screw"):offsets[name]=(0,-110,115)
            if name.startswith("guide_adjuster"):offsets[name]=(0,-160,40)
            if name.startswith("tie_bolt"):offsets[name]=(-200,0,0)
            if name.startswith("tie_nut"):offsets[name]=(120,0,0)
        return {name:part.translate(offsets[name]) for name,part in normal.items()}
    d = {}
    def add(name, part, xyz=(0, 0, 0)):
        d[name] = part.translate(xyz)
    add("frame_left", parts["01_frame_left"], (-65 if exploded else 0, 0, 0))
    add("frame_right", parts["02_frame_right"], (65 if exploded else 0, 0, 0))
    add("power_nut", parts["03_power_nut"], (0, 0, 70 if exploded else 0))
    lift_play = .55 if opening > 0 else 0
    add("power_screw", parts["04_power_screw_wheel"].rotate((0, 0, 0), (0, 0, 1), 360 * (opening + lift_play) / PITCH),
        (0, 0, FOOT_Z + opening + lift_play + (110 if exploded else 0)))
    ram_at = (0, RAM_Y, RAM_Z + opening)
    add("guided_ram", parts["05_guided_ram"], (0, -65 if exploded else RAM_Y, ram_at[2]))
    add("lower_tray", parts["06_tray_lower"], (0, -90 if exploded else 0, 32))
    add("upper_tray", flip(parts["07_tray_upper"]), (0, -90 if exploded else 0, RAM_Z + opening))
    add("lower_die_ENVELOPE_NOT_PRINT", die_envelope(), (.3, -90 if exploded else 0, 39.5))
    add("upper_die_ENVELOPE_NOT_PRINT", flip(die_envelope()), (.3, -90 if exploded else 0, 45.6 + opening))
    add("lower_clamp", parts["08_die_clamp_wedge"], (0, -90 if exploded else 0, 32))
    add("upper_clamp", flip(parts["08_die_clamp_wedge"].mirror("YZ")), (0, -90 if exploded else 0, RAM_Z + opening))
    add("lower_clamp_screw", flip(parts["09_die_clamp_screw"]).rotate((0,0,0),(0,0,1),198), (-29, -90 if exploded else 0, 39.1))
    add("upper_clamp_screw", parts["09_die_clamp_screw"].rotate((0,0,0),(0,0,1),162), (-29, -90 if exploded else 0, RAM_Z + opening - 7.1))
    add("foot_keeper", parts["10_foot_keeper"], (0, -65 if exploded else RAM_Y, RAM_Z + opening))
    for x in [-16, 16]:
        add(f"keeper_screw_{x}", flip(parts["11_keeper_screw"]).rotate((0,0,0),(0,0,1),204), (x, 16, RAM_Z + opening + 36.2))
    for x in [-10, 10]:
        add(f"guide_adjuster_{x}", axis_y(parts["12_guide_adjuster"]), (x, -32.7, RAM_Z + opening + 16))
    add("lower_tray_retainer", flip(parts["13_tray_retainer"]).rotate((0,0,0),(0,0,1),180), (27, -25, 36))
    add("upper_tray_retainer", parts["13_tray_retainer"].rotate((0,0,0),(0,0,1),180), (27, -25, RAM_Z + opening - 4))
    for i, (y, z) in enumerate([(65, 16), (65, 66), (65, 124)]):
        add(f"tie_bolt_{i}", axis_x(parts["14_frame_tie_bolt"]), (-36, y, z))
        add(f"tie_nut_{i}", axis_x(parts["15_frame_tie_nut"]), (36, y, z))
    return d


QUANTITIES = {"08_die_clamp_wedge": 2, "09_die_clamp_screw": 2,
              "11_keeper_screw": 2, "12_guide_adjuster": 2,
              "13_tray_retainer": 2, "14_frame_tie_bolt": 3, "15_frame_tie_nut": 3}


def print_shape(name, part):
    if name in ("01_frame_left", "02_frame_right"):
        part = part.rotate((0, 0, 0), (0, 1, 0), -90 if name.endswith("left") else 90)
    elif name == "04_power_screw_wheel":
        part = flip(part)
    elif name == "05_guided_ram":
        part = part.rotate((0, 0, 0), (1, 0, 0), 90)
    elif name in ("06_tray_lower", "07_tray_upper"):
        # Rear edge on bed: bearing floor vertical, dovetail extrudes vertically.
        part = part.rotate((0,0,0),(1,0,0),-90)
    b = part.val().BoundingBox()
    return part.translate((-(b.xmin + b.xmax) / 2, -(b.ymin + b.ymax) / 2, -b.zmin))


def export(parts, out):
    for folder in ["stl", "step", "assemblies", "validation", "images"]:
        (out / folder).mkdir(parents=True, exist_ok=True)
    rows = []
    for name, part in parts.items():
        if not part.val().isValid() or len(part.solids().vals()) != 1:
            raise RuntimeError(f"Invalid or disconnected CAD part: {name}")
        p = print_shape(name, part)
        b = p.val().BoundingBox()
        cq.exporters.export(p, str(out / "stl" / f"{name}.stl"), tolerance=.035, angularTolerance=.12)
        cq.exporters.export(p, str(out / "step" / f"{name}.step"))
        rows.append(dict(part=name, quantity=QUANTITIES.get(name, 1), x_mm=round(b.xlen, 2),
                         y_mm=round(b.ylen, 2), z_mm=round(b.zlen, 2),
                         solid_cm3=round(p.val().Volume() / 1000, 3)))
        print(f"Exported {name}: {b.xlen:.1f} x {b.ylen:.1f} x {b.zlen:.1f}", flush=True)
    colors = [(0.20, .29, .35), (.17, .52, .53), (.93, .57, .18), (.70, .72, .75)]
    for state, op, ex in [("closed", 0, False), ("open", STROKE, False), ("exploded", 0, True)]:
        assy = cq.Assembly(name=f"All_PLA_press_{state}")
        items = assembly(parts, op, ex)
        for i, (name, part) in enumerate(items.items()):
            color = colors[2] if "ENVELOPE" in name else colors[i % len(colors)]
            assy.add(part, name=name, color=cq.Color(*color))
        assy.export(str(out / "assemblies" / f"{state}.step"))
        cq.exporters.export(cq.Compound.makeCompound([s.val() for s in items.values()]),
                            str(out / "assemblies" / f"{state}_VIEW_ONLY.stl"), tolerance=.05)
    (out / "bom.json").write_text(json.dumps({"external_hardware_required": 0, "parts": rows}, indent=2))
    with (out / "BOM.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    print("Building original screw press...", flush=True)
    parts = build()
    export(parts, args.out)
