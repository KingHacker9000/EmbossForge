from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

from . import __version__
from .calibration import write_calibration_pack
from .config import PAPER_PRESETS_MM, PrinterProfile
from .generator import DieGenerationRequest, generate_die
from .mechanics import CartridgeSpec, PressSpec, export_mini_test_pack, export_press_pack
from .mechanics.fit_coupon import export_fit_coupon
from .micro_die import export_micro_butterfly_test
from .relief import ArtworkMode, ReliefPolarity, ReliefSpec, ReliefStyle, SourceInterpretation
from .scad_backend import find_openscad, render_scad


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="embossforge",
        description="Generate printable embossing dies and press hardware",
    )
    parser.add_argument("--version", action="version", version=f"EmbossForge {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Check the local CAD/toolchain installation")
    sub.add_parser("gui", help="Launch the desktop app")

    die = sub.add_parser("die", help="Generate a matched male/female die pair")
    die.add_argument("artwork", type=Path, help="SVG, PNG, JPG, BMP, TIFF, or WEBP artwork")
    die.add_argument("--out", type=Path, default=Path("build"), help="Output directory")
    die.add_argument("--name", help="Output stem; defaults to the artwork filename")
    die.add_argument("--diameter", type=float, default=42.0, help="Die diameter in mm")
    die.add_argument("--base", type=float, default=3.0, help="Die base thickness in mm")
    die.add_argument("--relief", type=float, default=0.65, help="Binary relief height / relief-mode default max in mm")
    die.add_argument("--mode", choices=[m.value for m in ArtworkMode], default="binary", help="binary or variable-depth relief")
    die.add_argument(
        "--source-interpretation",
        choices=[s.value for s in SourceInterpretation],
        default=None,
        help="What uploaded pixels mean: flat-artwork, height-map, or shaded-reference",
    )
    die.add_argument("--relief-max", type=float, default=None, help="Maximum variable-depth relief in mm")
    die.add_argument(
        "--relief-style",
        choices=[s.value for s in ReliefStyle],
        default="stepped",
        help="Variable-depth mapping style",
    )
    die.add_argument("--relief-levels", type=int, default=6, help="Number of levels for stepped relief")
    die.add_argument("--relief-gamma", type=float, default=1.0, help="Relief tone response gamma")
    die.add_argument(
        "--relief-polarity",
        choices=[p.value for p in ReliefPolarity],
        default="dark-high",
        help="Which grayscale direction maps to higher relief",
    )
    die.add_argument(
        "--relief-zero-threshold",
        type=float,
        default=0.02,
        help="Normalized low-relief dead zone from 0 to 1",
    )
    die.add_argument("--relief-smoothing", type=float, default=0.0, help="Relief smoothing radius in mm")
    die.add_argument(
        "--relief-quality",
        choices=["draft", "balanced", "fine"],
        default="balanced",
        help="Height-field sampling quality",
    )
    die.add_argument(
        "--keep-subresolution-relief",
        action="store_true",
        help="Do not remove positive relief below the selected printer's feature resolution",
    )
    die.add_argument(
        "--allow-risky",
        action="store_true",
        help="Allow high experimental paper-risk findings; cannot bypass invalid/mating geometry",
    )
    die.add_argument(
        "--clearance",
        type=float,
        default=None,
        help="Female XY clearance in mm; defaults to printer profile recommendation or 0.20 mm",
    )
    die.add_argument(
        "--paper",
        choices=sorted(PAPER_PRESETS_MM),
        help="Paper thickness preset; overridden by --paper-thickness",
    )
    die.add_argument(
        "--paper-thickness",
        type=float,
        default=None,
        help="Exact paper thickness in mm; overrides --paper",
    )
    die.add_argument("--extra-depth", type=float, default=0.20, help="Extra female cavity depth in mm")
    die.add_argument("--margin", type=float, default=3.0, help="Artwork margin from die edge in mm")
    die.add_argument("--threshold", type=int, default=160, help="Raster threshold 0-255 in binary mode")
    die.add_argument("--invert", action="store_true", help="Use for light artwork on a dark background in binary mode")
    die.add_argument(
        "--profile",
        type=Path,
        help="Printer TOML profile; supplies clearance defaults and validates build volume",
    )
    die.add_argument("--scad-only", action="store_true", help="Generate OpenSCAD source but do not render STL")

    calibration = sub.add_parser("calibrate", help="Generate printer/emboss calibration artifacts")
    calibration.add_argument("--out", type=Path, default=Path("build") / "calibration", help="Output directory")
    calibration.add_argument("--scad-only", action="store_true", help="Generate OpenSCAD source but do not render STL")

    mechanics = sub.add_parser("mechanics", help="Generate the V0.2 cartridge and lever-press prototype")
    mechanics.add_argument("--out", type=Path, default=Path("build") / "mechanics", help="Output directory")
    mechanics.add_argument("--die-diameter", type=float, default=42.0, help="Compatible die diameter in mm")
    mechanics.add_argument("--slide-clearance", type=float, default=0.25, help="Cartridge/receiver per-side clearance in mm")
    mechanics.add_argument("--pivot", type=float, default=6.4, help="Pivot bore diameter in mm")

    mini = sub.add_parser(
        "mini-test",
        help="Generate a much smaller low-filament functional throwaway press + die pack",
    )
    mini.add_argument("--out", type=Path, default=Path("build") / "mini-test", help="Output directory")
    mini.add_argument("--slide-clearance", type=float, default=0.25, help="Per-side receiver clearance in mm")
    mini.add_argument("--paper-thickness", type=float, default=0.10, help="Paper thickness in mm")

    fit = sub.add_parser(
        "fit-coupon",
        help="Generate an ultra-small two-piece rail/receiver fit test for scarce filament",
    )
    fit.add_argument("--out", type=Path, default=Path("build") / "fit-coupon", help="Output directory")
    fit.add_argument("--slide-clearance", type=float, default=0.25, help="Per-side clearance in mm")

    butterfly = sub.add_parser(
        "butterfly-test",
        help="Generate an ultra-small real male/female butterfly emboss die pair",
    )
    butterfly.add_argument("--out", type=Path, default=Path("build") / "butterfly-test", help="Output directory")
    butterfly.add_argument("--paper-thickness", type=float, default=0.10, help="Paper thickness in mm")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "doctor":
            return _doctor()
        if args.command == "gui":
            return _gui()
        if args.command == "die":
            return _die(args)
        if args.command == "calibrate":
            return _calibrate(args)
        if args.command == "mechanics":
            return _mechanics(args)
        if args.command == "mini-test":
            return _mini_test(args)
        if args.command == "fit-coupon":
            return _fit_coupon(args)
        if args.command == "butterfly-test":
            return _butterfly_test(args)
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
        cadquery_ok = False
    else:
        version = getattr(cq, "__version__", "installed")
        print(f"CadQuery:   OK  {version}")
        cadquery_ok = True

    try:
        import PySide6  # noqa: F401
    except Exception:
        print("Desktop UI: optional / install with pip install -e \".[gui]\"")
    else:
        print("Desktop UI: OK")

    blender = shutil.which("blender") or shutil.which("blender.exe")
    print(f"Blender:    {'OK  ' + blender if blender else 'optional / not on PATH'}")

    ff = shutil.which("ffmpeg")
    print(f"FFmpeg:     {'OK  ' + ff if ff else 'optional / not found'}")
    return 0 if openscad and cadquery_ok else 1


