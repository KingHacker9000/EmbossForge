from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
from typing import Any

import cv2
import numpy as np

from .config import DieSpec, PrinterProfile
from .relief import ReliefPolarity, ReliefSpec


@dataclass(frozen=True)
class ShadedReferenceResult:
    """Inspectable artifacts produced when a shaded render is interpreted as relief.

    This is deliberately *not* photogrammetry or inverse rendering. The converter
    synthesizes a stable emboss-oriented height field from motif boundaries and
    local structure while suppressing broad illumination gradients.
    """

    height_map: Path
    relief_preview: Path
    foreground_mask: Path
    foreground_fraction: float
    structural_edge_fraction: float
    background_method: str
    target_px: int
    mm_per_sample: float

    def to_manifest_dict(self) -> dict[str, Any]:
        return {
            "method": "deterministic-shaded-reference-v1",
            "claim": "interpreted emboss relief; not reconstructed true 3D depth",
            "height_map": str(self.height_map),
            "relief_preview": str(self.relief_preview),
            "foreground_mask": str(self.foreground_mask),
            "foreground_fraction": round(self.foreground_fraction, 6),
            "structural_edge_fraction": round(self.structural_edge_fraction, 6),
            "background_method": self.background_method,
            "target_px": self.target_px,
            "mm_per_sample": self.mm_per_sample,
        }


def convert_shaded_reference(
    source: str | Path,
    output_dir: str | Path,
    name: str,
    spec: DieSpec,
    relief_spec: ReliefSpec,
    profile: PrinterProfile | None,
) -> ShadedReferenceResult:
    """Derive a manufacturable height map from a shaded/3D-looking raster image.

    Broad lighting gradients are intentionally removed. Geometry comes primarily
    from foreground regions, distance from motif boundaries, and stable local
    edges. The output is an explicit intermediate height map that the normal
    relief backend consumes and preserves in the generation manifest.
    """
    relief_spec.validate()
    src = Path(source)
    if src.suffix.lower() == ".svg":
        raise ValueError(
            "Shaded-reference conversion currently requires a raster image (PNG/JPG/TIFF/WEBP/BMP). "
            "Use binary mode for ordinary SVG artwork or export a rendered reference as PNG."
        )

    raw = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
    if raw is None:
        raise ValueError(f"Could not read shaded reference: {src}")

    if raw.ndim == 2:
        bgr = cv2.cvtColor(raw, cv2.COLOR_GRAY2BGR)
        alpha = None
    elif raw.shape[2] == 4:
        bgr = raw[:, :, :3]
        alpha = raw[:, :, 3].astype(np.float32) / 255.0
    else:
        bgr = raw[:, :, :3]
        alpha = None

    target_px, mm_per_sample = _target_sampling(spec, relief_spec, profile)
    canvas, alpha_canvas = _fit_to_square(bgr, alpha, target_px)
    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)

    mask, background_method = _foreground_mask(canvas, gray, alpha_canvas)
    # A bright specular stripe can locally match a white background even though
    # it lies inside a coherent medallion/petal/wing. For opaque shaded renders,
    # fill enclosed segmentation holes before physical-resolution cleanup. Alpha
    # inputs are left literal because transparent holes are usually intentional.
    if background_method != "alpha":
        mask = _fill_enclosed_holes(mask)
    mask = _printer_aware_mask_cleanup(mask, mm_per_sample, profile)
    foreground_fraction = float(np.mean(mask > 0))
    if foreground_fraction < 0.002:
        raise ValueError(
            "Could not isolate a usable foreground motif from the shaded reference. "
            "Use an image with a plain/transparent background or provide a true height map."
        )

    relief, structural = _synthesize_relief(gray, mask, mm_per_sample, profile)
    relief = _limit_to_artwork_circle(relief, spec)

    # Leave stepped/continuous quantization, gamma, dead-zone, and final printer
    # filtering to build_height_map so every relief source shares one backend.
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    height_path = out / f"{name}_derived_heightmap.png"
    preview_path = out / f"{name}_derived_relief_preview.png"
    mask_path = out / f"{name}_derived_foreground_mask.png"

    if relief_spec.polarity == ReliefPolarity.DARK_HIGH:
        encoded = np.round((1.0 - relief) * 255.0).astype(np.uint8)
    else:
        encoded = np.round(relief * 255.0).astype(np.uint8)
    preview = np.round(relief * 255.0).astype(np.uint8)

    if not cv2.imwrite(str(height_path), encoded):
        raise RuntimeError(f"Could not write derived shaded-reference height map: {height_path}")
    if not cv2.imwrite(str(preview_path), preview):
        raise RuntimeError(f"Could not write shaded-reference relief preview: {preview_path}")
    if not cv2.imwrite(str(mask_path), mask):
        raise RuntimeError(f"Could not write shaded-reference foreground mask: {mask_path}")

    edge_fraction = float(np.mean((structural > 0.45) & (mask > 0)))
    return ShadedReferenceResult(
        height_map=height_path,
        relief_preview=preview_path,
        foreground_mask=mask_path,
        foreground_fraction=foreground_fraction,
        structural_edge_fraction=edge_fraction,
        background_method=background_method,
        target_px=target_px,
        mm_per_sample=mm_per_sample,
    )


