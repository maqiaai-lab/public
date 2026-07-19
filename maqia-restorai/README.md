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

# 3b. Or run the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

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
