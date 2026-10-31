import base64
import math

import cv2
import numpy as np

MIN_LANDMARK_VISIBILITY = 0.5

mp_pose = None
drawing_utils = None
drawing_styles = None
try:
    from mediapipe.python.solutions import drawing_styles, drawing_utils, pose as mp_pose

    HAS_MEDIAPIPE = True
    MEDIAPIPE_IMPORT_ERROR = None
except Exception as err:
    MEDIAPIPE_IMPORT_ERROR = str(err)
    HAS_MEDIAPIPE = False
    print(f"[MediaPipe Engine] MediaPipe Pose unavailable: {err}")


class PoseDetectorUnavailableError(RuntimeError):
    pass


# Key MediaPipe landmark indices used by the app.
LANDMARK_NAMES = {
    0: "Nose / Head",
    11: "Left Shoulder",
    12: "Right Shoulder",
    13: "Left Elbow",
    14: "Right Elbow",
    15: "Left Wrist",
    16: "Right Wrist",
    23: "Left Hip",
    24: "Right Hip",
    25: "Left Knee",
    26: "Right Knee",
    27: "Left Ankle",
    28: "Right Ankle"
}


def euclidean_distance(p1, p2, width, height):
    """Calculates pixel distance between two landmark points."""
    x1, y1 = p1["x"] * width, p1["y"] * height
    x2, y2 = p2["x"] * width, p2["y"] * height
    return math.hypot(x2 - x1, y2 - y1)


def landmark_is_usable(landmark: dict | None) -> bool:
    """Whether a landmark is visible enough and lies inside the source image."""
    if landmark is None:
        return False
    try:
        x = float(landmark["x"])
        y = float(landmark["y"])
        visibility = float(landmark["visibility"])
    except (KeyError, TypeError, ValueError):
        return False
    return (
        math.isfinite(x)
        and math.isfinite(y)
        and math.isfinite(visibility)
        and visibility >= MIN_LANDMARK_VISIBILITY
        and 0 <= x <= 1
        and 0 <= y <= 1
    )


def analyze_body_pose(image_bytes: bytes):
    """
    Analyzes a person photo with MediaPipe Pose.
    Returns detected landmarks, per-point usability, image-space metrics, and visualization.
    """
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image file provided.")

    if (
        not HAS_MEDIAPIPE
        or mp_pose is None
        or drawing_utils is None
        or drawing_styles is None
    ):
        raise PoseDetectorUnavailableError(
            f"MediaPipe Pose is unavailable: {MEDIAPIPE_IMPORT_ERROR or 'import failed'}"
        )
    pose_api = mp_pose
    drawing = drawing_utils
    styles = drawing_styles

    height, width, _ = img.shape
    landmarks_dict = {}
    landmarks_list = []
    annotated_img = img.copy()

    try:
        with pose_api.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=True,
            min_detection_confidence=0.5
        ) as pose:
            results = pose.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    except Exception as err:
        raise PoseDetectorUnavailableError(f"MediaPipe Pose inference failed: {err}") from err

    pose_landmarks = getattr(results, "pose_landmarks", None)
    if pose_landmarks is not None and pose_landmarks.landmark:
        drawing.draw_landmarks(
            annotated_img,
            pose_landmarks,
            list(pose_api.POSE_CONNECTIONS),
            landmark_drawing_spec=styles.get_default_pose_landmarks_style()
        )

        for idx, lm in enumerate(pose_landmarks.landmark):
            x, y, z, visibility = map(float, (lm.x, lm.y, lm.z, lm.visibility))
            finite_x = math.isfinite(x)
            finite_y = math.isfinite(y)
            finite_z = math.isfinite(z)
            finite_visibility = math.isfinite(visibility)
            in_frame = finite_x and finite_y and 0 <= x <= 1 and 0 <= y <= 1
            point_data = {
                "id": idx,
                "name": LANDMARK_NAMES.get(idx, f"Landmark {idx}"),
                "x": round(x, 4) if finite_x else None,
                "y": round(y, 4) if finite_y else None,
                "z": round(z, 4) if finite_z else None,
                "visibility": round(visibility, 4) if finite_visibility else None,
                "in_frame": in_frame,
                "usable_for_measurement": landmark_is_usable({
                    "x": x,
                    "y": y,
                    "visibility": visibility
                }),
                "px_x": int(x * width) if finite_x else None,
                "px_y": int(y * height) if finite_y else None
            }
            landmarks_dict[idx] = point_data
            if idx in LANDMARK_NAMES:
                landmarks_list.append(point_data)

    pose_detected = bool(landmarks_dict)
    metrics = calculate_body_metrics(landmarks_dict, width, height) if pose_detected else None

    encoded, buffer = cv2.imencode(".jpg", annotated_img)
    if not encoded:
        raise RuntimeError("Could not encode pose visualization.")
    annotated_b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")

    return {
        "detection_status": "detected" if pose_detected else "not_detected",
        "detection_reason": None if pose_detected else "No human pose detected in the image.",
        "pose_source": "mediapipe",
        "visibility_threshold": MIN_LANDMARK_VISIBILITY,
        "landmarks": landmarks_list,
        "landmarks_dict": landmarks_dict,
        "metrics": metrics,
        "landmark_visualization": f"data:image/jpeg;base64,{annotated_b64}",
        "image_width": width,
        "image_height": height
    }


