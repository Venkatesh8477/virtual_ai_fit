import cv2
import numpy as np
import base64

try:
    import mediapipe as mp
    mp_selfie_segmentation = mp.solutions.selfie_segmentation
    HAS_MEDIAPIPE_SEGMENTATION = True
except Exception as e:
    print(f"[Segmentation Engine] MediaPipe Selfie Segmentation warning: {e}. Fallback active.")
    HAS_MEDIAPIPE_SEGMENTATION = False

def segment_person_background(image_bytes: bytes) -> dict:
    """
    Removes background using MediaPipe Selfie Segmentation model.
    Returns transparent PNG image bytes and Base64 Data URL.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Failed to decode image for background removal.")

    h, w, _ = img.shape
    segmented_rgba = None
    mask = None

    if HAS_MEDIAPIPE_SEGMENTATION:
        try:
            with mp_selfie_segmentation.SelfieSegmentation(model_selection=0) as segmentor:
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                results = segmentor.process(rgb_img)
                
                # Segmentation mask (probability map between 0 and 1)
                condition = results.segmentation_mask > 0.4
                
                # Create BGRA image (with alpha channel)
                b_channel, g_channel, r_channel = cv2.split(img)
                alpha_channel = np.where(condition, 255, 0).astype(np.uint8)
                
                # Smooth mask edges with Gaussian blur for clean anti-aliasing
                alpha_channel = cv2.GaussianBlur(alpha_channel, (5, 5), 0)
                
                segmented_rgba = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))
                mask = results.segmentation_mask
        except Exception as err:
            print(f"[Segmentation Engine] MediaPipe exception: {err}")
            segmented_rgba = None

    # Fallback OpenCV segmentation if MediaPipe isn't available or fails
    if segmented_rgba is None:
        segmented_rgba = generate_fallback_segmentation(img)

    # Encode transparent RGBA image to PNG
    _, buffer = cv2.imencode('.png', segmented_rgba)
    segmented_png_bytes = buffer.tobytes()
    segmented_b64 = base64.b64encode(segmented_png_bytes).decode('utf-8')
    data_url = f"data:image/png;base64,{segmented_b64}"

    return {
        "segmented_bytes": segmented_png_bytes,
        "segmented_data_url": data_url,
        "width": w,
        "height": h
    }

def generate_fallback_segmentation(img: np.ndarray) -> np.ndarray:
    """Generates clean background-removed PNG using saliency and GrabCut segmentation."""
    h, w, _ = img.shape
    
    # Create initial bounding box around central area where subject is located
    margin_w, margin_h = int(w * 0.1), int(h * 0.05)
    rect = (margin_w, margin_h, w - 2 * margin_w, h - 2 * margin_h)
    
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    try:
        cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 3, cv2.GC_INIT_WITH_RECT)
        mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype(np.uint8)
        mask2 = cv2.GaussianBlur(mask2, (5, 5), 0)
    except Exception as e:
        print(f"[Segmentation Engine] GrabCut fallback error: {e}")
        # Default simple center ellipse mask
        mask2 = np.zeros((h, w), np.uint8)
        cv2.ellipse(mask2, (w // 2, h // 2), (int(w * 0.35), int(h * 0.45)), 0, 0, 360, 255, -1)

    b, g, r = cv2.split(img)
    return cv2.merge((b, g, r, mask2))
