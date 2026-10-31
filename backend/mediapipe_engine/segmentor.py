import base64

import cv2
import numpy as np

SEGMENTATION_THRESHOLD = 0.4
MASK_BLUR_KERNEL = 5

selfie_segmentation = None
try:
    from mediapipe.python.solutions import selfie_segmentation

    HAS_MEDIAPIPE_SEGMENTATION = True
    MEDIAPIPE_SEGMENTATION_IMPORT_ERROR = None
except Exception as err:
    MEDIAPIPE_SEGMENTATION_IMPORT_ERROR = str(err)
    HAS_MEDIAPIPE_SEGMENTATION = False
    print(f"[Segmentation Engine] MediaPipe Selfie Segmentation unavailable: {err}")


def segment_person_background(image_bytes: bytes) -> dict:
    """
    Return an RGBA PNG and its grayscale alpha mask, preserving the input dimensions.
    The mask uses MediaPipe's foreground probability threshold when available.
    """
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image for background removal.")

    height, width, _ = img.shape
    segmented_rgba = None
    segmentation_method = None
    fallback_reason = None

    if HAS_MEDIAPIPE_SEGMENTATION and selfie_segmentation is not None:
        try:
            with selfie_segmentation.SelfieSegmentation(model_selection=0) as model:
                rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = model.process(rgb_image)
                probability_mask = np.asarray(
                    getattr(results, "segmentation_mask", None), dtype=np.float32
                )

                if probability_mask.shape != (height, width):
                    raise ValueError("MediaPipe returned a mask with unexpected dimensions.")
                if not np.isfinite(probability_mask).all():
                    raise ValueError("MediaPipe returned a mask with non-finite values.")
                if np.any(probability_mask < 0) or np.any(probability_mask > 1):
                    raise ValueError("MediaPipe returned probabilities outside the [0, 1] range.")

                alpha = np.where(
                    probability_mask > SEGMENTATION_THRESHOLD, 255, 0
                ).astype(np.uint8)
                alpha = cv2.GaussianBlur(alpha, (MASK_BLUR_KERNEL, MASK_BLUR_KERNEL), 0)
                blue, green, red = cv2.split(img)
                segmented_rgba = cv2.merge((blue, green, red, alpha))
                segmentation_method = "mediapipe_selfie_segmentation"
        except Exception as err:
            fallback_reason = f"MediaPipe Selfie Segmentation failed: {err}"
            print(f"[Segmentation Engine] {fallback_reason}; using OpenCV fallback.")
    else:
        fallback_reason = (
            MEDIAPIPE_SEGMENTATION_IMPORT_ERROR
            or "MediaPipe Selfie Segmentation is unavailable."
        )
        print(f"[Segmentation Engine] {fallback_reason}; using OpenCV fallback.")

    if segmented_rgba is None:
        segmented_rgba, segmentation_method = generate_fallback_segmentation(img)

    if segmented_rgba.shape != (height, width, 4):
        raise RuntimeError("Segmentation output must be an RGBA image matching the input dimensions.")

    encoded, png_buffer = cv2.imencode(".png", segmented_rgba)
    if not encoded:
        raise RuntimeError("Could not encode the segmented image.")

    alpha = segmented_rgba[:, :, 3]
    mask_encoded, mask_buffer = cv2.imencode(".png", alpha)
    if not mask_encoded:
        raise RuntimeError("Could not encode the segmentation mask.")

    segmented_png = png_buffer.tobytes()
    mask_png = mask_buffer.tobytes()
    return {
        "segmented_bytes": segmented_png,
        "segmented_data_url": f"data:image/png;base64,{base64.b64encode(segmented_png).decode('utf-8')}",
        "mask_data_url": f"data:image/png;base64,{base64.b64encode(mask_png).decode('utf-8')}",
        "segmentation_method": segmentation_method,
        "segmentation_warning": fallback_reason,
        "foreground_fraction": round(float(np.mean(alpha >= 128)), 4),
        "width": width,
        "height": height
    }


def generate_fallback_segmentation(img: np.ndarray) -> tuple[np.ndarray, str]:
    """Return a labeled OpenCV GrabCut or center-ellipse fallback."""
    height, width, _ = img.shape
    margin_w, margin_h = int(width * 0.1), int(height * 0.05)
    rect = (margin_w, margin_h, width - 2 * margin_w, height - 2 * margin_h)
    mask = np.zeros((height, width), np.uint8)
    background_model = np.zeros((1, 65), np.float64)
    foreground_model = np.zeros((1, 65), np.float64)
    method = "opencv_grabcut_fallback"

    try:
        cv2.grabCut(
            img, mask, rect, background_model, foreground_model, 3, cv2.GC_INIT_WITH_RECT
        )
        alpha = np.where(
            (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0
        ).astype(np.uint8)
        alpha = cv2.GaussianBlur(alpha, (MASK_BLUR_KERNEL, MASK_BLUR_KERNEL), 0)
    except Exception as err:
        print(f"[Segmentation Engine] GrabCut fallback failed: {err}; using center ellipse.")
        alpha = np.zeros((height, width), np.uint8)
        cv2.ellipse(
            alpha,
            (width // 2, height // 2),
            (int(width * 0.35), int(height * 0.45)),
            0,
            0,
            360,
            (255,),
            -1
        )
        method = "center_ellipse_fallback"

    blue, green, red = cv2.split(img)
    return cv2.merge((blue, green, red, alpha)), method
