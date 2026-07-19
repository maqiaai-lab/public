"""Perspective-correct (de-skew) the photo using its detected corners."""
import numpy as np
import cv2


def perspective_transform(arr: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """
    Warp the quadrilateral defined by `corners` (TL, TR, BR, BL) into a
    flat, axis-aligned rectangle. Output size is inferred from the edge
    lengths of the detected quad so the photo's aspect ratio is preserved.
    """
    tl, tr, br, bl = corners

    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    max_width = int(max(width_top, width_bottom))

    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)
    max_height = int(max(height_left, height_right))

    max_width = max(max_width, 1)
    max_height = max(max_height, 1)

    dst = np.array(
        [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
        dtype=np.float32,
    )

    matrix = cv2.getPerspectiveTransform(corners.astype(np.float32), dst)
    return cv2.warpPerspective(
        arr, matrix, (max_width, max_height),
        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE,
    )
