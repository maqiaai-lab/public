"""Trim residual border pixels after perspective correction."""
import numpy as np


def tight_crop(arr: np.ndarray, margin: int = 3) -> np.ndarray:
    """Trim a small margin from all edges to remove interpolation artifacts
    left by the perspective warp. No-op if the image would become too small."""
    h, w = arr.shape[:2]
    if margin <= 0 or h - 2 * margin < 100 or w - 2 * margin < 100:
        return arr
    return arr[margin : h - margin, margin : w - margin]
