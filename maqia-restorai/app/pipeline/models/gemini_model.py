from google import genai
from google.genai import types
from PIL import Image
import io

from app.config import settings
from app.models import Analysis


def _build_instruction(analysis: Analysis) -> str:
    parts = [
        "Restore this old, damaged photograph.",
        "Repair scratches, tears, creases, and fading.",
        "Reduce noise and correct exposure.",
        "Preserve the exact identity, facial features, age, and proportions of every "
        "person. Do NOT beautify, slim, smooth wrinkles, or alter who they are.",
    ]
    if analysis.is_bw:
        parts.append("Add natural, historically-plausible color.")
    return " ".join(parts)


async def nano_banana_restore(img: Image.Image, analysis: Analysis) -> Image.Image:
    client = genai.Client(api_key=settings.gemini_api_key)
    instruction = _build_instruction(analysis)

    buf = io.BytesIO()
    img.save(buf, format="PNG")

    resp = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
            instruction,
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            return Image.open(io.BytesIO(part.inline_data.data))

    raise RuntimeError("Gemini returned no image")
