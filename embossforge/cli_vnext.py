from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import cli as legacy
from .mechanics import export_micro_press_pack


def _micro_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="embossforge micro-press",
        description=(
            "Generate the ultra-light one-piece PLA flexure tongs made specifically "
            "for the existing 16 mm butterfly-test die pair."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("build") / "micro-press",
        help="Output directory",
    )
    parser.add_argument(
        "--die-clearance",
        type=float,
        default=0.15,
        help="Per-side clearance around the existing 16 mm butterfly die in mm",
    )
    # Kept so commands copied from the first experimental micro-press revision
    # do not fail; there are no sliding parts in the flexure-tongs design.
    parser.add_argument("--slide-clearance", type=float, default=0.25, help=argparse.SUPPRESS)
    return parser


def _run_micro(argv: list[str]) -> int:
    args = _micro_parser().parse_args(argv)
    outputs = export_micro_press_pack(
        args.out,
        slide_clearance_mm=args.slide_clearance,
        die_pocket_clearance_mm=args.die_clearance,
    )
    print("Generated one-piece Micro Embosser flexure tongs")
    print("  compatible dies: exact existing 16 mm butterfly-test male/female pair")
    print("  mechanism: two long PLA spring arms + direct keyed die sockets")
    print("  hardware: none")
    print(f"  STL: {outputs['stl']}")
    print(f"  STEP: {outputs['step']}")
    print(f"  manifest: {outputs['micro_manifest']}")
    print(f"  conservative all-solid PLA mass upper bound: {outputs['solid_pla_mass_upper_bound_g']} g")
    print("  IMPORTANT: trust FlashPrint's sliced grams estimate before printing")
    print("  NOTE: light hand-force prototype; avoid repeatedly over-flexing PLA")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "micro-press":
        try:
            return _run_micro(args[1:])
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    return legacy.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
