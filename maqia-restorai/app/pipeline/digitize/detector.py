"""Decide whether an upload is a phone capture of a physical photo
(needs digitizing) versus an already-digital scan/file (pass through).

Important: pixel-only detection cannot perfectly separate "a print lying on a
surface" from "a studio portrait whose own background is plain" — they can be
identical. So this gate is deliberately CONSERVATIVE (favor pass-through when
unsure) and is only used for the ambiguous file-upload path. The camera-capture
path in the UI sends digitize=force, because there the intent is unambiguous.
"""
import numpy as np
import cv2
from PIL import Image

from app.pipeline.digitize.steps.edge_detect import detect_photo_quad

# A real capture has a smooth surface border around the print; a full-frame
# digital photo's edges are image content. Frame-edge colour std separates them.
FRAME_BAND_MAX_STD = 20.0
MIN_COVERAGE = 0.15
MAX_COVERAGE = 0.85


def _frame_band_std(arr: np.ndarray) -> float:
    h, w = arr.shape[:2]
    b = max(int(min(h, w) * 0.03), 3)
    band = np.concatenate([
        arr[:b].reshape(-1, 3), arr[-b:].reshape(-1, 3),
        arr[:, :b].reshape(-1, 3), arr[:, -b:].reshape(-1, 3),
    ])
    return float(band.std(0).mean())


def looks_like_capture(img: Image.Image, min_confidence: float = 0.65) -> tuple[bool, float]:
    """
    Conservative test for the auto path. Returns (is_capture, confidence).

    Requires all of:
      - a confident print-like quad,
      - coverage in a plausible range (not the whole frame, not a speck),
      - a smooth surface border around the print (frame-edge band is uniform).
    """
    arr = np.asarray(img.convert("RGB"))
    corners, confidence = detect_photo_quad(arr)
    if corners is None or confidence < min_confidence:
        return False, confidence

    h, w = arr.shape[:2]
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    coverage = ((max(xs) - min(xs)) * (max(ys) - min(ys))) / (w * h)
    if coverage < MIN_COVERAGE or coverage > MAX_COVERAGE:
        return False, confidence

    if _frame_band_std(arr) > FRAME_BAND_MAX_STD:
        return False, confidence

    return True, confidence
