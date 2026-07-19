"""Detect the physical photo's quadrilateral inside a phone capture."""
import numpy as np
import cv2
from typing import Optional


# Detection runs on a downscaled copy for speed; corners are scaled back up.
DETECT_MAX_EDGE = 1024


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Return corners ordered TL, TR, BR, BL."""
    rect = np.zeros((4, 2), dtype=np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).flatten()
    rect[0] = pts[np.argmin(s)]      # top-left  = smallest x+y
    rect[2] = pts[np.argmax(s)]      # bottom-right = largest x+y
    rect[1] = pts[np.argmin(diff)]   # top-right = smallest y-x
    rect[3] = pts[np.argmax(diff)]   # bottom-left = largest y-x
    return rect


def _quad_from_contour(cnt: np.ndarray) -> Optional[np.ndarray]:
    """Reduce a contour to 4 corners. Try polygon approximation first
    (handles rotated rectangles cleanly), then fall back to the minimum-area
    rotated rectangle, which always yields 4 corners even when the border was
    detected as a jagged/fragmented contour."""
    hull = cv2.convexHull(cnt)
    peri = cv2.arcLength(hull, True)
    for eps in (0.02, 0.03, 0.05, 0.08):
        approx = cv2.approxPolyDP(hull, eps * peri, True)
        if len(approx) == 4:
            return approx.reshape(4, 2).astype(np.float32)
    # Fallback: min-area rectangle
    box = cv2.boxPoints(cv2.minAreaRect(cnt))
    return box.astype(np.float32)


def detect_photo_quad(arr: np.ndarray) -> tuple[Optional[np.ndarray], float]:
    """
    Find the largest rectangular region (the physical photo) in the capture.

    Returns (corners, confidence). Corners are in full-resolution coordinates,
    ordered TL, TR, BR, BL. Confidence is contour_area / quad_area
    (1.0 = the detected contour fills its fitted quad perfectly). Returns
    (None, 0.0) if no plausible quad found.
    """
    h, w = arr.shape[:2]
    scale = max(h, w) / DETECT_MAX_EDGE if max(h, w) > DETECT_MAX_EDGE else 1.0
    if scale > 1.0:
        small = cv2.resize(arr, (int(w / scale), int(h / scale)), interpolation=cv2.INTER_AREA)
    else:
        small = arr

    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    # Bilateral filter smooths interior texture while keeping the photo border sharp
    gray = cv2.bilateralFilter(gray, 9, 60, 60)
    edges = cv2.Canny(gray, 40, 130)
    # Close gaps so the photo border forms one connected contour
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, 0.0

    small_area = small.shape[0] * small.shape[1]
    best_quad = None
    best_conf = 0.0

    for cnt in sorted(contours, key=cv2.contourArea, reverse=True)[:5]:
        area = cv2.contourArea(cnt)
        if area < 0.12 * small_area:
            continue

        quad = _quad_from_contour(cnt)
        if quad is None:
            continue

        quad_area = cv2.contourArea(quad.astype(np.float32))
        if quad_area <= 0:
            continue
        # How rectangular is this region? contour area vs its fitted quad area.
        conf = min(area / quad_area, 1.0)

        if conf > best_conf:
            best_conf = conf
            best_quad = quad

    if best_quad is None:
        return None, 0.0

    best_quad = best_quad * scale
    return _order_corners(best_quad), float(best_conf)
