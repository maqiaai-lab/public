"""Detect the physical photo's quadrilateral inside a phone capture.

A phone snapshot of a print is hard because the print's *outer border* is
often low-contrast (dark photo on a dark table) or lost in clutter (patterned
cloth, busy desk). What is reliable is that the print is a dense, textured,
self-contained region sitting on a comparatively different surface.

So rather than hunting for a clean rectangular border, we build a "print-ish"
mask from several independent cues, merge each region's interior into a solid
blob, fit a quad to each candidate blob, and score the candidates. When cues
disagree the scorer picks the most photo-like quad.
"""
import numpy as np
import cv2
from typing import Optional

# Detection runs on a downscaled copy for speed; corners are scaled back up.
DETECT_MAX_EDGE = 1024
MIN_AREA_FRAC = 0.10
MAX_AREA_FRAC = 0.95
# Below this edge-support the border is low-contrast and the quad likely
# undersegments — trigger the (slower) GrabCut colour refinement.
REFINE_EDGE_SUPPORT = 0.80


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Order 4 corners TL, TR, BR, BL.

    Uses angle-sort around the centroid, which is a true bijection — every
    input corner maps to a distinct output slot. (The common sum/diff trick
    is NOT bijective for rotated quads: two corners can win the same slot,
    collapsing the quad to a triangle.)"""
    pts = np.asarray(pts, dtype=np.float32)
    c = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    pts = pts[np.argsort(ang)]                     # clockwise in image coords
    start = int(np.argmin(pts.sum(axis=1)))        # rotate so top-left is first
    pts = np.roll(pts, -start, axis=0)
    # Ensure the winding is TL, TR, BR, BL (top edge goes left→right).
    if pts[1][0] < pts[3][0]:
        pts = pts[[0, 3, 2, 1]]
    return pts.astype(np.float32)


def _adaptive_canny(gray: np.ndarray) -> np.ndarray:
    v = float(np.median(gray))
    lo = int(max(0, 0.66 * v))
    hi = int(min(255, 1.33 * v))
    return cv2.Canny(gray, lo, hi)


def _print_masks(small: np.ndarray) -> list[np.ndarray]:
    """Return several binary candidate masks of the print region, each from a
    different cue. Each mask has the print interior filled to a solid blob."""
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    gray_b = cv2.bilateralFilter(gray, 9, 60, 60)
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    sat = hsv[..., 1]

    masks = []
    close_k = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    small_k = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))

    # Cue 1: multi-channel edges, interior merged into a solid blob.
    edges = cv2.bitwise_or(_adaptive_canny(gray_b), _adaptive_canny(sat))
    edges = cv2.dilate(edges, small_k, iterations=1)
    blob = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, close_k, iterations=3)
    blob = _fill(blob)
    masks.append(blob)

    # Cue 2: local texture (std-dev) — print is textured, smooth surfaces aren't.
    g = gray.astype(np.float32)
    mean = cv2.blur(g, (15, 15))
    sq = cv2.blur(g * g, (15, 15))
    texture = np.sqrt(np.maximum(sq - mean * mean, 0))
    tnorm = cv2.normalize(texture, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, tmask = cv2.threshold(tnorm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    tmask = cv2.morphologyEx(tmask, cv2.MORPH_CLOSE, close_k, iterations=2)
    tmask = _fill(tmask)
    masks.append(tmask)

    # Cue 3: brightness/color distance from the dominant surface color.
    # The border strip is assumed to be background; measure each pixel's
    # distance from the median border color.
    border = np.concatenate([
        small[:5].reshape(-1, 3), small[-5:].reshape(-1, 3),
        small[:, :5].reshape(-1, 3), small[:, -5:].reshape(-1, 3),
    ])
    bg_col = np.median(border, axis=0)
    dist = np.linalg.norm(small.astype(np.float32) - bg_col, axis=2)
    dnorm = cv2.normalize(dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    _, dmask = cv2.threshold(dnorm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    dmask = cv2.morphologyEx(dmask, cv2.MORPH_OPEN, small_k, iterations=1)
    dmask = cv2.morphologyEx(dmask, cv2.MORPH_CLOSE, close_k, iterations=2)
    dmask = _fill(dmask)
    masks.append(dmask)

    return masks, edges


def _fill(mask: np.ndarray) -> np.ndarray:
    """Fill interior holes of the largest blobs so a textured region becomes solid."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(mask)
    cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)
    return filled


