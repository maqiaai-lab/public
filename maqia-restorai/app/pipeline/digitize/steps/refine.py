"""Refine a rough print quad using a GrabCut colour model.

Used only when the initial detection has weak edge support (low-contrast
borders — dark print on a dark surface — where the print's darker regions get
clipped and the quad undersegments). GrabCut grows the confident core outward
along colour coherence to recover the true print extent. It is comparatively
slow (~0.5s), so callers gate it on a weak-detection trigger rather than
running it on every image.
"""
import numpy as np
import cv2

GC_MAX_EDGE = 600


def grabcut_refine(arr: np.ndarray, quad: np.ndarray, order_fn) -> np.ndarray:
    h, w = arr.shape[:2]
    scale = max(h, w) / GC_MAX_EDGE if max(h, w) > GC_MAX_EDGE else 1.0
    small = (cv2.resize(arr, (int(w / scale), int(h / scale)), interpolation=cv2.INTER_AREA)
             if scale > 1.0 else arr.copy())
    sq = quad / scale

    mask = np.full(small.shape[:2], cv2.GC_PR_BGD, np.uint8)
    cv2.fillPoly(mask, [sq.astype(np.int32)], cv2.GC_PR_FGD)
    # Shrunk quad = sure foreground seed for the colour model.
    core = sq.mean(0) + (sq - sq.mean(0)) * 0.6
    cv2.fillPoly(mask, [core.astype(np.int32)], cv2.GC_FGD)

    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(small, mask, None, bgd, fgd, 3, cv2.GC_INIT_WITH_MASK)
    except Exception:
        return quad

    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE,
                          cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)), iterations=2)
    contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return quad
    box = cv2.boxPoints(cv2.minAreaRect(max(contours, key=cv2.contourArea))) * scale
    return order_fn(box)
