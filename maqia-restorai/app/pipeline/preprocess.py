from PIL import Image, ImageOps
import io

from app.config import settings


def preprocess_image(img: Image.Image) -> Image.Image:
    """Normalize a PIL image for the restoration chain: honor orientation,
    drop to RGB, cap the long edge so we don't pay 4K prices on the restore
    pass (upscaling happens at the end)."""
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    img.thumbnail((settings.max_edge, settings.max_edge))
    return img


def preprocess(raw_bytes: bytes) -> Image.Image:
    return preprocess_image(Image.open(io.BytesIO(raw_bytes)))
