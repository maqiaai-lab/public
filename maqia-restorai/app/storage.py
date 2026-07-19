from pathlib import Path
from PIL import Image
import io
import uuid

from app.config import settings


def ensure_dirs():
    (settings.storage_dir / "originals").mkdir(parents=True, exist_ok=True)
    (settings.storage_dir / "results").mkdir(parents=True, exist_ok=True)


def save_original(img: Image.Image) -> str:
    ensure_dirs()
    filename = f"{uuid.uuid4().hex}.png"
    path = settings.storage_dir / "originals" / filename
    img.save(path, format="PNG")
    return str(path)


def save_result(img: Image.Image, job_id: str) -> str:
    ensure_dirs()
    filename = f"{job_id}.png"
    path = settings.storage_dir / "results" / filename
    img.save(path, format="PNG")
    return str(path)


def image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def bytes_to_image(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))
