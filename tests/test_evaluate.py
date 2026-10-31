import base64
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from backend.tests import evaluate
from backend.tests.evaluate import mask_scores


class MaskScoreTests(unittest.TestCase):
    def test_iou_and_dice_for_partial_overlap(self):
        prediction = np.array([[255, 255], [0, 0]], dtype=np.uint8)
        reference = np.array([[255, 0], [255, 0]], dtype=np.uint8)

        iou, dice = mask_scores(prediction, reference)

        self.assertAlmostEqual(iou, 1 / 3)
        self.assertAlmostEqual(dice, 0.5)

    def test_empty_masks_score_as_perfect_match(self):
        empty = np.zeros((2, 2), dtype=np.uint8)

        self.assertEqual(mask_scores(empty, empty), (1.0, 1.0))
        self.assertEqual(evaluate.mask_metrics(empty, empty)["precision"], 1.0)
        self.assertEqual(evaluate.mask_metrics(empty, empty)["recall"], 1.0)

    def test_mask_metrics_include_precision_recall_and_false_foreground(self):
        prediction = np.array([[255, 255], [0, 0]], dtype=np.uint8)
        reference = np.array([[255, 0], [255, 0]], dtype=np.uint8)

        metrics = evaluate.mask_metrics(prediction, reference)

        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 0.5)
        self.assertEqual(metrics["false_positive_pixels"], 1)
        self.assertEqual(metrics["false_positive_fraction"], 0.25)

    def test_non_binary_reference_masks_are_rejected(self):
        prediction = np.zeros((2, 2), dtype=np.uint8)
        reference = np.array([[0, 128], [0, 255]], dtype=np.uint8)

        with self.assertRaisesRegex(ValueError, "only 0 and 255"):
            evaluate.mask_metrics(prediction, reference)

    def test_empty_scene_reference_must_be_all_black(self):
        image_path = evaluate.POSE_IMAGES / "pose_test_1_front_facing.jpg"
        image = cv2.imdecode(
            np.frombuffer(image_path.read_bytes(), np.uint8), cv2.IMREAD_COLOR
        )
        with tempfile.TemporaryDirectory(dir=evaluate.TEST_ROOT) as temp_dir:
            reference_dir = Path(temp_dir)
            cv2.imwrite(
                str(reference_dir / f"{image_path.stem}.png"),
                np.full(image.shape[:2], 255, dtype=np.uint8),
            )
            row = {}

            evaluate.add_mask_metrics(
                row,
                np.zeros(image.shape[:2], dtype=np.uint8),
                image_path,
                reference_dir,
                expected_empty=True,
            )

        self.assertIn("entirely black", row["reference_mask_error"])
        self.assertIsNone(row["iou"])

    def test_different_dimensions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "dimensions differ"):
            mask_scores(np.zeros((2, 2)), np.zeros((3, 3)))

    def test_results_are_appended_for_run_comparison(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            results_root = Path(temp_dir)
            with patch.object(evaluate, "RESULTS_ROOT", results_root):
                first_path = evaluate.save_results([{
                    "run_id": "run-1",
                    "component": "pose_detection",
                    "image": "person.jpg",
                    "processing_success": True,
                }])
                second_path = evaluate.save_results([{
                    "run_id": "run-2",
                    "component": "pose_detection",
                    "image": "person.jpg",
                    "processing_success": True,
                }])

            if second_path is None:
                self.fail("Expected evaluation CSV to be saved.")
            self.assertEqual(first_path, second_path)
            with second_path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))
            self.assertEqual([row["run_id"] for row in rows], ["run-1", "run-2"])


