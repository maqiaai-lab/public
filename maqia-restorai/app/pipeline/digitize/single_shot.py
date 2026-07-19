"""MVP digitization: one phone snapshot of a physical photo."""
import numpy as np
import logging
from PIL import Image

from app.pipeline.digitize.protocol import DigitizeResult
from app.pipeline.digitize.steps.edge_detect import detect_photo_quad
from app.pipeline.digitize.steps.perspective import perspective_transform
from app.pipeline.digitize.steps.crop import tight_crop
from app.pipeline.digitize.steps.color_correct import color_correct
from app.pipeline.digitize.steps.demoire import demoire

logger = logging.getLogger(__name__)


class SingleShotStrategy:
    name = "single_shot"

    def __init__(self, min_confidence: float = 0.65, crop_margin: int = 3, demoire_enabled: bool = False):
        self.min_confidence = min_confidence
        self.crop_margin = crop_margin
        self.demoire_enabled = demoire_enabled

    def execute(self, images: list[Image.Image]) -> DigitizeResult:
        img = images[0].convert("RGB")
        arr = np.asarray(img)

        corners, confidence = detect_photo_quad(arr)

        if corners is None or confidence < self.min_confidence:
            logger.info("Digitize: no confident photo quad found (conf=%.2f) — passing through", confidence)
            return DigitizeResult(image=img, was_digitized=False, confidence=confidence, strategy=self.name)

        logger.info("Digitize: photo detected (conf=%.2f), rectifying", confidence)
        rectified = perspective_transform(arr, corners)
        cropped = tight_crop(rectified, margin=self.crop_margin)
        corrected = color_correct(cropped)
        if self.demoire_enabled:
            corrected = demoire(corrected)

        return DigitizeResult(
            image=Image.fromarray(corrected),
            was_digitized=True,
            confidence=confidence,
            corners=[(int(x), int(y)) for x, y in corners],
            strategy=self.name,
        )
