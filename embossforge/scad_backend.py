from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .config import DieSpec


DEFAULT_OPENSCAD_TIMEOUT_SECONDS = 180


def _bundled_tool_candidates() -> list[Path]:
    """Return OpenSCAD locations used by PyInstaller/portable releases."""
    roots: list[Path] = []
    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            roots.append(Path(meipass))
    return [root / "tools" / "openscad" / "openscad.exe" for root in roots]


def find_openscad() -> Path | None:
    candidates: list[Path] = []
    candidates.extend(_bundled_tool_candidates())
    found = shutil.which("openscad") or shutil.which("OpenSCAD")
    if found:
        candidates.append(Path(found))
    candidates.extend(
        [
            Path(r"C:\Program Files\OpenSCAD\openscad.exe"),
            Path(r"C:\Program Files (x86)\OpenSCAD\openscad.exe"),
            Path("/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"),
            Path("/usr/bin/openscad"),
            Path("/usr/local/bin/openscad"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _render_timeout_seconds() -> int:
    raw = os.environ.get("EMBOSSFORGE_OPENSCAD_TIMEOUT", "").strip()
    if not raw:
        return DEFAULT_OPENSCAD_TIMEOUT_SECONDS
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_OPENSCAD_TIMEOUT_SECONDS
    return max(30, value)


def render_scad(source_scad: str | Path, output_stl: str | Path) -> Path:
    """Render one OpenSCAD source file to STL using local or bundled OpenSCAD.

    Each render is bounded so a pathological height field cannot leave the desktop
    stuck at "Generating…" forever. Advanced users can override the timeout with
    EMBOSSFORGE_OPENSCAD_TIMEOUT (seconds).
    """
    openscad = find_openscad()
    if openscad is None:
        raise RuntimeError(
            "OpenSCAD executable was not found. Install OpenSCAD, add it to PATH, "
            "or use the official EmbossForge portable release that bundles it."
        )
    source = Path(source_scad)
    output = Path(output_stl)
    output.parent.mkdir(parents=True, exist_ok=True)
    _render(openscad, source, output, timeout_seconds=_render_timeout_seconds())
    return output


def generate_die_pair(
    artwork_svg: str | Path,
    output_dir: str | Path,
    name: str,
    spec: DieSpec,
    *,
    render_stl: bool = True,
) -> dict[str, Path]:
    spec.validate()
    art = Path(artwork_svg).resolve()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    male_scad = out / f"{name}_male.scad"
    female_scad = out / f"{name}_female.scad"
    male_stl = out / f"{name}_male.stl"
    female_stl = out / f"{name}_female.stl"
    manifest = out / f"{name}_manifest.json"

    male_scad.write_text(_male_scad(art, spec), encoding="utf-8")
    female_scad.write_text(_female_scad(art, spec), encoding="utf-8")

    outputs: dict[str, Path] = {
        "male_scad": male_scad,
        "female_scad": female_scad,
        "manifest": manifest,
    }

    if render_stl:
        render_scad(male_scad, male_stl)
        render_scad(female_scad, female_stl)
        outputs["male_stl"] = male_stl
        outputs["female_stl"] = female_stl

    manifest.write_text(
        json.dumps(
            {
                "name": name,
                "artwork": str(art),
                "spec": asdict(spec),
                "derived": {
                    "artwork_radius_mm": spec.artwork_radius_mm,
                    "female_cavity_depth_mm": spec.female_cavity_depth_mm,
                    "carrier_depth_mm": spec.carrier_depth_mm,
                },
                "orientation": {
                    "carrier_key": "+Y on both printed inserts",
                    "upper_install_transform": "rotate 180 degrees about Y with the upper cartridge",
                    "female_artwork_compensation": "mirrored in X before extrusion",
                },
                "outputs": {key: str(value) for key, value in outputs.items() if key != "manifest"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return outputs


def _escaped_art_path(art: Path) -> str:
    return str(art).replace("\\", "/").replace('"', '\\"')


def _art_module(art: Path, spec: DieSpec, *, delta: float = 0.0, mirror_x: bool = False) -> str:
    """Return a 2D artwork expression clipped to the safe circular emboss zone."""
    escaped = _escaped_art_path(art)
    mirror = "mirror([1, 0, 0]) " if mirror_x else ""
    clip_radius = spec.artwork_radius_mm
    return (
        "intersection() { "
        f"circle(r={clip_radius:.4f}, $fn={spec.facets}); "
        f"{mirror}offset(delta={delta:.4f}) "
        f"resize([{spec.artwork_box_mm:.4f}, {spec.artwork_box_mm:.4f}], auto=true) "
        f'import(file="{escaped}", center=true); '
        "}"
    )


def _carrier_base_scad(spec: DieSpec) -> str:
    """2D keyed carrier base: round die plus one hidden +Y orientation tab."""
    overlap = 0.5
    tab_depth = spec.key_depth_mm + overlap
    tab_y = spec.diameter_mm / 2 + (spec.key_depth_mm - overlap) / 2
    return (
        "union() { "
        "circle(d=die_d, $fn=$fn); "
        f"translate([0, {tab_y:.4f}]) square([{spec.key_width_mm:.4f}, {tab_depth:.4f}], center=true); "
        "}"
    )


def _male_scad(art: Path, spec: DieSpec) -> str:
    art_expr = _art_module(art, spec)
    base_expr = _carrier_base_scad(spec)
    return f"""// Generated by EmbossForge. Do not edit by hand.
// +Y tab is the hidden angular-orientation key used by the cartridge.
$fn = {spec.facets};

die_d = {spec.diameter_mm:.4f};
base_h = {spec.base_thickness_mm:.4f};
relief_h = {spec.relief_height_mm:.4f};

union() {{
  linear_extrude(height=base_h)
    {base_expr}
  translate([0, 0, base_h])
    linear_extrude(height=relief_h)
      {art_expr}
}}
"""


def _female_scad(art: Path, spec: DieSpec) -> str:
    art_expr = _art_module(art, spec, delta=spec.female_xy_clearance_mm, mirror_x=True)
    base_expr = _carrier_base_scad(spec)
    cavity = spec.female_cavity_depth_mm
    return f"""// Generated by EmbossForge. Do not edit by hand.
// Female artwork is mirrored in X for an upper cartridge flipped 180 degrees about Y.
// The +Y carrier tab remains +Y after that installation transform.
$fn = {spec.facets};

die_d = {spec.diameter_mm:.4f};
base_h = {spec.base_thickness_mm:.4f};
cavity_h = {cavity:.4f};

difference() {{
  linear_extrude(height=base_h)
    {base_expr}
  translate([0, 0, base_h - cavity_h])
    linear_extrude(height=cavity_h + 0.15)
      {art_expr}
}}
"""


def _render(
    openscad: Path,
    source_scad: Path,
    output_stl: Path,
    *,
    timeout_seconds: int,
) -> None:
    try:
        result = subprocess.run(
            [str(openscad), "-o", str(output_stl), str(source_scad)],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        output_stl.unlink(missing_ok=True)
        raise RuntimeError(
            f"OpenSCAD timed out after {timeout_seconds}s rendering {source_scad.name}. "
            "For a variable-depth die, retry with Height-map quality = Draft, fewer height levels, "
            "or a simpler/cleaner height map."
        ) from exc
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "OpenSCAD failed without diagnostic output"
        raise RuntimeError(f"OpenSCAD failed rendering {source_scad.name}: {message}")
