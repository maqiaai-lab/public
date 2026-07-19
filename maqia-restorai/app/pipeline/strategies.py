from PIL import Image
import logging

from app.models import Analysis, RestoreResult
from app.config import settings
from app.pipeline.identity import identity_similarity, get_face_embedding
from app.pipeline.models.replicate_models import (
    bringing_old_photos_back,
    codeformer,
    ddcolor,
    deoldify,
    real_esrgan_upscale,
)


async def _colorize(img: Image.Image) -> Image.Image:
    """Colorize B&W using the configured model. DeOldify is the default — it
    produces natural, muted tones; DDColor is vivid but invents implausible
    hues (garish backgrounds) on low-information regions."""
    if settings.colorizer == "ddcolor":
        return await ddcolor(img)
    return await deoldify(img, settings.deoldify_model, settings.deoldify_render_factor)

logger = logging.getLogger(__name__)


def fidelity_for_age(age: float | None) -> float | None:
    """Map a detected face age to a CodeFormer fidelity, or None to skip.

    CodeFormer's `fidelity` runs 0..1 where HIGHER = stay closer to the real
    input (less generative restructuring). Younger faces sit further from
    CodeFormer's adult-biased training prior, so it distorts them — we counter
    that by dialing fidelity UP for children (gentler, identity-preserving) and
    skipping infants/toddlers entirely, rather than a single on/off switch."""
    if age is None:
        return settings.codeformer_fidelity
    if age < settings.codeformer_skip_age:
        return None
    if age < 13:
        return settings.codeformer_child_fidelity
    if age < 18:
        return settings.codeformer_teen_fidelity
    return settings.codeformer_fidelity


def _codeformer_plan(repaired: Image.Image) -> tuple[float | None, str]:
    """Return (fidelity, reason) for the face-restoration step on this image,
    or (None, reason) to skip it. Skips when no face is detectable (babies,
    occlusion, odd angles) since CodeFormer distorts those."""
    try:
        from app.pipeline.identity import get_face_app
        import numpy as np
        app = get_face_app()
        if app == "unavailable":
            return settings.codeformer_fidelity, "InsightFace unavailable, default fidelity"
        arr = np.asarray(repaired)[:, :, ::-1]
        faces = app.get(arr)
        if not faces:
            return None, "no face detected by InsightFace after repair"
        min_age = min(f.age for f in faces)
        fidelity = fidelity_for_age(min_age)
        if fidelity is None:
            return None, f"infant/toddler (age ~{min_age:.0f}) — skipping to avoid distortion"
        return fidelity, f"age ~{min_age:.0f} → fidelity {fidelity:.2f}"
    except Exception:
        return settings.codeformer_fidelity, "face check failed, default fidelity"


def _guard_identity(pre_cf: Image.Image, cf_out: Image.Image) -> Image.Image:
    """Revert CodeFormer if it distorted the face.

    Age estimation is unreliable on old photos (toddlers get estimated as
    adults), so we can't protect children by age alone. Instead we measure it:
    compare the face identity before and after CodeFormer. If identity dropped
    below the floor, CodeFormer restructured the person — keep the un-restored
    face. If identity can't be measured (no face model / no detectable face),
    keep the CodeFormer output (it usually helps)."""
    if cf_out is pre_cf:
        return cf_out  # stage errored and passed through
    sim = identity_similarity(pre_cf, cf_out)
    if sim is not None and sim < settings.codeformer_min_identity:
        logger.warning("CodeFormer identity drift %.2f < %.2f — reverting to pre-restore face",
                       sim, settings.codeformer_min_identity)
        return pre_cf
    if sim is not None:
        logger.info("CodeFormer identity preserved (%.2f)", sim)
    return cf_out


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
        fidelity, reason = _codeformer_plan(out)
        if fidelity is not None:
            logger.info("Step 2: Face restoration (CodeFormer) — %s", reason)
            pre_cf = out
            cf_out = await _safe_stage("face-restore",
                                       lambda: codeformer(pre_cf, fidelity=fidelity), pre_cf)
            out = _guard_identity(pre_cf, cf_out)
        else:
            logger.info("Step 2: Skipping CodeFormer — %s", reason)

    if analysis.is_bw:
        logger.info("Step 3: Colorization (%s)", settings.colorizer)
        out = await _safe_stage("colorize", lambda: _colorize(out), out)

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
