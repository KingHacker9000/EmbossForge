from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math

import cv2
import numpy as np

from .config import DieSpec, PrinterProfile
from .relief import ReliefPolarity, ReliefSpec, ReliefStyle


@dataclass(frozen=True)
class HeightMapResult:
    relief: np.ndarray
    machine_heightmap: Path
    male_surface_map: Path
    width_px: int
    height_px: int
    mm_per_sample: float
    filtered_pixels: int = 0


def build_height_map(
    source: str | Path,
    output_dir: str | Path,
    name: str,
    spec: DieSpec,
    relief_spec: ReliefSpec,
    profile: PrinterProfile | None,
) -> HeightMapResult:
    """Convert a true raster height map into a printer-aware normalized field.

    Machine convention is white=zero and black=max relief. The returned ``relief``
    array is normalized 0..1 with 1=max relief. A separate surface map is written
    with white=max because OpenSCAD's ``surface()`` interprets brighter pixels as
    larger Z values.

    Non-zero relief can optionally be lifted to ``ReliefSpec.min_relief_mm`` so
    grayscale tiers do not collapse into fractions of a printable FDM layer.
    """
    relief_spec.validate()
    src = Path(source)
    if src.suffix.lower() == ".svg":
        raise ValueError(
            "Variable-depth SVG rendering is not enabled yet. Export the authored height map as PNG/TIFF, "
            "or use binary mode for this SVG."
        )

    raw = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    if raw is None:
        raise ValueError(f"Could not read height-map artwork: {src}")

    alpha: np.ndarray | None = None
    if raw.ndim == 2:
        gray = raw
    elif raw.shape[2] == 4:
        alpha = raw[:, :, 3].astype(np.float32) / 255.0
        gray = cv2.cvtColor(raw[:, :, :3], cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(raw[:, :, :3], cv2.COLOR_BGR2GRAY)

    target_px, mm_per_sample = _sampling_target(spec, relief_spec, profile)
    canvas_gray = np.full((target_px, target_px), 255, dtype=np.uint8)
    canvas_alpha = np.zeros((target_px, target_px), dtype=np.float32) if alpha is not None else None

    h, w = gray.shape
    scale = min(target_px / max(1, w), target_px / max(1, h))
    new_w = max(1, min(target_px, int(round(w * scale))))
    new_h = max(1, min(target_px, int(round(h * scale))))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(gray, (new_w, new_h), interpolation=interpolation)
    x0 = (target_px - new_w) // 2
    y0 = (target_px - new_h) // 2
    canvas_gray[y0 : y0 + new_h, x0 : x0 + new_w] = resized

    if alpha is not None and canvas_alpha is not None:
        resized_alpha = cv2.resize(alpha, (new_w, new_h), interpolation=cv2.INTER_AREA)
        canvas_alpha[y0 : y0 + new_h, x0 : x0 + new_w] = resized_alpha

    luminance = canvas_gray.astype(np.float32) / 255.0
    if relief_spec.polarity == ReliefPolarity.DARK_HIGH:
        relief = 1.0 - luminance
    else:
        relief = luminance

    if canvas_alpha is not None:
        relief *= canvas_alpha

    relief = np.clip(relief, 0.0, 1.0)
    relief[relief < relief_spec.zero_threshold] = 0.0
    relief = np.power(relief, relief_spec.gamma).astype(np.float32)

    if relief_spec.smoothing_mm > 0:
        sigma = relief_spec.smoothing_mm / max(mm_per_sample, 1e-9)
        if sigma >= 0.25:
            relief = cv2.GaussianBlur(relief, (0, 0), sigmaX=sigma, sigmaY=sigma)
            relief = np.clip(relief, 0.0, 1.0)
            # Avoid turning the whole nominally-flat field into a shallow fuzzy pad.
            relief[relief < relief_spec.zero_threshold] = 0.0

    relief = _map_to_printable_depth_tiers(relief, relief_spec)
    _apply_circular_artwork_mask(relief, spec)

    filtered_pixels = 0
    if profile is not None and relief_spec.auto_filter_subresolution:
        relief, filtered_pixels = _filter_subresolution_positive_features(relief, mm_per_sample, profile)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    machine = out / f"{name}_heightmap.png"
    surface = out / f"{name}_male_surface.png"

    # Machine map remains white=zero / black=max as documented.
    machine_u8 = np.round((1.0 - relief) * 255.0).astype(np.uint8)
    surface_u8 = np.round(relief * 255.0).astype(np.uint8)
    if not cv2.imwrite(str(machine), machine_u8):
        raise RuntimeError(f"Could not write height map: {machine}")
    if not cv2.imwrite(str(surface), surface_u8):
        raise RuntimeError(f"Could not write relief surface map: {surface}")

    return HeightMapResult(
        relief=relief,
        machine_heightmap=machine,
        male_surface_map=surface,
        width_px=target_px,
        height_px=target_px,
        mm_per_sample=mm_per_sample,
        filtered_pixels=filtered_pixels,
    )


def build_female_surface_map(
    result: HeightMapResult,
    output_dir: str | Path,
    name: str,
    spec: DieSpec,
    relief_spec: ReliefSpec,
) -> tuple[Path, float, np.ndarray]:
    """Create the cavity-depth field from the same canonical male field.

    The press already holds the two nominal die faces apart by the selected paper
    thickness. Therefore the cavity depth is male relief + *extra Z clearance only*.
    Adding paper thickness here as well double-counts it and prevents the paper from
    being driven against the female cavity.
    """
    radius_px = int(math.ceil(spec.female_xy_clearance_mm / max(result.mm_per_sample, 1e-9)))
    source_u8 = np.round(result.relief * 255.0).astype(np.uint8)
    if radius_px > 0:
        kernel_size = 2 * radius_px + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        expanded_u8 = cv2.dilate(source_u8, kernel)
    else:
        expanded_u8 = source_u8

    expanded = expanded_u8.astype(np.float32) / 255.0
    cavity_mm = expanded * relief_spec.max_relief_mm
    cavity_mm[expanded > 0] += spec.female_extra_depth_mm
    max_cavity_mm = relief_spec.max_relief_mm + spec.female_extra_depth_mm

    if max_cavity_mm >= spec.base_thickness_mm:
        raise ValueError(
            "female relief cavity is deeper than the female die base; increase base thickness "
            "or reduce maximum relief/extra depth"
        )

    normalized = np.clip(cavity_mm / max(max_cavity_mm, 1e-9), 0.0, 1.0)
    # Existing cartridge convention requires the upper/female artwork mirrored in X.
    normalized = np.fliplr(normalized)
    female_u8 = np.round(normalized * 255.0).astype(np.uint8)

    path = Path(output_dir) / f"{name}_female_surface.png"
    if not cv2.imwrite(str(path), female_u8):
        raise RuntimeError(f"Could not write female relief surface map: {path}")
    return path, max_cavity_mm, normalized


def _map_to_printable_depth_tiers(relief: np.ndarray, relief_spec: ReliefSpec) -> np.ndarray:
    """Map non-zero authored tones into an FDM-meaningful physical depth range.

    Zero stays exactly zero. With the default 1.20 mm max / 0.40 mm minimum / four
    stepped levels, active geometry becomes 0.40, 0.80 or 1.20 mm. This avoids the
    previous 0.12-ish mm tiers that could disappear into a single sliced layer.
    """
    out = relief.copy().astype(np.float32)
    active = out > 0
    if not np.any(active):
        return out

    floor = relief_spec.min_relief_mm / relief_spec.max_relief_mm
    values = np.clip(out[active], 0.0, 1.0)

    if relief_spec.style == ReliefStyle.STEPPED:
        active_levels = max(1, relief_spec.levels - 1)
        if active_levels == 1:
            mapped = np.ones_like(values)
        else:
            # levels includes the zero/background level; every active pixel gets
            # one of the remaining printable tiers and cannot quantize back to 0.
            indices = np.rint(values * (active_levels - 1)).astype(np.int32)
            indices = np.clip(indices, 0, active_levels - 1)
            mapped = floor + (indices / float(active_levels - 1)) * (1.0 - floor)
    else:
        mapped = floor + values * (1.0 - floor)

    out[active] = np.clip(mapped, 0.0, 1.0)
    return out


def _sampling_target(
    spec: DieSpec,
    relief_spec: ReliefSpec,
    profile: PrinterProfile | None,
) -> tuple[int, float]:
    if profile is None:
        target = 512
        return target, spec.artwork_box_mm / target

    samples_per_feature = {"draft": 2.0, "balanced": 4.0, "fine": 6.0}[relief_spec.sampling_quality]
    useful_feature = min(profile.min_feature_mm, max(profile.nozzle_mm, 1e-6))
    mm_per_sample = useful_feature / samples_per_feature
    target = int(math.ceil(spec.artwork_box_mm / max(mm_per_sample, 1e-6)))
    target = max(96, min(1024, target))
    return target, spec.artwork_box_mm / target


def _filter_subresolution_positive_features(
    relief: np.ndarray,
    mm_per_sample: float,
    profile: PrinterProfile,
) -> tuple[np.ndarray, int]:
    """Remove positive regions too narrow to be a stable shared male master.

    The female is derived *after* this filter, preventing asymmetric feature loss.
    This intentionally favors compatibility over retaining every sub-nozzle detail.
    """
    active = (relief > 0).astype(np.uint8) * 255
    diameter_px = max(1, int(math.ceil(profile.min_feature_mm / max(mm_per_sample, 1e-9))))
    if diameter_px <= 1:
        return relief, 0
    if diameter_px % 2 == 0:
        diameter_px += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (diameter_px, diameter_px))
    opened = cv2.morphologyEx(active, cv2.MORPH_OPEN, kernel)
    removed = (active > 0) & (opened == 0)
    count = int(np.count_nonzero(removed))
    if count:
        relief = relief.copy()
        relief[removed] = 0.0
    return relief, count


def _apply_circular_artwork_mask(relief: np.ndarray, spec: DieSpec) -> None:
    height, width = relief.shape
    yy, xx = np.ogrid[:height, :width]
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    artwork_fraction = spec.artwork_radius_mm / max(spec.artwork_box_mm / 2.0, 1e-9)
    radius_px = min(width, height) * 0.5 * min(1.0, artwork_fraction)
    mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius_px**2
    relief[~mask] = 0.0