def _valid_quad(q: np.ndarray) -> bool:
    """Reject degenerate quads (collapsed/coincident corners, non-convex).
    A real print has four well-separated corners."""
    d = [np.linalg.norm(q[i] - q[(i + 1) % 4]) for i in range(4)]
    if min(d) < 0.15 * max(d):
        return False
    return bool(cv2.isContourConvex(q.astype(np.int32)))


def _quad_from_contour(cnt: np.ndarray) -> Optional[np.ndarray]:
    """Reduce a contour to four corners. Prefer a genuine perspective quad
    (approxPolyDP) when it is non-degenerate — that captures keystone skew —
    but fall back to the minimum-area rotated rectangle, which always yields
    four proper corners even when the blob's border is ragged or a low-contrast
    edge was clipped (the failure mode that otherwise collapses to a triangle)."""
    hull = cv2.convexHull(cnt)
    peri = cv2.arcLength(hull, True)
    for eps in (0.02, 0.03, 0.05, 0.08):
        approx = cv2.approxPolyDP(hull, eps * peri, True)
        if len(approx) == 4:
            quad = approx.reshape(4, 2).astype(np.float32)
            if _valid_quad(quad):
                return quad
    return cv2.boxPoints(cv2.minAreaRect(cnt)).astype(np.float32)


def _edge_support(quad: np.ndarray, edges: np.ndarray) -> float:
    """Fraction of the quad's perimeter that lies on a real edge."""
    perim = np.zeros(edges.shape, np.uint8)
    cv2.polylines(perim, [quad.astype(np.int32)], True, 255, thickness=3)
    edge_d = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    total = int((perim > 0).sum())
    if total == 0:
        return 0.0
    hit = int(np.logical_and(perim > 0, edge_d > 0).sum())
    return hit / total


def _score(quad: np.ndarray, contour_area: float, edges: np.ndarray, area: float) -> float:
    quad_area = cv2.contourArea(quad.astype(np.float32))
    if quad_area <= 0:
        return 0.0
    cov = quad_area / area
    if cov < MIN_AREA_FRAC or cov > MAX_AREA_FRAC:
        return 0.0
    rectangularity = min(contour_area / quad_area, 1.0)
    support = _edge_support(quad, edges)
    # Weighted: a real print is rectangular AND its border sits on real edges.
    return 0.55 * rectangularity + 0.45 * support


def detect_photo_quad(arr: np.ndarray) -> tuple[Optional[np.ndarray], float]:
    """
    Find the largest print-like quadrilateral in the capture.

    Returns (corners, confidence). Corners are full-resolution, ordered
    TL, TR, BR, BL. Confidence in [0,1] blends rectangularity and edge support.
    Returns (None, 0.0) when nothing plausible is found.
    """
    h, w = arr.shape[:2]
    scale = max(h, w) / DETECT_MAX_EDGE if max(h, w) > DETECT_MAX_EDGE else 1.0
    small = (cv2.resize(arr, (int(w / scale), int(h / scale)), interpolation=cv2.INTER_AREA)
             if scale > 1.0 else arr)

    masks, edges = _print_masks(small)
    small_area = small.shape[0] * small.shape[1]

    best_quad, best_score = None, 0.0
    for mask in masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:3]:
            area = cv2.contourArea(cnt)
            if area < MIN_AREA_FRAC * small_area:
                continue
            quad = _quad_from_contour(cnt)
            if quad is None:
                continue
            s = _score(quad, area, edges, small_area)
            if s > best_score:
                best_score, best_quad = s, quad

    if best_quad is None:
        return None, 0.0

    # If the winning quad's border sits poorly on real edges, it is probably
    # undersegmenting a low-contrast print — refine with a colour model.
    if _edge_support(best_quad, edges) < REFINE_EDGE_SUPPORT:
        from app.pipeline.digitize.steps.refine import grabcut_refine
        refined = grabcut_refine(arr, best_quad * scale, _order_corners)
        return refined, float(best_score)

    best_quad = best_quad * scale
    return _order_corners(best_quad), float(best_score)
