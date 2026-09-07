from __future__ import annotations

from pathlib import Path
import shutil


RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def normalize_artwork(
    source: str | Path,
    destination_svg: str | Path,
    *,
    threshold: int = 160,
    invert: bool = False,
    simplify_fraction: float = 0.0015,
    min_area_px: float = 8.0,
) -> Path:
    """Normalize SVG or raster artwork to a local SVG file.

    Raster input is converted to filled vector contours. Black/dark artwork on a
    light background is the default. Set ``invert=True`` for light artwork on a
    dark background.
    """
    src = Path(source)
    dst = Path(destination_svg)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(src)

    ext = src.suffix.lower()
    if ext == ".svg":
        shutil.copyfile(src, dst)
        return dst
    if ext not in RASTER_EXTENSIONS:
        raise ValueError(f"Unsupported artwork type: {ext or '<none>'}. Use SVG, PNG, JPG, BMP, TIFF, or WEBP.")

    return _raster_to_svg(
        src,
        dst,
        threshold=threshold,
        invert=invert,
        simplify_fraction=simplify_fraction,
        min_area_px=min_area_px,
    )


def _raster_to_svg(
    src: Path,
    dst: Path,
    *,
    threshold: int,
    invert: bool,
    simplify_fraction: float,
    min_area_px: float,
) -> Path:
    import cv2

    gray = cv2.imread(str(src), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError(f"Could not read raster artwork: {src}")

    threshold = max(0, min(255, int(threshold)))
    mode = cv2.THRESH_BINARY if invert else cv2.THRESH_BINARY_INV
    _, mask = cv2.threshold(gray, threshold, 255, mode)

    contours, _hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    kept: list[list[tuple[float, float]]] = []
    for contour in contours:
        if abs(cv2.contourArea(contour)) < min_area_px:
            continue
        perimeter = cv2.arcLength(contour, True)
        epsilon = max(0.25, perimeter * simplify_fraction)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        points = [(float(p[0][0]), float(p[0][1])) for p in approx]
        if len(points) >= 3:
            kept.append(points)

    if not kept:
        raise ValueError("No usable foreground shapes were found in the raster artwork")

    height, width = gray.shape
    # A single even-odd path preserves nested contours as holes regardless of winding.
    parts: list[str] = []
    for points in kept:
        x0, y0 = points[0]
        parts.append(f"M{x0:.3f},{y0:.3f}")
        parts.extend(f"L{x:.3f},{y:.3f}" for x, y in points[1:])
        parts.append("Z")
    path_data = " ".join(parts)

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        f'  <path d="{path_data}" fill="black" fill-rule="evenodd"/>\n'
        '</svg>\n'
    )
    dst.write_text(svg, encoding="utf-8")
    return dst
