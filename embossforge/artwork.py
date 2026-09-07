from __future__ import annotations

from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET


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

    Raster input is converted to filled vector contours. SVG input is copied
    into a canonical coordinate system when needed. In particular, non-zero or
    negative SVG viewBox origins are translated to a 0,0 viewBox because
    OpenSCAD's ``import(..., center=true)`` can otherwise offset the imported
    geometry and cause our circular clipping operation to keep only a sliver of
    the design.

    Black/dark artwork on a light background is the default. Set
    ``invert=True`` for light artwork on a dark background.
    """
    src = Path(source)
    dst = Path(destination_svg)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        raise FileNotFoundError(src)

    ext = src.suffix.lower()
    if ext == ".svg":
        return _normalize_svg(src, dst)
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


def _parse_viewbox(value: str) -> tuple[float, float, float, float] | None:
    parts = [p for p in re.split(r"[\s,]+", value.strip()) if p]
    if len(parts) != 4:
        return None
    try:
        min_x, min_y, width, height = (float(p) for p in parts)
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    return min_x, min_y, width, height


def _fmt_svg_number(value: float) -> str:
    if abs(value) < 1e-12:
        value = 0.0
    return f"{value:.8f}".rstrip("0").rstrip(".") or "0"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _normalize_svg(src: Path, dst: Path) -> Path:
    """Canonicalize an SVG viewBox origin without changing visible geometry."""
    text = src.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        # Preserve prior permissive behavior for unusual but OpenSCAD-readable
        # SVG files. OpenSCAD will provide the useful diagnostic later.
        shutil.copyfile(src, dst)
        return dst

    raw_viewbox = root.attrib.get("viewBox")
    parsed = _parse_viewbox(raw_viewbox) if raw_viewbox else None
    if parsed is None:
        shutil.copyfile(src, dst)
        return dst

    min_x, min_y, width, height = parsed
    if abs(min_x) < 1e-12 and abs(min_y) < 1e-12:
        shutil.copyfile(src, dst)
        return dst

    # Keep non-rendering/support nodes at root level and translate only visible
    # content. This preserves defs/styles while changing the coordinate origin.
    namespace = ""
    if root.tag.startswith("{"):
        namespace = root.tag.split("}", 1)[0] + "}"
    group = ET.Element(
        f"{namespace}g",
        {
            "transform": (
                f"translate({_fmt_svg_number(-min_x)} {_fmt_svg_number(-min_y)})"
            )
        },
    )

    support_names = {"defs", "style", "metadata", "title", "desc"}
    visible_children = []
    for child in list(root):
        if _local_name(child.tag) not in support_names:
            visible_children.append(child)

    if not visible_children:
        shutil.copyfile(src, dst)
        return dst

    for child in visible_children:
        root.remove(child)
        group.append(child)
    root.append(group)
    root.set(
        "viewBox",
        f"0 0 {_fmt_svg_number(width)} {_fmt_svg_number(height)}",
    )

    # Register the common namespace so ElementTree emits <svg> instead of ns0.
    if namespace == "{http://www.w3.org/2000/svg}":
        ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.ElementTree(root).write(dst, encoding="utf-8", xml_declaration=True)
    return dst


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