class PoseLabelTests(unittest.TestCase):
    def test_visual_manifest_overrides_misleading_filename(self):
        labels = evaluate.load_pose_labels()

        self.assertTrue(labels["pose_test_1_no_person.jpg"]["has_person"])
        self.assertFalse(labels["pose_test_1_front_facing.jpg"]["has_person"])
        evaluate.validate_pose_labels(
            evaluate.discover_images(evaluate.POSE_IMAGES), labels
        )

    def test_evaluation_uses_manifest_person_status(self):
        image_path = evaluate.POSE_IMAGES / "pose_test_1_no_person.jpg"
        labels = evaluate.load_pose_labels()
        detected_pose = {
            "detection_status": "detected",
            "landmarks_dict": {},
        }
        with patch.object(evaluate, "analyze_body_pose", return_value=detected_pose):
            row = evaluate.evaluate_pose(image_path, labels)

        self.assertFalse(row["expected_no_person"])
        self.assertFalse(row["no_person_correctly_rejected"])
        self.assertEqual(row["test_category"], "front_facing")

    def test_pose_rows_record_label_mismatch_and_landmark_details(self):
        image_path = evaluate.POSE_IMAGES / "pose_test_1_front_facing.jpg"
        labels = evaluate.load_pose_labels()
        landmarks = {
            landmark_id: {
                "x": 0.25,
                "y": 0.5,
                "visibility": 0.9,
                "in_frame": True,
            }
            for landmark_id in evaluate.REQUIRED_LANDMARKS
        }
        detected_pose = {
            "detection_status": "detected",
            "landmarks_dict": landmarks,
        }
        with patch.object(evaluate, "analyze_body_pose", return_value=detected_pose):
            row = evaluate.evaluate_pose(image_path, labels)

        checks = json.loads(row["required_landmarks"])
        self.assertFalse(row["detection_matches_person_label"])
        self.assertIn("no-person", row["failure_reason"])
        self.assertEqual(checks["0"]["visibility"], 0.9)
        self.assertTrue(checks["0"]["in_frame"])

    def test_manifest_must_cover_exactly_the_test_images(self):
        with self.assertRaisesRegex(ValueError, "manifest mismatch"):
            evaluate.validate_pose_labels([Path("new_image.jpg")], {})

    def test_keypoint_pck_counts_missing_predictions_as_misses(self):
        references = {
            "nose": (50, 10),
            "left_shoulder": (40, 30),
            "right_shoulder": (60, 30),
            "left_hip": (42, 70),
            "right_hip": (58, 70),
        }
        predictions = {
            landmark_id: {
                "x": x / 100,
                "y": y / 100,
                "visibility": 1.0,
            }
            for landmark_id, (x, y) in zip(
                evaluate.KEYPOINT_IDS.values(), references.values()
            )
        }
        predictions.pop(evaluate.KEYPOINT_IDS["nose"])

        metrics = evaluate.keypoint_accuracy(predictions, references, 100, 100)

        self.assertEqual(metrics["correct"], 4)
        self.assertEqual(metrics["visible"], 5)
        self.assertEqual(metrics["missing_predictions"], 1)
        self.assertEqual(metrics["pck_0_2"], 0.8)


class SegmentationLabelTests(unittest.TestCase):
    def test_empty_scene_false_foreground_is_reported_without_reference_mask(self):
        image_path = evaluate.POSE_IMAGES / "pose_test_1_front_facing.jpg"
        labels = evaluate.load_pose_labels()
        source = cv2.imdecode(
            np.frombuffer(image_path.read_bytes(), np.uint8), cv2.IMREAD_COLOR
        )
        height, width = source.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[0, :2] = 255
        cutout = cv2.cvtColor(source, cv2.COLOR_BGR2RGBA)
        _, mask_bytes = cv2.imencode(".png", mask)
        _, cutout_bytes = cv2.imencode(".png", cutout)
        fake_result = {
            "mask_data_url": "data:image/png;base64,"
            + base64.b64encode(mask_bytes).decode(),
            "segmented_data_url": "data:image/png;base64,"
            + base64.b64encode(cutout_bytes).decode(),
            "segmentation_method": "test",
        }

        with tempfile.TemporaryDirectory(dir=evaluate.TEST_ROOT) as temp_dir, \
                patch.object(evaluate, "RESULTS_ROOT", Path(temp_dir)), \
                patch.object(evaluate, "segment_person_background", return_value=fake_result):
            row = evaluate.evaluate_segmentation(image_path, labels)

        self.assertTrue(row["processing_success"], row["failure_reason"])
        self.assertTrue(row["expected_no_person"])
        self.assertEqual(row["false_foreground_pixels"], 2)
        self.assertAlmostEqual(
            row["false_foreground_fraction"], 2 / (width * height), places=6
        )


if __name__ == "__main__":
    unittest.main()
