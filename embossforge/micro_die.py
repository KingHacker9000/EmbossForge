from __future__ import annotations

from dataclasses import asdict
import json
import math
from pathlib import Path

from .config import DieSpec
from .scad_backend import generate_die_pair


BUTTERFLY_SVG = """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"-8 -8 16 16\">\n  <g fill=\"black\">\n    <ellipse cx=\"-3.0\" cy=\"-2.4\" rx=\"3.3\" ry=\"3.4\"/>\n    <ellipse cx=\"3.0\" cy=\"-2.4\" rx=\"3.3\" ry=\"3.4\"/>\n    <ellipse cx=\"-3.4\" cy=\"2.6\" rx=\"2.5\" ry=\"2.3\"/>\n    <ellipse cx=\"3.4\" cy=\"2.6\" rx=\"2.5\" ry=\"2.3\"/>\n    <rect x=\"-0.75\" y=\"-4.7\" width=\"1.5\" height=\"9.4\" rx=\"0.65\"/>\n    <circle cx=\"0\" cy=\"-5.25\" r=\"1.0\"/>\n  </g>\n</svg>\n"""


def micro_butterfly_spec(*, paper_thickness_mm: float = 0.10) -> DieSpec:
    """Tiny but printable matched die intended for a first embossing test.

    The 16 mm carrier is deliberately simple enough for a 0.4 mm nozzle while
    keeping the complete solid pair near one gram of PLA before printer purge.
    """
    spec = DieSpec(
        diameter_mm=16.0,
        base_thickness_mm=1.8,
        relief_height_mm=0.45,
        female_xy_clearance_mm=0.20,
        female_extra_depth_mm=0.10,
        paper_thickness_mm=paper_thickness_mm,
        margin_mm=1.5,
        facets=96,
        key_width_mm=3.5,
        key_depth_mm=1.5,
    )
    spec.validate()
    return spec


def _solid_pair_mass_upper_bound_g(spec: DieSpec, *, pla_density_g_cm3: float = 1.24) -> float:
    """Conservative fully-solid PLA mass bound for both dies.

    The female cavity is ignored and the male relief is pessimistically treated
    as filling the entire safe artwork circle, so real sliced material should be
    below this value (apart from printer purge/prime material).
    """
    overlap_mm = 0.5
    carrier_area_mm2 = (
        math.pi * (spec.diameter_mm / 2) ** 2
        + spec.key_width_mm * (spec.key_depth_mm + overlap_mm)
    )
    pair_base_volume_mm3 = 2 * carrier_area_mm2 * spec.base_thickness_mm
    male_relief_bound_mm3 = math.pi * spec.artwork_radius_mm**2 * spec.relief_height_mm
    volume_cm3 = (pair_base_volume_mm3 + male_relief_bound_mm3) / 1000.0
    return volume_cm3 * pla_density_g_cm3


def export_micro_butterfly_test(
    out_dir: str | Path,
    *,
    paper_thickness_mm: float = 0.10,
) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    spec = micro_butterfly_spec(paper_thickness_mm=paper_thickness_mm)
    artwork = out / "micro_butterfly.svg"
    artwork.write_text(BUTTERFLY_SVG, encoding="utf-8")

    outputs = generate_die_pair(
        artwork,
        out,
        "micro_butterfly",
        spec,
        render_stl=True,
    )

    mass_bound = _solid_pair_mass_upper_bound_g(spec)
    manifest = out / "micro_butterfly_test_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "purpose": "Ultra-low-filament first real male/female embossing test",
                "design": "simple butterfly silhouette",
                "spec": asdict(spec),
                "solid_pair_mass_upper_bound_g": round(mass_bound, 3),
                "printing_note": (
                    "Slice the male and female STL together at 100% scale. "
                    "Trust FlashPrint's material estimate before printing and leave extra filament for printer purge/prime."
                ),
                "use_note": (
                    "This pair is meant for light test embossing only. Align the hidden tabs, place paper between the faces, "
                    "and press gently between two flat hard surfaces or with a small clamp/pliers with flat jaws."
                ),
                "outputs": {key: str(value) for key, value in outputs.items()},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = {key: str(value) for key, value in outputs.items()}
    result["artwork"] = str(artwork)
    result["test_manifest"] = str(manifest)
    result["solid_pair_mass_upper_bound_g"] = f"{mass_bound:.2f}"
    return result