def looks_continuously_shaded(source: str | Path) -> bool:
    """Return an advisory-only hint for desktop UX; never changes semantics."""
    src = Path(source)
    if src.suffix.lower() == ".svg":
        return False
    gray = cv2.imread(str(src), cv2.IMREAD_GRAYSCALE)
    if gray is None or gray.size < 64:
        return False
    sample = cv2.resize(gray, (128, 128), interpolation=cv2.INTER_AREA)
    hist = cv2.calcHist([sample], [0], None, [32], [0, 256]).ravel()
    occupied = int(np.count_nonzero(hist > sample.size * 0.001))
    midtone_fraction = float(np.mean((sample > 24) & (sample < 232)))
    return occupied >= 14 and midtone_fraction >= 0.20


def _target_sampling(
    spec: DieSpec,
    relief_spec: ReliefSpec,
    profile: PrinterProfile | None,
) -> tuple[int, float]:
    if profile is None:
        target = 512
    else:
        samples_per_feature = {"draft": 2.0, "balanced": 4.0, "fine": 6.0}[relief_spec.sampling_quality]
        useful_feature = min(profile.min_feature_mm, max(profile.nozzle_mm, 1e-6))
        mm_per_sample = useful_feature / samples_per_feature
        target = int(math.ceil(spec.artwork_box_mm / max(mm_per_sample, 1e-6)))
        target = max(160, min(768, target))
    return target, spec.artwork_box_mm / target


def _fit_to_square(
    bgr: np.ndarray,
    alpha: np.ndarray | None,
    target_px: int,
) -> tuple[np.ndarray, np.ndarray | None]:
    h, w = bgr.shape[:2]
    scale = min(target_px / max(1, w), target_px / max(1, h))
    new_w = max(1, min(target_px, int(round(w * scale))))
    new_h = max(1, min(target_px, int(round(h * scale))))
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    resized = cv2.resize(bgr, (new_w, new_h), interpolation=interpolation)

    border = _border_pixels(bgr)
    background = np.median(border, axis=0).astype(np.uint8) if border.size else np.array([255, 255, 255], dtype=np.uint8)
    canvas = np.empty((target_px, target_px, 3), dtype=np.uint8)
    canvas[:] = background
    x0 = (target_px - new_w) // 2
    y0 = (target_px - new_h) // 2
    canvas[y0 : y0 + new_h, x0 : x0 + new_w] = resized

    if alpha is None:
        return canvas, None
    alpha_resized = cv2.resize(alpha, (new_w, new_h), interpolation=cv2.INTER_AREA)
    alpha_canvas = np.zeros((target_px, target_px), dtype=np.float32)
    alpha_canvas[y0 : y0 + new_h, x0 : x0 + new_w] = alpha_resized
    return canvas, alpha_canvas


