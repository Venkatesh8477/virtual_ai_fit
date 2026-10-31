import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from mediapipe_engine import pose_detector


def blank_image_bytes():
    encoded, image = cv2.imencode(".jpg", np.zeros((80, 60, 3), dtype=np.uint8))
    if not encoded:
        raise RuntimeError("Could not create test image.")
    return image.tobytes()


class NoPose:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def process(self, image):
        return SimpleNamespace(pose_landmarks=None)


class DetectedPose(NoPose):
    def process(self, image):
        landmarks = [
            SimpleNamespace(x=0.5, y=0.5, z=0.0, visibility=0.9)
            for _ in range(33)
        ]
        landmarks[11].visibility = 0.2
        landmarks[12].x = 1.1
        return SimpleNamespace(pose_landmarks=SimpleNamespace(landmark=landmarks))


class PoseDetectorTests(unittest.TestCase):
    def test_no_pose_returns_empty_landmarks_without_synthetic_success(self):
        with patch.object(pose_detector.mp_pose, "Pose", return_value=NoPose()):
            result = pose_detector.analyze_body_pose(blank_image_bytes())

        self.assertEqual(result["detection_status"], "not_detected")
        self.assertEqual(result["landmarks"], [])
        self.assertEqual(result["landmarks_dict"], {})
        self.assertIsNone(result["metrics"])
        self.assertIn("No human pose", result["detection_reason"])

    def test_detected_landmarks_include_visibility_and_frame_quality(self):
        with (
            patch.object(pose_detector.mp_pose, "Pose", return_value=DetectedPose()),
            patch.object(pose_detector.drawing_utils, "draw_landmarks"),
            patch.object(
                pose_detector.drawing_styles,
                "get_default_pose_landmarks_style",
                return_value=None
            ),
        ):
            result = pose_detector.analyze_body_pose(blank_image_bytes())

        self.assertEqual(result["detection_status"], "detected")
        self.assertFalse(result["landmarks_dict"][11]["usable_for_measurement"])
        self.assertFalse(result["landmarks_dict"][12]["in_frame"])
        self.assertEqual(result["visibility_threshold"], 0.5)

    def test_invalid_image_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Invalid image"):
            pose_detector.analyze_body_pose(b"not an image")

    def test_unavailable_model_is_reported(self):
        with (
            patch.object(pose_detector, "HAS_MEDIAPIPE", False),
            patch.object(pose_detector, "MEDIAPIPE_IMPORT_ERROR", "test failure"),
        ):
            with self.assertRaisesRegex(pose_detector.PoseDetectorUnavailableError, "test failure"):
                pose_detector.analyze_body_pose(blank_image_bytes())

    def test_metrics_use_only_usable_landmarks_and_image_pixels(self):
        coords = {
            11: (0.30, 0.20), 12: (0.70, 0.20),
            13: (0.25, 0.35), 14: (0.75, 0.35),
            15: (0.20, 0.50), 16: (0.80, 0.50),
            23: (0.35, 0.50), 24: (0.65, 0.50),
            25: (0.38, 0.70), 26: (0.62, 0.70),
            27: (0.40, 0.90), 28: (0.60, 0.90)
        }
        landmarks = {
            idx: {"x": x, "y": y, "visibility": 0.9}
            for idx, (x, y) in coords.items()
        }

        metrics = pose_detector.calculate_body_metrics(landmarks, 100, 100)
        self.assertEqual(metrics["shoulder_width_px"], 40.0)
        self.assertEqual(metrics["measurement_units"], "pixels")
        self.assertNotIn("shoulder_width_cm", metrics)

        landmarks[11]["visibility"] = 0.2
        metrics = pose_detector.calculate_body_metrics(landmarks, 100, 100)
        self.assertIsNone(metrics["shoulder_width_px"])
        self.assertIsNone(metrics["waist_width_px"])

    def test_out_of_frame_landmark_is_not_usable(self):
        self.assertFalse(pose_detector.landmark_is_usable({
            "x": 1.01, "y": 0.5, "visibility": 0.99
        }))


if __name__ == "__main__":
    unittest.main()
