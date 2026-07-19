import uuid
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.config import settings
from app.models import JobStatus, JobResponse, JobStatusResponse
from app.storage import save_original, save_result, ensure_dirs
from app.pipeline.preprocess import preprocess
from app.pipeline.analysis import analyze
from app.pipeline.strategies import restore_full

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

jobs: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_dirs()
    yield


app = FastAPI(
    title="Maqia RestorAI",
    description="AI Photo Restoration Engine — Faithful chain pipeline",
    version="0.1.0",
    lifespan=lifespan,
)


async def _process_job(job_id: str, img_bytes: bytes):
    try:
        jobs[job_id]["status"] = JobStatus.PROCESSING

        img = preprocess(img_bytes)
        original_path = save_original(img)
        jobs[job_id]["original_path"] = original_path

        analysis = analyze(img)
        logger.info("Job %s analysis: %s", job_id, analysis.model_dump())

        restored_img, result = await restore_full(img, analysis)

        result_path = save_result(restored_img, job_id)
        result.result_path = result_path
        result.original_path = original_path

        jobs[job_id]["status"] = JobStatus.NEEDS_REVIEW if result.needs_review else JobStatus.DONE
        jobs[job_id]["result"] = result.model_dump()
        jobs[job_id]["result_path"] = result_path
        logger.info("Job %s complete: %s (id_score=%.3f)",
                    job_id, result.engine, result.identity_score or 0)

    except Exception as e:
        logger.exception("Job %s failed", job_id)
        jobs[job_id]["status"] = JobStatus.FAILED
        jobs[job_id]["error"] = str(e)


@app.post("/restore", response_model=JobResponse)
async def restore_photo(file: UploadFile, background_tasks: BackgroundTasks):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Upload must be an image file")

    raw = await file.read()
    if len(raw) > 50 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 50MB)")

    job_id = uuid.uuid4().hex[:12]
    jobs[job_id] = {"status": JobStatus.QUEUED}

    background_tasks.add_task(_process_job, job_id, raw)

    return JobResponse(job_id=job_id, status=JobStatus.QUEUED)


@app.get("/restore/{job_id}", response_model=JobStatusResponse)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")

    job = jobs[job_id]
    result = job.get("result", {})

    result_url = f"/files/results/{job_id}.png" if job.get("result_path") else None
    original_path = job.get("original_path")
    original_url = f"/files/originals/{Path(original_path).name}" if original_path else None

    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        engine=result.get("engine"),
        identity_score=result.get("identity_score"),
        result_url=result_url,
        original_url=original_url,
    )


@app.get("/files/results/{filename}")
async def get_result_file(filename: str):
    path = settings.storage_dir / "results" / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(path, media_type="image/png")


@app.get("/files/originals/{filename}")
async def get_original_file(filename: str):
    path = settings.storage_dir / "originals" / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(path, media_type="image/png")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
