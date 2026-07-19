#!/usr/bin/env python3
"""
CLI tool — restore a photo directly without the API server.

Usage:
    python restore.py input.jpg [--mode faithful|enhanced] [--output restored.png]
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from PIL import Image
from app.pipeline.preprocess import preprocess
from app.pipeline.analysis import analyze
from app.pipeline.strategies import restore_full
from app.models import EngineMode


async def main():
    parser = argparse.ArgumentParser(description="Restore a damaged photo")
    parser.add_argument("input", help="Path to the input image")
    parser.add_argument("--mode", choices=["faithful", "enhanced"], default="faithful")
    parser.add_argument("--output", "-o", default=None, help="Output path (default: input_restored.png)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_stem(input_path.stem + "_restored").with_suffix(".png")
    mode = EngineMode(args.mode)

    print(f"Loading {input_path}...")
    raw = input_path.read_bytes()

    print("Preprocessing...")
    img = preprocess(raw)

    print("Analyzing damage...")
    analysis = analyze(img)
    print(f"  B&W: {analysis.is_bw} | Faces: {analysis.n_faces} | {analysis.megapixels:.1f} MP")

    print(f"Restoring (mode={mode.value})...")
    restored_img, result = await restore_full(img, analysis, mode)

    restored_img.save(output_path)
    print(f"\nDone! Saved to {output_path}")
    print(f"  Engine: {result.engine}")
    if result.identity_score is not None:
        print(f"  Identity score: {result.identity_score:.3f}")
    if result.needs_review:
        print("  WARNING: flagged for review (identity may have drifted)")


if __name__ == "__main__":
    asyncio.run(main())
