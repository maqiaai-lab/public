# Maqia RestorAI

AI Photo Restoration Engine — faithful chain pipeline for heritage photo restoration.

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure API keys
cp .env.example .env
# Edit .env with your REPLICATE_API_TOKEN and GEMINI_API_KEY

# 3a. Restore a photo directly (CLI)
python restore.py path/to/old_photo.jpg

# 3b. Or run the API server (+ mobile camera-capture web UI at http://localhost:8000/ )
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Digitization (photo of a physical print)

Users often don't have a scan — just the physical photo. The pipeline
auto-handles a phone snapshot of a print: it detects the photo's edges,
de-skews the perspective, crops out the background, and corrects the color
cast **before** restoration. No user action needed — it's auto-detected and
skipped for already-digital uploads.

- **Web UI** (`/`): "Take a photo of your print" opens the phone's rear camera.
- **API**: `POST /restore?digitize=auto|force|skip`
- **CLI**: `python restore.py capture.jpg --digitize auto`

The digitization stage uses a strategy pattern (`app/pipeline/digitize/`).
Single-shot ships today; a multi-shot strategy (merge several frames to remove
glare / recover detail) plugs in via `digitize_strategy="multi_shot"` config
with no changes to the rest of the pipeline.

## API usage

```bash
# Submit a photo for restoration
curl -X POST http://localhost:8000/restore \
  -F "file=@old_photo.jpg" \
  -F "mode=faithful"

# Check job status
curl http://localhost:8000/restore/{job_id}

# Download result (once status is "done")
curl http://localhost:8000/files/results/{job_id}.png -o restored.png
```

## Pipeline

**Faithful chain** (default): Damage repair → Face restoration → Colorization → Upscale

| Step | Model | Purpose |
|------|-------|---------|
| 1 | Bringing Old Photos Back to Life | Scratch/tear/fade repair |
| 2 | CodeFormer (fidelity=0.75) | Identity-preserving face restoration |
| 3 | DDColor | B&W → color (skipped for color photos) |
| 4 | Real-ESRGAN | Restorative 2x upscale |

**Rescue fallback** (auto-escalation or `mode=enhanced`): Gemini generative restoration for severely damaged photos.

## Docker

```bash
docker compose up --build
```
