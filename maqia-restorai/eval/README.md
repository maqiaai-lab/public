# Digitization battle-test

Objective, ground-truth eval for the phone-capture digitization detector
(`app/pipeline/digitize`). Composites real photos onto synthetic surfaces via
known perspective transforms — the destination quad IS the ground truth — so
detection accuracy is measured, not eyeballed.

## Run

```bash
# Put a few real damaged photos here first (any .jpg):
#   eval/fixtures/*.jpg
python -m eval.digitize_eval
```

Emits a summary table + `eval/report.html` (visual grid of every case with the
detected quad drawn on it; green = pass, red = fail).

## What it measures

| Metric | Meaning |
|--------|---------|
| `detection_rate` | fraction of captures where a quad was found (force path) |
| `mean_iou` / `median_iou` | detected quad vs ground-truth quad |
| `pass_rate` | IoU ≥ 0.85 (tight enough to crop cleanly) |
| `median_corner_err` | mean corner distance / image diagonal |
| `auto_recall` | of real captures, how many the *conservative auto gate* flags |
| `false_positive_rate` | already-digital photos wrongly flagged as captures |

## Coverage

Each photo is composited across 6 backgrounds (wood, dark, cloth, white desk,
busy, hand), 5 perspectives (flat → heavy keystone, rotated, offcenter), and
5 lighting conditions (even, warm, cool, uneven, glare), plus an explicit
low-contrast hard-case set.

## Current results (3 fixtures, 39 cases)

- detection 100% · median IoU 0.96 · **pass@0.75 = 95%** · false-positive 0%
- Fast path ~100 ms; low-contrast cases trigger a GrabCut refinement (~1 s).
- Remaining tail (<5%) is adversarial-synthetic (offcenter + glare + cloth,
  borderless dark-on-dark) — harder than typical real captures, which have a
  paper border.
