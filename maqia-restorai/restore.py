#!/usr/bin/env python3
"""
CLI tool — restore a photo directly without the API server.

Usage:
    python restore.py input.jpg [--output restored.png]
"""
import asyncio
import argparse
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from PIL import Image
from app.pipeline.digitize import digitize_images
from app.pipeline.preprocess import preprocess_image
from app.pipeline.analysis import analyze
from app.pipeline.strategies import restore_full


async def main():
    parser = argparse.ArgumentParser(description="Restore a damaged photo")
    parser.add_argument("input", help="Path to the input image")
    parser.add_argument("--output", "-o", default=None, help="Output path (default: input_restored.png)")
    parser.add_argument("--digitize", choices=["auto", "force", "skip"], default="auto",
                        help="Physical-photo digitization: auto-detect (default), force, or skip")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_stem(input_path.stem + "_restored").with_suffix(".png")

    print(f"Loading {input_path}...")
    raw = input_path.read_bytes()

    print("Digitizing (if photo-of-photo)...")
    dig_mode = {"auto": None, "force": True, "skip": False}[args.digitize]
    dig = digitize_images([Image.open(io.BytesIO(raw))], force=dig_mode)
    if dig.was_digitized:
        print(f"  Detected & rectified physical photo (confidence {dig.confidence:.2f})")

    print("Preprocessing...")
    img = preprocess_image(dig.image)

    print("Analyzing damage...")
    analysis = analyze(img)
    print(f"  B&W: {analysis.is_bw} | Faces: {analysis.n_faces} | {analysis.megapixels:.1f} MP")

    print("Restoring...")
    restored_img, result = await restore_full(img, analysis)

    restored_img.save(output_path)
    print(f"\nDone! Saved to {output_path}")
    print(f"  Engine: {result.engine}")
    if result.identity_score is not None:
        print(f"  Identity score: {result.identity_score:.3f}")
    if result.needs_review:
        print("  WARNING: flagged for review (identity may have drifted)")


if __name__ == "__main__":
    asyncio.run(main())
