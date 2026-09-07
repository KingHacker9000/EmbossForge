from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import shutil
import sys

from . import __version__
from .artwork import normalize_artwork
from .config import DieSpec
from .scad_backend import find_openscad, generate_die_pair


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="embossforge", description="Generate printable embossing dies from artwork")
    parser.add_argument("--version", action="version", version=f"EmbossForge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check the local CAD/toolchain installation")

    die = sub.add_parser("die", help="Generate a matched male/female die pair")
    die.add_argument("artwork", type=Path, help="SVG, PNG, JPG, BMP, TIFF, or WEBP artwork")
    die.add_argument("--out", type=Path, default=Path("build"), help="Output directory")
    die.add_argument("--name", help="Output stem; defaults to the artwork filename")
    die.add_argument("--diameter", type=float, default=42.0, help="Die diameter in mm")
    die.add_argument("--base", type=float, default=3.0, help="Die base thickness in mm")
    die.add_argument("--relief", type=float, default=0.65, help="Male relief height in mm")
    die.add_argument("--clearance", type=float, default=0.20, help="Female XY clearance around artwork in mm")
    die.add_argument("--paper-thickness", type=float, default=0.10, help="Paper thickness in mm")
    die.add_argument("--extra-depth", type=float, default=0.20, help="Extra female cavity depth in mm")
    die.add_argument("--margin", type=float, default=3.0, help="Artwork margin from die edge in mm")
    die.add_argument("--threshold", type=int, default=160, help="Raster threshold 0-255")
    die.add_argument("--invert", action="store_true", help="Use for light artwork on a dark background")
    die.add_argument("--scad-only", action="store_true", help="Generate OpenSCAD source but do not render STL")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            return _doctor()
        if args.command == "die":
            return _die(args)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


def _doctor() -> int:
    print(f"EmbossForge {__version__}")
    print(f"Python:    {sys.version.split()[0]}  [{sys.executable}]")

    openscad = find_openscad()
    print(f"OpenSCAD:  {'OK  ' + str(openscad) if openscad else 'NOT FOUND'}")

    try:
        import cadquery as cq  # noqa: F401
    except Exception as exc:
        print(f"CadQuery:   NOT AVAILABLE ({exc})")
    else:
        version = getattr(cq, "__version__", "installed")
        print(f"CadQuery:   OK  {version}")

    ff = shutil.which("ffmpeg")
    print(f"FFmpeg:     {'OK  ' + ff if ff else 'optional / not found'}")
    return 0 if openscad else 1


def _die(args: argparse.Namespace) -> int:
    name = args.name or args.artwork.stem
    out = args.out / name
    normalized = out / f"{name}_normalized.svg"

    normalize_artwork(
        args.artwork,
        normalized,
        threshold=args.threshold,
        invert=args.invert,
    )

    spec = replace(
        DieSpec(),
        diameter_mm=args.diameter,
        base_thickness_mm=args.base,
        relief_height_mm=args.relief,
        female_xy_clearance_mm=args.clearance,
        paper_thickness_mm=args.paper_thickness,
        female_extra_depth_mm=args.extra_depth,
        margin_mm=args.margin,
    )
    outputs = generate_die_pair(normalized, out, name, spec, render_stl=not args.scad_only)

    print(f"Generated die pair: {name}")
    print(f"  normalized artwork: {normalized}")
    for key, path in outputs.items():
        print(f"  {key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
