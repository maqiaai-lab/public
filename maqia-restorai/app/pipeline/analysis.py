import numpy as np
from PIL import Image

from app.models import Analysis


def detect_faces_simple(img: Image.Image) -> int:
    """Basic face detection using OpenCV Haar cascades as a lightweight fallback."""
    try:
        import cv2
        arr = np.asarray(img)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        return len(faces)
    except Exception:
        return 0


def analyze(img: Image.Image) -> Analysis:
    arr = np.asarray(img)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    chroma = np.mean(np.abs(r.astype(int) - g) + np.abs(g.astype(int) - b))
    is_bw = chroma < 12

    n_faces = detect_faces_simple(img)

    return Analysis(
        is_bw=bool(is_bw),
        has_faces=n_faces > 0,
        n_faces=n_faces,
        megapixels=(img.width * img.height) / 1e6,
    )
