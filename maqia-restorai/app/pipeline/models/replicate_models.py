import replicate
import httpx
from PIL import Image
import io
from typing import Optional

from app.config import settings


async def _download_image(url: str) -> Image.Image:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content))


def _upload_to_replicate(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    url = replicate.files.create(buf, filename="input.png")
    return str(url)


async def bringing_old_photos_back(img: Image.Image, with_scratch: bool = True) -> Image.Image:
    input_url = _upload_to_replicate(img)
    output = replicate.run(
        "microsoft/bringing-old-photos-back-to-life:c75db81db6cbd809d93f6f8a5ce4c3da690e7ae1f8a6c9df73a73f4f0f1459a1",
        input={
            "image": input_url,
            "with_scratch": with_scratch,
        },
    )
    output_url = str(output)
    return await _download_image(output_url)


async def codeformer(img: Image.Image, fidelity: float = 0.75) -> Image.Image:
    input_url = _upload_to_replicate(img)
    output = replicate.run(
        "sczhou/codeformer:7de2ea26c616d5bf2245ad0d5e24f0ff9a6204578a5c876db53142edd9d2cd56",
        input={
            "image": input_url,
            "codeformer_fidelity": fidelity,
            "upscale": 1,
            "face_upsample": True,
            "background_enhance": False,
        },
    )
    output_url = str(output)
    return await _download_image(output_url)


async def ddcolor(img: Image.Image) -> Image.Image:
    input_url = _upload_to_replicate(img)
    output = replicate.run(
        "piddnad/ddcolor:ca494ba129e44e45f661d6ece83c4c98a9a7c774309beca01571ae120b0d2b68",
        input={"image": input_url},
    )
    output_url = output[0] if isinstance(output, list) else str(output)
    return await _download_image(output_url)


async def real_esrgan_upscale(img: Image.Image, scale: int = 2) -> Image.Image:
    input_url = _upload_to_replicate(img)
    output = replicate.run(
        "nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa",
        input={
            "image": input_url,
            "scale": scale,
            "face_enhance": False,
        },
    )
    output_url = str(output)
    return await _download_image(output_url)
