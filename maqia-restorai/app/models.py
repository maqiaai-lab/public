from pydantic import BaseModel
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


class Analysis(BaseModel):
    is_bw: bool
    has_faces: bool
    n_faces: int
    megapixels: float
    min_face_age: Optional[float] = None


class RestoreResult(BaseModel):
    engine: str
    must_verify: bool = False
    needs_review: bool = False
    identity_score: Optional[float] = None
    result_path: Optional[str] = None
    original_path: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    engine: Optional[str] = None
    identity_score: Optional[float] = None
    result_url: Optional[str] = None
    original_url: Optional[str] = None
