from PIL import Image
import logging

from app.models import Analysis, RestoreResult
from app.config import settings
from app.pipeline.identity import identity_similarity, get_face_embedding
from app.pipeline.models.replicate_models import (
    bringing_old_photos_back,
    codeformer,
    ddcolor,
    real_esrgan_upscale,
)

logger = logging.getLogger(__name__)

YOUNG_CHILD_AGE_THRESHOLD = 6


def _should_run_codeformer(repaired: Image.Image) -> tuple[bool, str]:
    """Decide whether CodeFormer is safe to run on the repaired image.
    Only run it when InsightFace can confirm a detectable, mature face —
    otherwise CodeFormer is likely to distort (babies, occluded faces, etc.)."""
    try:
        from app.pipeline.identity import get_face_app
        import numpy as np
        app = get_face_app()
        if app == "unavailable":
            return True, "InsightFace unavailable, running CodeFormer by default"
        arr = np.asarray(repaired)[:, :, ::-1]
        faces = app.get(arr)
        if not faces:
            return False, "no face detected by InsightFace after repair"
        min_age = min(f.age for f in faces)
        if min_age < YOUNG_CHILD_AGE_THRESHOLD:
            return False, f"young child detected (age ~{min_age:.0f})"
        return True, f"adult face confirmed (age ~{min_age:.0f})"
    except Exception:
        return True, "face check failed, running CodeFormer by default"


async def _safe_stage(name: str, coro_fn, current: Image.Image) -> Image.Image:
    """Run one restoration stage. If the external model errors, log it and
    pass the current image through unchanged so a single flaky model never
    aborts the whole restoration."""
    try:
        return await coro_fn()
    except Exception as e:
        logger.warning("Stage '%s' failed (%s) — passing image through unchanged", name, e)
        return current


async def run_faithful_chain(img: Image.Image, analysis: Analysis) -> Image.Image:
    logger.info("Step 1: Global damage repair (Bringing Old Photos Back to Life)")
    out = await _safe_stage("damage-repair",
                            lambda: bringing_old_photos_back(img, with_scratch=True), img)

    if analysis.has_faces:
        should_run, reason = _should_run_codeformer(out)
        if should_run:
            logger.info("Step 2: Face restoration (CodeFormer, fidelity=%.2f) — %s",
                        settings.codeformer_fidelity, reason)
            out = await _safe_stage("face-restore",
                                    lambda: codeformer(out, fidelity=settings.codeformer_fidelity), out)
        else:
            logger.info("Step 2: Skipping CodeFormer — %s", reason)

    if analysis.is_bw:
        logger.info("Step 3: Colorization (DDColor)")
        out = await _safe_stage("colorize", lambda: ddcolor(out), out)

    logger.info("Step 4: Restorative upscale (Real-ESRGAN 2x)")
    out = await _safe_stage("upscale", lambda: real_esrgan_upscale(out, scale=2), out)

    return out


async def restore_full(img: Image.Image, analysis: Analysis) -> tuple[Image.Image, RestoreResult]:
    restored = await run_faithful_chain(img, analysis)
    id_score = identity_similarity(img, restored)

    needs_review = (
        analysis.has_faces
        and id_score is not None
        and id_score < settings.review_threshold
    )

    result = RestoreResult(
        engine="faithful-chain",
        identity_score=id_score,
        needs_review=needs_review,
    )
    return restored, result