def _gui() -> int:
    try:
        from .gui import main as gui_main
    except ImportError as exc:
        raise RuntimeError(
            "Desktop UI dependencies are not installed. Run: pip install -e \".[gui]\""
        ) from exc
    return gui_main()


def _die(args: argparse.Namespace) -> int:
    profile = PrinterProfile.from_toml(args.profile) if args.profile else None
    relief_spec = None
    if args.mode == ArtworkMode.RELIEF.value:
        relief_spec = ReliefSpec(
            max_relief_mm=args.relief_max if args.relief_max is not None else args.relief,
            style=ReliefStyle(args.relief_style),
            levels=args.relief_levels,
            gamma=args.relief_gamma,
            polarity=ReliefPolarity(args.relief_polarity),
            zero_threshold=args.relief_zero_threshold,
            smoothing_mm=args.relief_smoothing,
            sampling_quality=args.relief_quality,
            auto_filter_subresolution=not args.keep_subresolution_relief,
        )

    request = DieGenerationRequest(
        artwork=args.artwork,
        output_root=args.out,
        name=args.name,
        diameter_mm=args.diameter,
        base_thickness_mm=args.base,
        relief_height_mm=args.relief,
        clearance_mm=args.clearance,
        paper_preset=args.paper,
        paper_thickness_mm=args.paper_thickness,
        female_extra_depth_mm=args.extra_depth,
        margin_mm=args.margin,
        threshold=args.threshold,
        invert=args.invert,
        render_stl=not args.scad_only,
        printer_profile=profile,
        artwork_mode=ArtworkMode(args.mode),
        source_interpretation=(
            SourceInterpretation(args.source_interpretation) if args.source_interpretation else None
        ),
        relief=relief_spec,
        allow_risky=args.allow_risky,
    )
    result = generate_die(request)

    print(f"Generated die pair: {result.name}")
    print(f"  geometry mode: {result.artwork_mode.value}")
    print(f"  source interpretation: {result.source_interpretation.value}")
    if result.printer_profile is not None:
        print(f"  printer profile: {result.printer_profile.name}")
    print(f"  paper thickness: {result.spec.paper_thickness_mm:.3f} mm ({result.paper_source})")
    print(f"  female clearance: {result.spec.female_xy_clearance_mm:.3f} mm ({result.clearance_source})")
    print(f"  validation: {result.validation.highest_severity.value} [{result.validation.verification_level}]")
    for finding in result.validation.findings:
        print(f"    {finding.severity.value}: {finding.message}")
    print(f"  processed artwork: {result.normalized_artwork}")
    for key, path in result.outputs.items():
        print(f"  {key}: {path}")
    return 0


