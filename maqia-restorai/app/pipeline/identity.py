import numpy as np
from PIL import Image
from typing import Optional


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


_face_app = None


def get_face_app():
    global _face_app
    if _face_app is None:
        try:
            from insightface.app import FaceAnalysis
            _face_app = FaceAnalysis(
                name="buffalo_l", providers=["CPUExecutionProvider"]
            )
            _face_app.prepare(ctx_id=0, det_size=(640, 640))
        except Exception:
            _face_app = "unavailable"
    return _face_app


def get_face_embedding(img: Image.Image) -> Optional[np.ndarray]:
    app = get_face_app()
    if app == "unavailable":
        return None
    arr = np.asarray(img)[:, :, ::-1]  # RGB -> BGR for insightface
    faces = app.get(arr)
    if not faces:
        return None
    largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return largest.embedding


def identity_similarity(original: Image.Image, restored: Image.Image) -> Optional[float]:
    emb_orig = get_face_embedding(original)
    emb_rest = get_face_embedding(restored)
    if emb_orig is None or emb_rest is None:
        return None
    return cosine_similarity(emb_orig, emb_rest)
