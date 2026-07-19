import numpy as np
from PIL import Image

from app.models import Analysis


def detect_faces(img: Image.Image) -> int:
    arr = np.asarray(img)

    # Try OpenCV cascade if available
    try:
        import cv2
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=2, minSize=(30, 30),
        )
        if len(faces) > 0:
            return len(faces)
    except Exception:
        pass

    # Heuristic: old portrait photos almost always contain faces even when
    # damage defeats the cascade. If the center region has meaningful contrast
    # (not a blank/uniform image), assume a face is present.
    gray = np.mean(arr, axis=2)
    h, w = gray.shape
    center = gray[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
    if float(np.std(center)) > 25:
        return 1

    return 0


def analyze(img: Image.Image) -> Analysis:
    arr = np.asarray(img)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    chroma = np.mean(np.abs(r.astype(int) - g) + np.abs(g.astype(int) - b))
    is_bw = chroma < 12

    n_faces = detect_faces(img)

    return Analysis(
        is_bw=bool(is_bw),
        has_faces=n_faces > 0,
        n_faces=n_faces,
        megapixels=(img.width * img.height) / 1e6,
    )
