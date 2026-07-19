"""Decide whether an upload is a phone capture of a physical photo
(needs digitizing) versus an already-digital scan/file (pass through)."""
import numpy as np
from PIL import Image

from app.pipeline.digitize.steps.edge_detect import detect_photo_quad


def looks_like_capture(img: Image.Image, min_confidence: float = 0.65) -> tuple[bool, float]:
    """
    Heuristic: if a confident quadrilateral covering 15-90% of the frame is
    found, the image is probably a photo-of-a-photo. A clean scan fills the
    frame edge-to-edge and yields no inner quad.

    Returns (is_capture, confidence).
    """
    arr = np.asarray(img.convert("RGB"))
    corners, confidence = detect_photo_quad(arr)
    if corners is None:
        return False, 0.0

    # Reject quads that basically fill the frame (already a full scan)
    h, w = arr.shape[:2]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    quad_w = max(xs) - min(xs)
    quad_h = max(ys) - min(ys)
    coverage = (quad_w * quad_h) / (w * h)

    is_capture = confidence >= min_confidence and coverage < 0.9
    return is_capture, confidence