def _calibrate(args: argparse.Namespace) -> int:
    outputs = write_calibration_pack(args.out)
    if not args.scad_only:
        rendered: dict[str, str] = {}
        for name, source in outputs.items():
            target = Path(source).with_suffix(".stl")
            render_scad(source, target)
            rendered[f"{name}_stl"] = str(target)
        outputs.update(rendered)

    print("Generated calibration pack")
    for key, path in outputs.items():
        print(f"  {key}: {path}")
    return 0


def _mechanics(args: argparse.Namespace) -> int:
    cartridge = CartridgeSpec(
        die_diameter_mm=args.die_diameter,
        receiver_slide_clearance_mm=args.slide_clearance,
    )
    press = PressSpec(pivot_diameter_mm=args.pivot)
    outputs = export_press_pack(args.out, cartridge=cartridge, press=press)

    print("Generated V0.2 mechanical prototype")
    print(f"  nominal lever ratio: {press.nominal_lever_ratio:.2f}:1")
    for key, path in outputs.items():
        print(f"  {key}: {path}")
    return 0


def _mini_test(args: argparse.Namespace) -> int:
    outputs = export_mini_test_pack(
        args.out,
        slide_clearance_mm=args.slide_clearance,
        paper_thickness_mm=args.paper_thickness,
    )
    print("Generated low-filament miniature functional test pack")
    print("  NOTE: this is for fit/motion/light-emboss validation, not full-strength testing")
    for key, path in outputs.items():
        print(f"  {key}: {path}")
    return 0


def _fit_coupon(args: argparse.Namespace) -> int:
    outputs = export_fit_coupon(args.out, slide_clearance_mm=args.slide_clearance)
    print("Generated ultra-low-filament rail fit coupon")
    print(f"  STL: {outputs['stl']}")
    print(f"  STEP: {outputs['step']}")
    print(f"  manifest: {outputs['manifest']}")
    print(f"  solid PLA mass upper bound: {outputs['solid_pla_mass_upper_bound_g']:.2f} g")
    print("  IMPORTANT: trust your slicer's material estimate before printing")
    return 0


def _butterfly_test(args: argparse.Namespace) -> int:
    outputs = export_micro_butterfly_test(args.out, paper_thickness_mm=args.paper_thickness)
    print("Generated micro butterfly male/female emboss test")
    print("  die diameter: 16 mm")
    print(f"  male STL: {outputs['male_stl']}")
    print(f"  female STL: {outputs['female_stl']}")
    print(f"  artwork: {outputs['artwork']}")
    print(f"  manifest: {outputs['test_manifest']}")
    print(f"  conservative solid pair mass upper bound: {outputs['solid_pair_mass_upper_bound_g']} g")
    print("  IMPORTANT: slice both at 100% scale and trust your slicer's estimate before printing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
