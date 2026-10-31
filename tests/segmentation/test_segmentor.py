import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import base64

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from mediapipe_engine import segmentor


def encoded_test_image():
    image = np.zeros((40, 60, 3), dtype=np.uint8)
    encoded, data = cv2.imencode(".jpg", image)
    if not encoded:
        raise RuntimeError("Could not create test image.")
    return data.tobytes()


class FixedMaskModel:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def process(self, image):
        height, width = image.shape[:2]
        mask = np.zeros((height, width), dtype=np.float32)
        mask[10:30, 15:35] = 0.8
        return SimpleNamespace(segmentation_mask=mask)


class InvalidMaskModel(FixedMaskModel):
    def process(self, image):
        height, width = image.shape[:2]
        return SimpleNamespace(
            segmentation_mask=np.full((height, width), 1.5, dtype=np.float32)
        )


class SegmentorTests(unittest.TestCase):
    def test_returns_rgba_image_and_grayscale_mask_at_input_size(self):
        fake_model_api = SimpleNamespace(
            SelfieSegmentation=lambda model_selection: FixedMaskModel()
        )
        with (
            patch.object(segmentor, "HAS_MEDIAPIPE_SEGMENTATION", True),
            patch.object(segmentor, "selfie_segmentation", fake_model_api),
        ):
            result = segmentor.segment_person_background(encoded_test_image())

        segmented = cv2.imdecode(
            np.frombuffer(result["segmented_bytes"], np.uint8), cv2.IMREAD_UNCHANGED
        )
        mask = cv2.imdecode(
            np.frombuffer(base64.b64decode(result["mask_data_url"].split(",", 1)[1]), np.uint8),
            cv2.IMREAD_GRAYSCALE
        )
        self.assertEqual(segmented.shape, (40, 60, 4))
        self.assertEqual(mask.shape, (40, 60))
        self.assertEqual(result["segmentation_method"], "mediapipe_selfie_segmentation")
        self.assertIsNone(result["segmentation_warning"])
        self.assertGreater(mask[20, 25], mask[0, 0])

    def test_unavailable_model_fallback_is_reported(self):
        fallback_image = np.zeros((40, 60, 4), dtype=np.uint8)
        with (
            patch.object(segmentor, "HAS_MEDIAPIPE_SEGMENTATION", False),
            patch.object(segmentor, "MEDIAPIPE_SEGMENTATION_IMPORT_ERROR", "test unavailable"),
            patch.object(
                segmentor,
                "generate_fallback_segmentation",
                return_value=(fallback_image, "opencv_grabcut_fallback")
            ),
        ):
            result = segmentor.segment_person_background(encoded_test_image())

        self.assertEqual(result["segmentation_method"], "opencv_grabcut_fallback")
        self.assertEqual(result["segmentation_warning"], "test unavailable")

    def test_invalid_probability_mask_uses_reported_fallback(self):
        fake_model_api = SimpleNamespace(
            SelfieSegmentation=lambda model_selection: InvalidMaskModel()
        )
        fallback_image = np.zeros((40, 60, 4), dtype=np.uint8)
        with (
            patch.object(segmentor, "HAS_MEDIAPIPE_SEGMENTATION", True),
            patch.object(segmentor, "selfie_segmentation", fake_model_api),
            patch.object(
                segmentor,
                "generate_fallback_segmentation",
                return_value=(fallback_image, "opencv_grabcut_fallback")
            ),
        ):
            result = segmentor.segment_person_background(encoded_test_image())

        self.assertEqual(result["segmentation_method"], "opencv_grabcut_fallback")
        self.assertIn("[0, 1]", result["segmentation_warning"])

    def test_invalid_image_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Failed to decode"):
            segmentor.segment_person_background(b"not an image")


if __name__ == "__main__":
    unittest.main()
