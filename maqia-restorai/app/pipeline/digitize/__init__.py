"""Public API for the digitization stage.

Runs BEFORE preprocess(). Turns a phone snapshot of a physical print into a
flat, cropped, color-corrected image. Auto-detects whether digitization is
needed so already-digital uploads pass straight through.

Extensibility: strategies satisfy the DigitizeStrategy protocol and are
chosen by config (`digitize_strategy`). Single-shot ships now; multi-shot
plugs in with no changes to callers.
"""
import io
import logging
from typing import Optional
from PIL import Image, ImageOps

from app.config import settings
from app.pipeline.digitize.protocol import DigitizeResult, DigitizeStrategy
from app.pipeline.digitize.single_shot import SingleShotStrategy
from app.pipeline.digitize.multi_shot import MultiShotStrategy
from app.pipeline.digitize.detector import looks_like_capture

logger = logging.getLogger(__name__)


def _get_strategy(name: Optional[str] = None) -> DigitizeStrategy:
    name = name or settings.digitize_strategy
    kwargs = dict(
        min_confidence=settings.digitize_min_confidence,
        crop_margin=settings.digitize_crop_margin,
        demoire_enabled=settings.digitize_demoire,
    )
    if name == "multi_shot":
        return MultiShotStrategy(**kwargs)
    return SingleShotStrategy(**kwargs)


def digitize_images(images: list[Image.Image], force: Optional[bool] = None,
                    strategy: Optional[str] = None) -> DigitizeResult:
    """
    Digitize one or more captures of the same physical photo.

    force: None = auto-detect, True = always digitize, False = skip entirely.
    strategy: override the configured strategy ("single_shot" | "multi_shot").
    """
    images = [ImageOps.exif_transpose(im).convert("RGB") for im in images]

    if force is False or not settings.digitize_enabled:
        return DigitizeResult(image=images[0], was_digitized=False, confidence=0.0)

    if force is None and settings.digitize_auto_detect and len(images) == 1:
        is_capture, conf = looks_like_capture(images[0], settings.digitize_min_confidence)
        if not is_capture:
            logger.info("Digitize: upload looks already-digital (conf=%.2f) — skipping", conf)
            return DigitizeResult(image=images[0], was_digitized=False, confidence=conf)

    return _get_strategy(strategy).execute(images)


def digitize(raw_bytes: bytes, force: Optional[bool] = None) -> bytes:
    """Convenience wrapper for the single-file path: bytes in, bytes out.
    Returns the original bytes unchanged if no digitization was applied."""
    img = Image.open(io.BytesIO(raw_bytes))
    result = digitize_images([img], force=force)
    if not result.was_digitized:
        return raw_bytes
    buf = io.BytesIO()
    result.image.save(buf, format="PNG")
    return buf.getvalue()
