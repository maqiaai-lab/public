"""Battle-test the digitization detector against synthetic phone-captures with
known ground-truth corners.

Metrics:
  - detection rate       : fraction of captures where a quad was returned
  - mean/median IoU       : detected quad vs ground-truth quad
  - corner error         : mean corner distance / image diagonal
  - pass rate            : IoU >= PASS_IOU (clean enough to crop)
  - false-positive rate  : already-digital images wrongly flagged as captures

Run:  python -m eval.digitize_eval            (from repo root)
Emits eval/report.html and prints a summary table.
"""
import sys
import io
import json
import base64
from pathlib import Path
from itertools import product

import numpy as np
import cv2
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.capture_sim import (
    make_capture, BACKGROUNDS, LIGHTING, persp_presets,
)
from app.pipeline.digitize.steps.edge_detect import detect_photo_quad
from app.pipeline.digitize.detector import looks_like_capture

PASS_IOU = 0.85
FIXTURES = Path(__file__).parent / "fixtures"
OUT_HTML = Path(__file__).parent / "report.html"


def quad_iou(a: np.ndarray, b: np.ndarray, size=500) -> float:
    """IoU of two quads by rasterizing to masks."""
    def mask(q):
        m = np.zeros((size, size), np.uint8)
        cv2.fillPoly(m, [q.astype(np.int32)], 255)
        return m > 0
    # normalize both quads into a common size box
    allpts = np.vstack([a, b])
    mn = allpts.min(0); mx = allpts.max(0)
    span = np.maximum(mx - mn, 1)
    na = (a - mn) / span * (size - 1)
    nb = (b - mn) / span * (size - 1)
    ma, mb = mask(na), mask(nb)
    inter = np.logical_and(ma, mb).sum()
    union = np.logical_or(ma, mb).sum()
    return float(inter / union) if union else 0.0


def corner_error(det: np.ndarray, gt: np.ndarray, diag: float) -> float:
    return float(np.mean(np.linalg.norm(det - gt, axis=1)) / diag)


def _thumb(arr: np.ndarray, corners=None, max_edge=180) -> str:
    img = arr.copy()
    if corners is not None:
        cv2.polylines(img, [corners.astype(np.int32)], True, (0, 255, 0), 3)
    h, w = img.shape[:2]
    s = max_edge / max(h, w)
    img = cv2.resize(img, (int(w*s), int(h*s)))
    buf = io.BytesIO(); Image.fromarray(img).save(buf, format="JPEG", quality=70)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def build_matrix(photos):
    """Curated set covering hard combos without a full cartesian explosion."""
    cases = []
    perspectives = list(persp_presets(100, 100).keys())
    seed = 0
    # Every photo × every perspective on a rotating background/lighting.
    bg_cycle = list(BACKGROUNDS.keys())
    lt_cycle = list(LIGHTING.keys())
    for pi, (pname, parr) in enumerate(photos.items()):
        for persp in perspectives:
            bg = bg_cycle[seed % len(bg_cycle)]
            lt = lt_cycle[seed % len(lt_cycle)]
            cases.append((pname, parr, bg, persp, lt, seed))
            seed += 1
    # Explicit hard cases: low-contrast + adversarial lighting
    hard = [
        ("dark", "flat", "even"), ("dark", "heavy", "glare"),
        ("hand", "moderate", "even"), ("hand", "rotated", "uneven"),
        ("busy", "heavy", "glare"), ("busy", "rotated", "even"),
        ("cloth", "offcenter", "cool"), ("wood", "rotated", "glare"),
    ]
    for pname, parr in photos.items():
        for bg, persp, lt in hard:
            cases.append((pname, parr, bg, persp, lt, seed)); seed += 1
    return cases


