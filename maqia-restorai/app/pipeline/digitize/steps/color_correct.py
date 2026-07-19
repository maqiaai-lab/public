"""White balance and exposure normalization for phone captures.

Conservative by design: a phone photo of a print is usually tinted by
ambient light, but we don't want to strip an intentionally warm vintage
tone before the restoration models see it. Corrections are blended, not
applied at full strength.
"""
import numpy as np
import cv2


# 0.0 = no correction, 1.0 = full gray-world neutralization.
WB_STRENGTH = 0.5


def gray_world_white_balance(arr: np.ndarray, strength: float = WB_STRENGTH) -> np.ndarray:
    """Neutralize a color cast using the gray-world assumption, blended by
    `strength` so vintage tones survive."""
    result = arr.astype(np.float32)
    means = result.reshape(-1, 3).mean(axis=0)
    gray = means.mean()
    for c in range(3):
        if means[c] > 1e-3:
            scale = gray / means[c]
            scale = 1.0 + (scale - 1.0) * strength  # blend toward neutral
            result[..., c] *= scale
    return np.clip(result, 0, 255).astype(np.uint8)


def normalize_exposure(arr: np.ndarray) -> np.ndarray:
    """Even out lighting with CLAHE on the L channel of LAB."""
    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2RGB)


def color_correct(arr: np.ndarray) -> np.ndarray:
    arr = gray_world_white_balance(arr)
    arr = normalize_exposure(arr)
    return arr
