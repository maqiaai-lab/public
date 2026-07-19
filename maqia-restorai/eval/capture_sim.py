"""Synthesize realistic phone-captures of physical photos, with ground-truth
corners, for battle-testing the digitization detector.

Each generated capture composites a real photo onto a background via a known
perspective transform. The destination quad IS the ground truth, so detection
accuracy can be measured objectively (corner error + IoU).
"""
import numpy as np
import cv2
from PIL import Image
from dataclasses import dataclass, field


@dataclass
class Capture:
    image: np.ndarray                      # RGB uint8 capture
    gt_corners: np.ndarray                 # ground-truth TL,TR,BR,BL in capture coords
    photo_name: str
    background: str
    perspective: str
    lighting: str
    coverage: float                        # photo area / frame area


# ---------- backgrounds ----------

def bg_wood(h, w, rng):
    base = np.zeros((h, w, 3), np.float32)
    base[..., 0], base[..., 1], base[..., 2] = 165, 140, 100
    for _ in range(40):
        y = int(rng.integers(0, h))
        cv2.line(base, (0, y), (w, y + int(rng.integers(-20, 20))),
                 (float(rng.integers(120, 180)), float(rng.integers(100, 150)), float(rng.integers(70, 110))),
                 thickness=int(rng.integers(1, 4)))
    base += rng.normal(0, 6, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


def bg_dark(h, w, rng):
    base = np.full((h, w, 3), 55, np.float32)
    base += rng.normal(0, 10, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


def bg_cloth(h, w, rng):
    yy, xx = np.mgrid[0:h, 0:w]
    pattern = (np.sin(xx / 14.0) + np.cos(yy / 14.0)) * 18
    base = np.stack([110 + pattern, 115 + pattern, 130 + pattern], axis=-1)
    base += rng.normal(0, 5, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


def bg_white_desk(h, w, rng):
    base = np.full((h, w, 3), 225, np.float32)
    base += rng.normal(0, 7, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


def bg_busy(h, w, rng):
    base = np.full((h, w, 3), 130, np.float32)
    for _ in range(12):
        x1, y1 = int(rng.integers(0, w)), int(rng.integers(0, h))
        x2, y2 = x1 + int(rng.integers(40, 260)), y1 + int(rng.integers(40, 260))
        color = tuple(float(c) for c in rng.integers(40, 220, 3))
        cv2.rectangle(base, (x1, y1), (x2, y2), color, -1)
    base = cv2.GaussianBlur(base, (21, 21), 0)
    base += rng.normal(0, 8, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


def bg_hand(h, w, rng):
    # skin-tone surface (photo held in hand) — low contrast for lighter prints
    base = np.zeros((h, w, 3), np.float32)
    base[..., 0], base[..., 1], base[..., 2] = 205, 165, 135
    base += rng.normal(0, 9, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


BACKGROUNDS = {
    "wood": bg_wood, "dark": bg_dark, "cloth": bg_cloth,
    "white_desk": bg_white_desk, "busy": bg_busy, "hand": bg_hand,
}


# ---------- perspective presets ----------
# Each returns a destination quad (TL,TR,BR,BL) inside an (H,W) frame.

def persp_presets(h, w):
    m = 0.08  # base margin fraction
    return {
        "flat": np.float32([[w*0.12, h*0.10], [w*0.88, h*0.11],
                            [w*0.87, h*0.90], [w*0.13, h*0.89]]),
        "moderate": np.float32([[w*0.20, h*0.14], [w*0.82, h*0.09],
                               [w*0.86, h*0.88], [w*0.15, h*0.83]]),
        "heavy": np.float32([[w*0.26, h*0.18], [w*0.80, h*0.07],
                            [w*0.92, h*0.86], [w*0.12, h*0.80]]),
        "rotated": np.float32([[w*0.28, h*0.10], [w*0.90, h*0.24],
                              [w*0.72, h*0.90], [w*0.10, h*0.74]]),
        "offcenter": np.float32([[w*0.05, h*0.30], [w*0.55, h*0.22],
                                [w*0.60, h*0.78], [w*0.08, h*0.84]]),
    }


# ---------- lighting ----------

def light_even(img, rng):
    return img

def light_warm(img, rng):
    out = img.astype(np.float32); out[..., 0] *= 1.15; out[..., 2] *= 0.85
    return np.clip(out, 0, 255).astype(np.uint8)

def light_cool(img, rng):
    out = img.astype(np.float32); out[..., 2] *= 1.15; out[..., 0] *= 0.88
    return np.clip(out, 0, 255).astype(np.uint8)

def light_uneven(img, rng):
    h, w = img.shape[:2]
    grad = np.linspace(0.55, 1.15, w)[None, :, None]
    return np.clip(img.astype(np.float32) * grad, 0, 255).astype(np.uint8)

def light_glare(img, rng):
    h, w = img.shape[:2]
    out = img.astype(np.float32)
    cx, cy = rng.integers(int(w*0.3), int(w*0.7)), rng.integers(int(h*0.3), int(h*0.7))
    yy, xx = np.mgrid[0:h, 0:w]
    blob = np.exp(-((xx-cx)**2 + (yy-cy)**2) / (2*(min(h, w)*0.18)**2))
    out += (blob[..., None] * 140)
    return np.clip(out, 0, 255).astype(np.uint8)

LIGHTING = {
    "even": light_even, "warm": light_warm, "cool": light_cool,
    "uneven": light_uneven, "glare": light_glare,
}


def _order(pts):
    pts = np.asarray(pts, np.float32)
    rect = np.zeros((4, 2), np.float32)
    s = pts.sum(1); d = np.diff(pts, axis=1).flatten()
    rect[0] = pts[np.argmin(s)]; rect[2] = pts[np.argmax(s)]
    rect[1] = pts[np.argmin(d)]; rect[3] = pts[np.argmax(d)]
    return rect


def make_capture(photo: np.ndarray, photo_name: str, bg_name: str,
                 persp_name: str, light_name: str, frame=(1400, 1050),
                 seed=0) -> Capture:
    rng = np.random.default_rng(seed)
    H, W = frame
    ph, pw = photo.shape[:2]

    bg = BACKGROUNDS[bg_name](H, W, rng)
    dst = persp_presets(H, W)[persp_name]

    src = np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]])
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(photo, M, (W, H), borderValue=(0, 0, 0))
    mask = cv2.warpPerspective(np.full((ph, pw), 255, np.uint8), M, (W, H))

    comp = bg.copy()
    comp[mask > 0] = warped[mask > 0]
    comp = LIGHTING[light_name](comp, rng)

    coverage = float((mask > 0).sum()) / (H * W)
    return Capture(
        image=comp, gt_corners=_order(dst), photo_name=photo_name,
        background=bg_name, perspective=persp_name, lighting=light_name,
        coverage=coverage,
    )