def _border_pixels(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    band = max(1, int(round(min(h, w) * 0.04)))
    return np.concatenate(
        [
            image[:band, :, :].reshape(-1, 3),
            image[-band:, :, :].reshape(-1, 3),
            image[:, :band, :].reshape(-1, 3),
            image[:, -band:, :].reshape(-1, 3),
        ],
        axis=0,
    )


def _foreground_mask(
    bgr: np.ndarray,
    gray: np.ndarray,
    alpha: np.ndarray | None,
) -> tuple[np.ndarray, str]:
    if alpha is not None and float(np.ptp(alpha)) > 0.05:
        mask = (alpha >= 0.08).astype(np.uint8) * 255
        return mask, "alpha"

    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    border = _border_pixels(lab)
    bg = np.median(border, axis=0) if border.size else np.array([255.0, 128.0, 128.0], dtype=np.float32)
    color_dist = np.linalg.norm(lab - bg[None, None, :], axis=2)
    scale = float(np.percentile(color_dist, 99.0))
    if scale <= 1e-6:
        distance_u8 = np.zeros_like(gray)
    else:
        distance_u8 = np.clip(color_dist / scale * 255.0, 0, 255).astype(np.uint8)
    otsu, mask = cv2.threshold(distance_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    fraction = float(np.mean(mask > 0))
    if 0.01 <= fraction <= 0.92 and otsu >= 3:
        return mask, "border-color-distance"

    # Fallback for monochrome artwork or images whose motif reaches the frame.
    border_gray = np.concatenate([gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]])
    bg_gray = float(np.median(border_gray))
    if bg_gray >= 127:
        _, fallback = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        _, fallback = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return fallback, "border-luminance-otsu"


def _fill_enclosed_holes(mask: np.ndarray) -> np.ndarray:
    """Fill only background regions that cannot reach the image border."""
    foreground = (mask > 0).astype(np.uint8)
    inverse = (1 - foreground).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(inverse, connectivity=8)
    if count <= 1:
        return mask

    height, width = mask.shape
    exterior_labels: set[int] = set()
    exterior_labels.update(int(v) for v in labels[0, :])
    exterior_labels.update(int(v) for v in labels[-1, :])
    exterior_labels.update(int(v) for v in labels[:, 0])
    exterior_labels.update(int(v) for v in labels[:, -1])

    filled = foreground.copy()
    max_hole_area = int(height * width * 0.45)
    for label in range(1, count):
        if label in exterior_labels:
            continue
        if int(stats[label, cv2.CC_STAT_AREA]) <= max_hole_area:
            filled[labels == label] = 1
    return filled.astype(np.uint8) * 255


def _printer_aware_mask_cleanup(
    mask: np.ndarray,
    mm_per_sample: float,
    profile: PrinterProfile | None,
) -> np.ndarray:
    cleaned = mask.copy()
    if profile is None:
        open_diameter = 3
        close_diameter = 3
        min_area_px = 8
    else:
        open_diameter = _odd_kernel(profile.min_feature_mm / max(mm_per_sample, 1e-9))
        close_diameter = _odd_kernel(profile.effective_min_negative_feature_mm / max(mm_per_sample, 1e-9))
        min_area_px = max(4, int(round((profile.min_feature_mm / max(mm_per_sample, 1e-9)) ** 2 * 0.35)))

    if close_diameter > 1:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close_diameter, close_diameter))
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel)
    if open_diameter > 1:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (open_diameter, open_diameter))
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    count, labels, stats, _ = cv2.connectedComponentsWithStats((cleaned > 0).astype(np.uint8), connectivity=8)
    filtered = np.zeros_like(cleaned)
    for idx in range(1, count):
        if int(stats[idx, cv2.CC_STAT_AREA]) >= min_area_px:
            filtered[labels == idx] = 255
    return filtered


def _synthesize_relief(
    gray: np.ndarray,
    mask: np.ndarray,
    mm_per_sample: float,
    profile: PrinterProfile | None,
) -> tuple[np.ndarray, np.ndarray]:
    mask01 = (mask > 0).astype(np.float32)
    distance = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    nonzero = distance[distance > 0]
    denom = float(np.percentile(nonzero, 92.0)) if nonzero.size else 1.0
    distance_n = np.clip(distance / max(denom, 1e-6), 0.0, 1.0)

    gray_f = gray.astype(np.float32) / 255.0
    sigma_broad = max(3.0, gray.shape[0] * 0.045)
    broad = cv2.GaussianBlur(gray_f, (0, 0), sigmaX=sigma_broad, sigmaY=sigma_broad)
    local = gray_f - broad
    local_scale = float(np.percentile(np.abs(local[mask > 0]), 95.0)) if np.any(mask > 0) else 0.0
    local_structure = np.clip(np.abs(local) / max(local_scale, 1e-4), 0.0, 1.0)

    gx = cv2.Sobel(gray_f, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray_f, cv2.CV_32F, 0, 1, ksize=3)
    grad = cv2.magnitude(gx, gy)
    grad_scale = float(np.percentile(grad[mask > 0], 95.0)) if np.any(mask > 0) else 0.0
    grad_n = np.clip(grad / max(grad_scale, 1e-4), 0.0, 1.0)

    structural = np.maximum(local_structure * 0.70, grad_n)
    structural = cv2.GaussianBlur(structural, (0, 0), sigmaX=0.8, sigmaY=0.8)

    # Major motif regions become broad rounded plateaus. Strong local edges become
    # shallow grooves instead of being mistaken for literal light/shadow height.
    base = 0.28 + 0.68 * np.sqrt(distance_n)
    relief = base - 0.30 * structural
    relief = np.clip(relief, 0.08, 1.0) * mask01

    if profile is not None:
        sigma_px = (profile.effective_line_width_mm * 0.18) / max(mm_per_sample, 1e-9)
        if sigma_px >= 0.35:
            relief = cv2.GaussianBlur(relief, (0, 0), sigmaX=sigma_px, sigmaY=sigma_px)
            relief *= mask01

    maximum = float(np.max(relief))
    if maximum > 1e-6:
        relief /= maximum
    return relief.astype(np.float32), structural.astype(np.float32)


def _limit_to_artwork_circle(relief: np.ndarray, spec: DieSpec) -> np.ndarray:
    height, width = relief.shape
    yy, xx = np.ogrid[:height, :width]
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0
    radius_px = min(width, height) * 0.5
    circle = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius_px**2
    result = relief.copy()
    result[~circle] = 0.0
    return result


def _odd_kernel(value: float) -> int:
    diameter = max(1, int(math.ceil(value)))
    if diameter % 2 == 0:
        diameter += 1
    # Large morphology kernels are expensive and can erase valid motifs. The
    # final shared height-map filter still enforces the printer profile.
    return min(diameter, 31)
