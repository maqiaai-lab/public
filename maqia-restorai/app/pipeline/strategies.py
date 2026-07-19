from PIL import Image
import logging

from app.models import Analysis, RestoreResult
from app.config import settings
from app.pipeline.identity import identity_similarity
from app.pipeline.models.replicate_models import (
    bringing_old_photos_back,
    codeformer,
    ddcolor,
    real_esrgan_upscale,
)

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
