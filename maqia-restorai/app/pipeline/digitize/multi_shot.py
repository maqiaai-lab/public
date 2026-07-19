"""Multi-shot digitization — FUTURE (Option 2).

Placeholder documenting the plug-in contract. When implemented, this strategy
will accept several frames of the same physical photo taken from slightly
different angles and merge them to remove glare/reflections and recover
detail (median/multi-frame super-resolution).

Planned pipeline:
  1. detect_photo_quad on each frame
  2. perspective_transform each to a common rectangle
  3. feature-align the rectified frames (ORB/ECC homography)
  4. merge — per-pixel median kills specular glare; weighted blend for SR
  5. color_correct + optional demoire

It satisfies the same DigitizeStrategy protocol, so wiring it in is a
config switch (digitize_strategy="multi_shot") plus a multi-file endpoint —
no changes to the rest of the pipeline.
"""
import logging
from PIL import Image

from app.pipeline.digitize.protocol import DigitizeResult
from app.pipeline.digitize.single_shot import SingleShotStrategy

logger = logging.getLogger(__name__)


class MultiShotStrategy:
    name = "multi_shot"

    def __init__(self, min_confidence: float = 0.65, crop_margin: int = 3, demoire_enabled: bool = False):
        # Until frame-merging lands, fall back to processing the sharpest frame
        # with the single-shot strategy so the interface already works.
        self._fallback = SingleShotStrategy(min_confidence, crop_margin, demoire_enabled)

    def execute(self, images: list[Image.Image]) -> DigitizeResult:
        if len(images) > 1:
            logger.info("MultiShot: frame-merge not yet implemented — using sharpest of %d frames", len(images))
            images = [_sharpest(images)]
        result = self._fallback.execute(images)
        result.strategy = self.name
        return result


def _sharpest(images: list[Image.Image]) -> Image.Image:
    """Pick the least-blurry frame by variance of Laplacian."""
    import numpy as np
    import cv2

    best, best_score = images[0], -1.0
    for im in images:
        gray = cv2.cvtColor(np.asarray(im.convert("RGB")), cv2.COLOR_RGB2GRAY)
        score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if score > best_score:
            best, best_score = im, score
    return best
