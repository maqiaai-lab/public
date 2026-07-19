"""Reduce moire/screen-door patterns from captures of printed or screened photos.

MVP uses a bilateral filter (edge-preserving smoothing) rather than
frequency-domain notch filtering — simpler, and the downstream Real-ESRGAN
pass restores fine detail. Opt-in via config; off by default because it
softens detail.
"""
import numpy as np
import cv2


def demoire(arr: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(arr, d=9, sigmaColor=75, sigmaSpace=75)