def main():
    photos = {}
    for f in sorted(FIXTURES.glob("*.jpg")):
        photos[f.stem] = np.asarray(Image.open(f).convert("RGB"))
    if not photos:
        print("No fixtures found in eval/fixtures/"); return

    cases = build_matrix(photos)
    rows = []
    ious, cerrs = [], []
    detected_n = 0

    for (pname, parr, bg, persp, lt, seed) in cases:
        cap = make_capture(parr, pname, bg, persp, lt, seed=seed)
        corners, conf = detect_photo_quad(cap.image)
        diag = np.hypot(*cap.image.shape[:2])

        if corners is None:
            rows.append(dict(photo=pname, bg=bg, persp=persp, light=lt,
                             coverage=round(cap.coverage, 2), detected=False,
                             iou=0.0, cerr=None, conf=round(conf, 2),
                             thumb=_thumb(cap.image)))
            ious.append(0.0)
            continue

        detected_n += 1
        iou = quad_iou(corners, cap.gt_corners)
        cerr = corner_error(corners, cap.gt_corners, diag)
        ious.append(iou); cerrs.append(cerr)
        rows.append(dict(photo=pname, bg=bg, persp=persp, light=lt,
                         coverage=round(cap.coverage, 2), detected=True,
                         iou=round(iou, 3), cerr=round(cerr, 4),
                         conf=round(conf, 2), thumb=_thumb(cap.image, corners)))

    # Negative cases: raw already-digital photos should NOT be flagged by auto.
    neg_rows = []
    fp = 0
    for pname, parr in photos.items():
        is_cap, conf = looks_like_capture(Image.fromarray(parr))
        if is_cap:
            fp += 1
        neg_rows.append(dict(photo=pname, flagged=is_cap, conf=round(conf, 2),
                             thumb=_thumb(parr)))

    # Auto-detect recall: of real captures, how many does the conservative auto
    # gate catch? (The camera path uses force, so this only bounds the file-upload path.)
    auto_hits = 0
    for (pname, parr, bg, persp, lt, seed) in cases:
        cap = make_capture(parr, pname, bg, persp, lt, seed=seed)
        is_cap, _ = looks_like_capture(Image.fromarray(cap.image))
        if is_cap:
            auto_hits += 1

    n = len(cases)
    passes = sum(1 for r in rows if r["detected"] and r["iou"] >= PASS_IOU)
    summary = dict(
        n_cases=n,
        # Force path (camera): raw detector quality
        detection_rate=round(detected_n / n, 3),
        mean_iou=round(float(np.mean(ious)), 3),
        median_iou=round(float(np.median(ious)), 3),
        pass_rate=round(passes / n, 3),
        median_corner_err=round(float(np.median(cerrs)), 4) if cerrs else None,
        # Auto path (file upload): conservative gate
        auto_recall=round(auto_hits / n, 3),
        false_positive_rate=round(fp / len(photos), 3),
    )

    print("\n=== DIGITIZATION BATTLE-TEST ===")
    for k, v in summary.items():
        print(f"  {k:22s}: {v}")

    # Failure breakdown
    print("\n  Failures (IoU < %.2f):" % PASS_IOU)
    fails = [r for r in rows if not (r["detected"] and r["iou"] >= PASS_IOU)]
    if not fails:
        print("    none 🎉")
    for r in fails:
        print(f"    {r['photo']:9s} {r['bg']:11s} {r['persp']:9s} {r['light']:7s} "
              f"cov={r['coverage']} det={r['detected']} iou={r['iou']} conf={r['conf']}")

    _write_html(summary, rows, neg_rows)
    print(f"\n  Report: {OUT_HTML}")
    return summary


def _write_html(summary, rows, neg_rows):
    def card(r):
        ok = r["detected"] and r["iou"] >= PASS_IOU
        border = "#2ecc71" if ok else "#e74c3c"
        cerr = r.get("cerr")
        return f"""<div style="border:3px solid {border};border-radius:8px;padding:6px;background:#1a1d24">
          <img src="{r['thumb']}" style="width:100%;border-radius:4px">
          <div style="font:12px monospace;color:#ccc;margin-top:4px">
            {r['photo']} · {r['bg']}<br>{r['persp']} · {r['light']}<br>
            cov {r['coverage']} · conf {r['conf']}<br>
            <b style="color:{border}">IoU {r['iou']}{' · cerr '+str(cerr) if cerr else ''}</b>
          </div></div>"""

    def neg_card(r):
        border = "#e74c3c" if r["flagged"] else "#2ecc71"
        label = "FALSE POSITIVE" if r["flagged"] else "correctly passed through"
        return f"""<div style="border:3px solid {border};border-radius:8px;padding:6px;background:#1a1d24">
          <img src="{r['thumb']}" style="width:100%;border-radius:4px">
          <div style="font:12px monospace;color:{border};margin-top:4px">{r['photo']}<br>{label}<br>conf {r['conf']}</div></div>"""

    sm = "".join(f"<span style='margin-right:18px'><b>{k}</b>: {v}</span>" for k, v in summary.items())
    grid = "".join(card(r) for r in rows)
    neg = "".join(neg_card(r) for r in neg_rows)
    html = f"""<!doctype html><html><head><meta charset=utf-8><title>Digitize Battle-Test</title></head>
    <body style="background:#0f1115;color:#e8eaed;font-family:sans-serif;padding:20px">
    <h1>Digitization Battle-Test</h1>
    <div style="background:#1a1d24;padding:14px;border-radius:8px;font:14px monospace;line-height:2">{sm}</div>
    <h2>Positive cases (green = IoU ≥ {PASS_IOU})</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px">{grid}</div>
    <h2>Negative cases (already-digital — should pass through)</h2>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px">{neg}</div>
    </body></html>"""
    OUT_HTML.write_text(html)


if __name__ == "__main__":
    main()
