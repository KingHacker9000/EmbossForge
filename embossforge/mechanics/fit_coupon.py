from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .cad import build_cartridge, build_receiver, export_part
from .mini import mini_cartridge_spec


PLA_DENSITY_G_PER_CM3 = 1.24


@dataclass(frozen=True)
class FitCouponSpec:
    """Small section of the real mini cartridge/receiver interface.

    The coupon is produced by clipping the actual source-generated cartridge and
    receiver, so rail height, groove height and slide clearance are identical to
    the miniature press rather than being reimplemented approximately.
    """

    sample_length_mm: float = 14.0
    cartridge_body_sample_mm: float = 6.0
    receiver_outer_sample_mm: float = 9.0
    plate_separation_mm: float = 5.0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive")


def _cq():
    try:
        import cadquery as cq
    except ImportError as exc:  # pragma: no cover - optional CAD dependency
        raise RuntimeError(
            "CadQuery is required for fit-coupon generation. Install with: pip install -e \".[cad]\""
        ) from exc
    return cq


def build_fit_coupon_parts(
    *,
    slide_clearance_mm: float = 0.25,
    spec: FitCouponSpec = FitCouponSpec(),
) -> dict[str, Any]:
    """Return tiny slider and receiver slices preserving the real rail fit."""
    spec.validate()
    cartridge_spec = mini_cartridge_spec(slide_clearance_mm=slide_clearance_mm)
    cq = _cq()

    cartridge = build_cartridge(cartridge_spec)
    receiver = build_receiver(cartridge_spec)

    # Sample the +X cartridge rail and its matching +X receiver groove. The Y
    # section is intentionally short to save filament while still requiring a
    # real sliding insertion rather than a simple press-fit snap.
    body_half = cartridge_spec.body_width_mm / 2
    rail_extension = cartridge_spec.side_rail_extension_mm
    receiver_half = cartridge_spec.receiver_outer_width_mm / 2

    slider_x0 = body_half - spec.cartridge_body_sample_mm
    slider_x1 = body_half + rail_extension + 0.5
    slider_clip = (
        cq.Workplane("XY")
        .box(
            slider_x1 - slider_x0,
            spec.sample_length_mm,
            cartridge_spec.body_thickness_mm + 1.0,
            centered=(True, True, False),
        )
        .translate(((slider_x0 + slider_x1) / 2, 0, -0.5))
    )
    slider = cartridge.intersect(slider_clip).translate((-slider_x0, 0, 0))

    receiver_x0 = receiver_half - spec.receiver_outer_sample_mm
    receiver_x1 = receiver_half + 0.5
    receiver_clip = (
        cq.Workplane("XY")
        .box(
            receiver_x1 - receiver_x0,
            spec.sample_length_mm,
            cartridge_spec.receiver_height_mm + 1.0,
            centered=(True, True, False),
        )
        .translate(((receiver_x0 + receiver_x1) / 2, 0, -0.5))
    )
    receiver_sample = receiver.intersect(receiver_clip).translate((-receiver_x0, 0, 0))

    return {"slider": slider, "receiver": receiver_sample}


def build_fit_coupon_pair(
    *,
    slide_clearance_mm: float = 0.25,
    spec: FitCouponSpec = FitCouponSpec(),
):
    """Arrange both coupon pieces in one STL-ready compound on the build plate."""
    cq = _cq()
    parts = build_fit_coupon_parts(slide_clearance_mm=slide_clearance_mm, spec=spec)

    slider = parts["slider"]
    receiver = parts["receiver"]
    sb = slider.val().BoundingBox()
    rb = receiver.val().BoundingBox()

    slider = slider.translate((-sb.xmin, -sb.ymin, -sb.zmin))
    receiver = receiver.translate((-rb.xmin, -rb.ymin, -rb.zmin))
    receiver = receiver.translate((sb.xlen + spec.plate_separation_mm, 0, 0))

    return cq.Compound.makeCompound([slider.val(), receiver.val()])


def export_fit_coupon(
    out_dir: str | Path,
    *,
    slide_clearance_mm: float = 0.25,
) -> dict[str, str | float]:
    """Export one tiny two-piece STL plus a manifest with a solid-mass ceiling."""
    if slide_clearance_mm < 0:
        raise ValueError("slide_clearance_mm cannot be negative")

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pair = build_fit_coupon_pair(slide_clearance_mm=slide_clearance_mm)

    stl = export_part(pair, out / "rail_fit_coupon_pair.stl")
    step = export_part(pair, out / "rail_fit_coupon_pair.step")

    solid_volume_mm3 = float(pair.Volume())
    solid_pla_mass_g = solid_volume_mm3 / 1000.0 * PLA_DENSITY_G_PER_CM3

    manifest = out / "rail_fit_coupon_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "purpose": "Ultra-low-filament check of the miniature cartridge rail/receiver slide fit",
                "slide_clearance_mm": slide_clearance_mm,
                "solid_volume_mm3": round(solid_volume_mm3, 2),
                "solid_pla_mass_upper_bound_g": round(solid_pla_mass_g, 2),
                "note": (
                    "The slicer estimate is the number to trust before printing. The solid PLA mass is a conservative "
                    "upper bound from CAD volume; normal sliced mass should be lower."
                ),
                "pass_criteria": (
                    "After removing brim/support artifacts, the slider should enter from the end, move through the "
                    "receiver by hand, and have little visible side-to-side slop."
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "stl": str(stl),
        "step": str(step),
        "manifest": str(manifest),
        "solid_volume_mm3": solid_volume_mm3,
        "solid_pla_mass_upper_bound_g": solid_pla_mass_g,
    }
