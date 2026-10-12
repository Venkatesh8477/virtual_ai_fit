import os
import cv2
import math
import httpx
import base64
import numpy as np
from io import BytesIO
from typing import Optional
from PIL import Image, ImageOps, ImageFilter
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from mediapipe_engine.pose_detector import analyze_body_pose
from mediapipe_engine.segmentor import segment_person_background
from database import DatabaseManager
from utils.auth import get_optional_user_id

router = APIRouter(prefix="/api/tryon", tags=["Virtual Try-On"])

COLAB_TRYON_URL = os.getenv("COLAB_TRYON_URL", "")

@router.post("/analyze")
async def analyze_person(person_image: UploadFile = File(...)):
    """Analyzes full body photo: detects MediaPipe landmarks & performs background segmentation."""
    person_bytes = await person_image.read()
    
    pose_results = analyze_body_pose(person_bytes)
    seg_results = segment_person_background(person_bytes)
    
    return {
        "landmarks": pose_results["landmarks"],
        "metrics": pose_results["metrics"],
        "landmark_visualization": pose_results["landmark_visualization"],
        "segmented_image": seg_results["segmented_data_url"]
    }

@router.post("/generate")
async def generate_virtual_tryon(
    person_image: UploadFile = File(...),
    dress_image: UploadFile = File(...),
    colab_url: Optional[str] = Form(None),
    user_id: Optional[str] = Depends(get_optional_user_id)
):
    """
    Executes High-Precision Virtual Try-On workflow.
    - MediaPipe pose landmark estimation
    - MediaPipe selfie background segmentation
    - IDM-VTON inference via Google Colab URL or Pose-Aligned Garment Extraction & Warping Engine
    """
    person_bytes = await person_image.read()
    dress_bytes = await dress_image.read()

    # Step 1: MediaPipe Pose Analysis
    pose_results = analyze_body_pose(person_bytes)
    
    # Step 2: Background Removal
    seg_results = segment_person_background(person_bytes)

    # Encode original images to Data URLs
    person_b64 = base64.b64encode(person_bytes).decode("utf-8")
    dress_b64 = base64.b64encode(dress_bytes).decode("utf-8")
    person_data_url = f"data:image/jpeg;base64,{person_b64}"
    dress_data_url = f"data:image/jpeg;base64,{dress_b64}"

    target_colab_url = colab_url or COLAB_TRYON_URL
    tryon_result_data_url = None
    engine_used = "High-Precision Pose Warping Engine"

    # Step 3: Send to Google Colab IDM-VTON pipeline if URL is provided
    if target_colab_url and target_colab_url.strip():
        try:
            print(f"[Virtual Try-On] Forwarding request to Colab API: {target_colab_url}")
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{target_colab_url.strip().rstrip('/')}/api/tryon",
                    json={
                        "person_image": person_b64,
                        "dress_image": dress_b64,
                        "landmarks": pose_results["landmarks_dict"]
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    tryon_result_data_url = data.get("result_image")
                    engine_used = "IDM-VTON (Google Colab GPU)"
        except Exception as e:
            print(f"[Virtual Try-On] Colab request failed or timed out: {e}. Falling back to local composite engine.")

    # Step 4: Pose-Aligned Garment Extraction & Warping Engine if Colab is offline/not provided
    if not tryon_result_data_url:
        tryon_result_data_url = generate_pose_aligned_tryon(person_bytes, dress_bytes, pose_results["landmarks_dict"])

    # Step 5: Save to Database History if user is logged in
    history_record = None
    if user_id:
        try:
            history_record = await DatabaseManager.save_tryon_history(
                user_id=user_id,
                person_image=person_data_url,
                dress_image=dress_data_url,
                result_image=tryon_result_data_url,
                body_analysis=pose_results["metrics"],
                segmented_image=seg_results["segmented_data_url"]
            )
        except Exception as e:
            print(f"[Virtual Try-On] History save exception: {e}")

    return {
        "status": "success",
        "engine": engine_used,
        "person_image": person_data_url,
        "dress_image": dress_data_url,
        "landmark_visualization": pose_results["landmark_visualization"],
        "segmented_image": seg_results["segmented_data_url"],
        "result_image": tryon_result_data_url,
        "body_analysis": pose_results["metrics"],
        "landmarks": pose_results["landmarks"],
        "history_id": history_record["id"] if history_record else None
    }

def extract_garment_foreground(dress_bytes: bytes) -> Image.Image:
    """
    Strips background from the dress image using saliency/GrabCut thresholding,
    returning a clean transparent PNG image of the clothing item.
    """
    nparr = np.frombuffer(dress_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return Image.open(BytesIO(dress_bytes)).convert("RGBA")

    h, w, _ = img.shape

    # Color thresholding & contour extraction to separate dress item from background
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Detect corner background colors
    corner_samples = np.vstack([
        img[0:15, 0:15].reshape(-1, 3),
        img[0:15, w-15:w].reshape(-1, 3),
        img[h-15:h, 0:15].reshape(-1, 3),
        img[h-15:h, w-15:w].reshape(-1, 3)
    ])
    bg_color = np.median(corner_samples, axis=0)

    # Distance map from background color
    diff = np.linalg.norm(img.astype(np.float32) - bg_color.astype(np.float32), axis=2)
    mask = np.where(diff > 35, 255, 0).astype(np.uint8)

    # Morphological clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Find main garment contour
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        clean_mask = np.zeros((h, w), np.uint8)
        cv2.drawContours(clean_mask, [main_contour], -1, 255, -1)
        mask = clean_mask

    # Edge feathering for natural alpha blending
    alpha_mask = cv2.GaussianBlur(mask, (7, 7), 0)

    b, g, r = cv2.split(img)
    rgba = cv2.merge((b, g, r, alpha_mask))
    
    # Crop tightly to garment bounding box
    coords = cv2.findNonZero(mask)
    if coords is not None:
        x, y, bw, bh = cv2.boundingRect(coords)
        rgba = rgba[y:y+bh, x:x+bw]

    # Convert to PIL Image
    rgba_rgb = cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA)
    return Image.fromarray(rgba_rgb)

def generate_pose_aligned_tryon(person_bytes: bytes, dress_bytes: bytes, landmarks_dict: dict) -> str:
    """
    Performs accurate pose-aligned garment warping onto torso:
    - Extracts transparent dress foreground
    - Aligns to MediaPipe shoulder slope & width
    - Protects head/neck area with collar curve mask
    - Performs smooth alpha blending onto person torso
    """
    person_pil = Image.open(BytesIO(person_bytes)).convert("RGBA")
    pw, ph = person_pil.size

    # Step 1: Extract background-free transparent garment
    try:
        dress_garment = extract_garment_foreground(dress_bytes)
    except Exception as e:
        print(f"[Try-On Engine] Garment extraction warning: {e}")
        dress_garment = Image.open(BytesIO(dress_bytes)).convert("RGBA")

    gw, gh = dress_garment.size

    # Step 2: Get MediaPipe landmarks
    nose = landmarks_dict.get(0, {"x": 0.50, "y": 0.15})
    l_sh = landmarks_dict.get(11, {"x": 0.35, "y": 0.28})
    r_sh = landmarks_dict.get(12, {"x": 0.65, "y": 0.28})
    l_hip = landmarks_dict.get(23, {"x": 0.40, "y": 0.58})
    r_hip = landmarks_dict.get(24, {"x": 0.60, "y": 0.58})

    # Pixel coordinates
    nose_x, nose_y = int(nose["x"] * pw), int(nose["y"] * ph)
    l_sh_x, l_sh_y = int(l_sh["x"] * pw), int(l_sh["y"] * ph)
    r_sh_x, r_sh_y = int(r_sh["x"] * pw), int(r_sh["y"] * ph)
    l_hip_x, l_hip_y = int(l_hip["x"] * pw), int(l_hip["y"] * ph)
    r_hip_x, r_hip_y = int(r_hip["x"] * pw), int(r_hip["y"] * ph)

    sh_mid_x = (l_sh_x + r_sh_x) // 2
    sh_mid_y = (l_sh_y + r_sh_y) // 2

    # Neck collar anchor: sitting right below chin/nose and at shoulder line
    neck_anchor_y = max(int(nose_y + (sh_mid_y - nose_y) * 0.6), int(ph * 0.20))

    # Shoulder width & inclination angle theta
    dx = r_sh_x - l_sh_x
    dy = r_sh_y - l_sh_y
    shoulder_w_px = max(int(math.sqrt(dx**2 + dy**2)), int(pw * 0.35))
    angle_deg = math.degrees(math.atan2(dy, dx)) if dx != 0 else 0

    hip_mid_y = (l_hip_y + r_hip_y) // 2
    torso_h_px = max(abs(hip_mid_y - sh_mid_y) * 1.4, int(ph * 0.45))

    # Scale garment to fit body proportions
    target_w = int(shoulder_w_px * 1.35)
    target_h = int(torso_h_px * 1.20)

    dress_resized = dress_garment.resize((target_w, target_h), Image.Resampling.LANCZOS)

    # Rotate garment if shoulders are tilted
    if abs(angle_deg) > 1.5:
        dress_resized = dress_resized.rotate(-angle_deg, resample=Image.Resampling.BICUBIC, expand=True)

    rw, rh = dress_resized.size

    # Position on person canvas
    paste_x = sh_mid_x - (rw // 2)
    paste_y = neck_anchor_y - int(rh * 0.05)

    # Step 3: Neck Line Mask Protection (Clips top edge to keep chin & neck exposed)
    mask = dress_resized.split()[3]  # Alpha channel
    mask_np = np.array(mask)

    # Cut out top neck curve area so chin/head is never obscured
    cutoff_y = int(rh * 0.08)
    mask_np[0:cutoff_y, :] = 0
    mask_cleaned = Image.fromarray(mask_np)

    # Step 4: Seamless Composite onto Person Image
    canvas = person_pil.copy()
    canvas.paste(dress_resized, (paste_x, paste_y), mask_cleaned)

    # Convert to RGB & Base64 Data URL
    result_rgb = canvas.convert("RGB")
    buffer = BytesIO()
    result_rgb.save(buffer, format="JPEG", quality=93)
    result_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/jpeg;base64,{result_b64}"
