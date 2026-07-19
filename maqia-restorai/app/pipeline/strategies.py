from PIL import Image
import logging

from app.models import Analysis, RestoreResult, EngineMode
from app.config import settings
from app.pipeline.identity import identity_similarity
from app.pipeline.models.replicate_models import (
    bringing_old_photos_back,
    codeformer,
    ddcolor,
    real_esrgan_upscale,
)
from app.pipeline.models.gemini_model import nano_banana_restore

logger = logging.getLogger(__name__)


async def run_faithful_chain(img: Image.Image, analysis: Analysis) -> Image.Image:
    logger.info("Step 1: Global damage repair (Bringing Old Photos Back to Life)")
    out = await bringing_old_photos_back(img, with_scratch=True)

    if analysis.has_faces:
        logger.info("Step 2: Face restoration (CodeFormer, fidelity=%.2f)", settings.codeformer_fidelity)
        out = await codeformer(out, fidelity=settings.codeformer_fidelity)

    if analysis.is_bw:
        logger.info("Step 3: Colorization (DDColor)")
        out = await ddcolor(out)

    logger.info("Step 4: Restorative upscale (Real-ESRGAN 2x)")
    out = await real_esrgan_upscale(out, scale=2)

    return out


async def run_rescue(img: Image.Image, analysis: Analysis) -> Image.Image:
    logger.info("Running rescue engine (Gemini)")
    return await nano_banana_restore(img, analysis)


async def restore(img: Image.Image, analysis: Analysis, mode: EngineMode = EngineMode.FAITHFUL) -> RestoreResult:
    if mode == EngineMode.ENHANCED:
        restored = await run_rescue(img, analysis)
        id_score = identity_similarity(img, restored)
        return RestoreResult(
            engine="nano-banana-pro",
            must_verify=True,
            identity_score=id_score,
            needs_review=id_score is not None and id_score < settings.review_threshold,
        )

    # Faithful chain is the default
    restored = await run_faithful_chain(img, analysis)
    id_score = identity_similarity(img, restored)

    # Auto-escalation: if faithful chain failed to preserve identity, try rescue
    if analysis.has_faces and id_score is not None and id_score < settings.identity_threshold:
        logger.warning(
            "Faithful chain identity score %.3f below threshold %.3f — escalating to rescue",
            id_score, settings.identity_threshold,
        )
        rescue_img = await run_rescue(img, analysis)
        rescue_score = identity_similarity(img, rescue_img)

        # Pick the better result
        if rescue_score is not None and rescue_score > id_score:
            restored = rescue_img
            id_score = rescue_score
            engine = "faithful-chain+rescue-escalation"
        else:
            engine = "faithful-chain"

        return RestoreResult(
            engine=engine,
            identity_score=id_score,
            needs_review=True,
        )

    return RestoreResult(
        engine="faithful-chain",
        identity_score=id_score,
        needs_review=id_score is not None and id_score < settings.review_threshold,
    )


# Keep a reference to the restored image in memory during processing
_last_restored: Image.Image | None = None


async def restore_full(img: Image.Image, analysis: Analysis, mode: EngineMode = EngineMode.FAITHFUL) -> tuple[Image.Image, RestoreResult]:
    global _last_restored

    if mode == EngineMode.ENHANCED:
        restored = await run_rescue(img, analysis)
        id_score = identity_similarity(img, restored)
        result = RestoreResult(
            engine="nano-banana-pro",
            must_verify=True,
            identity_score=id_score,
            needs_review=id_score is not None and id_score < settings.review_threshold,
        )
        _last_restored = restored
        return restored, result

    restored = await run_faithful_chain(img, analysis)
    id_score = identity_similarity(img, restored)

    if analysis.has_faces and id_score is not None and id_score < settings.identity_threshold:
        logger.warning(
            "Faithful chain identity score %.3f — escalating to rescue", id_score
        )
        rescue_img = await run_rescue(img, analysis)
        rescue_score = identity_similarity(img, rescue_img)

        if rescue_score is not None and rescue_score > id_score:
            restored = rescue_img
            id_score = rescue_score
            engine = "faithful-chain+rescue-escalation"
        else:
            engine = "faithful-chain"

        result = RestoreResult(engine=engine, identity_score=id_score, needs_review=True)
        _last_restored = restored
        return restored, result

    result = RestoreResult(
        engine="faithful-chain",
        identity_score=id_score,
        needs_review=id_score is not None and id_score < settings.review_threshold,
    )
    _last_restored = restored
    return restored, result
