import httpx
import base64
import io
import time
from PIL import Image

from app.config import settings

API_BASE = "https://api.replicate.com/v1"
POLL_INTERVAL = 2.0
MAX_WAIT = 300


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.replicate_api_token}",
        "Content-Type": "application/json",
    }


def _image_to_data_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


async def _run_model(version: str, input_data: dict, max_retries: int = 4) -> str:
    async with httpx.AsyncClient(timeout=30.0, verify="/root/.ccr/ca-bundle.crt") as client:
        for attempt in range(max_retries):
            resp = await client.post(
                f"{API_BASE}/predictions",
                headers=_headers(),
                json={"version": version, "input": input_data},
            )
            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                import logging
                logging.getLogger(__name__).warning("Rate limited, retrying in %ds...", wait)
                await _sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            raise RuntimeError("Rate limited after all retries")
        prediction = resp.json()

        get_url = prediction["urls"]["get"]
        elapsed = 0.0
        while prediction["status"] not in ("succeeded", "failed", "canceled"):
            await _sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            if elapsed > MAX_WAIT:
                raise TimeoutError(f"Prediction timed out after {MAX_WAIT}s")
            resp = await client.get(get_url, headers=_headers())
            resp.raise_for_status()
            prediction = resp.json()

        if prediction["status"] != "succeeded":
            raise RuntimeError(f"Prediction failed: {prediction.get('error', 'unknown')}")

        output = prediction["output"]
        if isinstance(output, list):
            return output[0] if isinstance(output[0], str) else output[0]["file"]
        return str(output)


async def _sleep(seconds: float):
    import asyncio
    await asyncio.sleep(seconds)


async def _download_image(url: str) -> Image.Image:
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, verify="/root/.ccr/ca-bundle.crt") as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content))


async def bringing_old_photos_back(img: Image.Image, with_scratch: bool = True) -> Image.Image:
    data_uri = _image_to_data_uri(img)
    output_url = await _run_model(
        "c75db81db6cbd809d93cc3b7e7a088a351a3349c9fa02b6d393e35e0d51ba799",
        {"image": data_uri, "with_scratch": with_scratch},
    )
    return await _download_image(output_url)


async def codeformer(img: Image.Image, fidelity: float = 0.75) -> Image.Image:
    data_uri = _image_to_data_uri(img)
    output_url = await _run_model(
        "cc4956dd26fa5a7185d5660cc9100fab1b8070a1d1654a8bb5eb6d443b020bb2",
        {
            "image": data_uri,
            "codeformer_fidelity": fidelity,
            "upscale": 1,
            "face_upsample": True,
            "background_enhance": False,
        },
    )
    return await _download_image(output_url)


async def ddcolor(img: Image.Image) -> Image.Image:
    data_uri = _image_to_data_uri(img)
    output_url = await _run_model(
        "ca494ba129e44e45f661d6ece83c4c98a9a7c774309beca01429b58fce8aa695",
        {"image": data_uri},
    )
    return await _download_image(output_url)


async def real_esrgan_upscale(img: Image.Image, scale: int = 2) -> Image.Image:
    data_uri = _image_to_data_uri(img)
    output_url = await _run_model(
        "b3ef194191d13140337468c916c2c5b96dd0cb06dffc032a022a31807f6a5ea8",
        {"image": data_uri, "scale": scale, "face_enhance": False},
    )
    return await _download_image(output_url)
