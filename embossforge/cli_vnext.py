from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import cli as legacy
from .mechanics import export_hand_lever_press_pack, export_micro_press_pack


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


def _lever_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="embossforge lever-press",
        description=(
            "Generate the V5 all-3D-printable hand lever embosser for the existing "
            "standard 42 mm keyed die pair."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("build") / "lever-press",
        help="Output directory",
    )
    parser.add_argument(
        "--die-clearance",
        type=float,
        default=0.20,
        help="Nominal per-side clearance around the standard 42 mm keyed die in mm",
    )
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


def _run_lever(argv: list[str]) -> int:
    args = _lever_parser().parse_args(argv)
    outputs = export_hand_lever_press_pack(
        args.out,
        die_pocket_clearance_mm=args.die_clearance,
    )
    print("Generated V5 all-3D-printable 42 mm lever embosser")
    print("  compatible dies: existing standard 42 mm EmbossForge keyed male/female pair")
    print("  mechanism: guided upper carriage + forked lever + printed slotted hinge pins")
    print("  retainers: 2 x printed cotter-style retaining wedge")
    print("  external hardware: NONE")
    print("  printed quantities: body x1, upper_carriage x1, lever x1, main_pivot_pin x1, drive_pin x1, retaining_wedge x2")
    print(f"  assembly closed STEP: {outputs['assembly_closed_step']}")
    print(f"  assembly open STEP:   {outputs['assembly_open_step']}")
    print(f"  manifest:             {outputs['manifest']}")
    print("  NOTE: CAD/CI validated; first physical V5 strength/fit test is still pending")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "micro-press":
        try:
            return _run_micro(args[1:])
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    if args and args[0] == "lever-press":
        try:
            return _run_lever(args[1:])
        except (FileNotFoundError, ValueError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    return legacy.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