def calculate_body_metrics(landmarks_dict: dict, width: int, height: int) -> dict:
    """Calculate image-space distances only when their source landmarks are usable."""
    def point(landmark_id):
        candidate = landmarks_dict.get(landmark_id)
        return candidate if landmark_is_usable(candidate) else None

    def distance(first_id, second_id):
        first, second = point(first_id), point(second_id)
        if first is None or second is None:
            return None
        return round(euclidean_distance(first, second, width, height), 1)

    def path_length(*landmark_ids):
        points = [point(landmark_id) for landmark_id in landmark_ids]
        if any(candidate is None for candidate in points):
            return None
        return round(sum(
            euclidean_distance(first, second, width, height)
            for first, second in zip(points, points[1:])
        ), 1)

    shoulder_width_px = distance(11, 12)
    hip_width_px = distance(23, 24)
    shoulder_left, shoulder_right = point(11), point(12)
    hip_left, hip_right = point(23), point(24)

    waist_width_px = None
    torso_length_px = None
    if (
        shoulder_left is not None
        and shoulder_right is not None
        and hip_left is not None
        and hip_right is not None
    ):
        waist_left = {
            "x": shoulder_left["x"] * 0.4 + hip_left["x"] * 0.6,
            "y": shoulder_left["y"] * 0.4 + hip_left["y"] * 0.6
        }
        waist_right = {
            "x": shoulder_right["x"] * 0.4 + hip_right["x"] * 0.6,
            "y": shoulder_right["y"] * 0.4 + hip_right["y"] * 0.6
        }
        waist_width_px = round(euclidean_distance(waist_left, waist_right, width, height), 1)

        shoulder_center = {
            "x": (shoulder_left["x"] + shoulder_right["x"]) / 2,
            "y": (shoulder_left["y"] + shoulder_right["y"]) / 2
        }
        hip_center = {
            "x": (hip_left["x"] + hip_right["x"]) / 2,
            "y": (hip_left["y"] + hip_right["y"]) / 2
        }
        torso_length_px = round(euclidean_distance(shoulder_center, hip_center, width, height), 1)

    left_arm = path_length(11, 13, 15)
    right_arm = path_length(12, 14, 16)
    arm_length_px = (
        round((left_arm + right_arm) / 2, 1)
        if left_arm is not None and right_arm is not None
        else None
    )

    left_leg = path_length(23, 25, 27)
    right_leg = path_length(24, 26, 28)
    leg_length_px = (
        round((left_leg + right_leg) / 2, 1)
        if left_leg is not None and right_leg is not None
        else None
    )
    body_ratio = (
        round(torso_length_px / leg_length_px, 2)
        if torso_length_px is not None and leg_length_px
        else None
    )

    body_type_shape = None
    if shoulder_width_px and hip_width_px and waist_width_px is not None:
        similar_widths = (
            abs(shoulder_width_px - hip_width_px)
            <= max(shoulder_width_px, hip_width_px) * 0.15
        )
        if similar_widths and waist_width_px < shoulder_width_px * 0.85:
            body_type_shape = "Hourglass"
        elif shoulder_width_px > hip_width_px * 1.1:
            body_type_shape = "Inverted Triangle"
        else:
            body_type_shape = "Rectangle"

    return {
        "measurement_units": "pixels",
        "measurement_note": "Distances are image-space estimates, not calibrated body measurements.",
        "shoulder_width_px": shoulder_width_px,
        "waist_width_px": waist_width_px,
        "hip_width_px": hip_width_px,
        "arm_length_px": arm_length_px,
        "leg_length_px": leg_length_px,
        "torso_length_px": torso_length_px,
        "body_ratio": body_ratio,
        "body_type_shape": body_type_shape
    }
