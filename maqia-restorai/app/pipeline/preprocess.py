from PIL import Image, ImageOps
import io

from app.config import settings


def preprocess(raw_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    img.thumbnail((settings.max_edge, settings.max_edge))
    return img
