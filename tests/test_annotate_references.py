import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from tools import annotate_references


class AnnotationSetupTests(unittest.TestCase):
    def test_pose_labels_match_existing_images_and_have_eight_people(self):
        labels = annotate_references.read_pose_labels()

        self.assertEqual(len(labels), 10)
        self.assertEqual(sum(labels.values()), 8)

    def test_empty_scene_mask_matches_input_and_is_binary(self):
        image_path = (
            annotate_references.POSE_IMAGES / "pose_test_1_front_facing.jpg"
        )
        image = cv2.imread(str(image_path))
        with tempfile.TemporaryDirectory(dir=annotate_references.ROOT) as temp_dir:
            output_dir = Path(temp_dir)
            with patch.object(annotate_references, "PERSON_MASKS", output_dir):
                annotate_references.save_empty_person_mask(image_path)
                saved = cv2.imread(
                    str(output_dir / f"{image_path.stem}.png"),
                    cv2.IMREAD_GRAYSCALE,
                )

        self.assertEqual(saved.shape, image.shape[:2])
        self.assertFalse(np.any(saved))
        self.assertEqual(set(np.unique(saved)), {0})

    def test_invalid_existing_empty_mask_is_not_overwritten(self):
        image_path = (
            annotate_references.POSE_IMAGES / "pose_test_1_front_facing.jpg"
        )
        image = cv2.imread(str(image_path))
        with tempfile.TemporaryDirectory(dir=annotate_references.ROOT) as temp_dir:
            output_dir = Path(temp_dir)
            output_dir.mkdir(exist_ok=True)
            existing_path = output_dir / f"{image_path.stem}.png"
            cv2.imwrite(
                str(existing_path),
                np.full(image.shape[:2], 255, dtype=np.uint8),
            )
            with patch.object(annotate_references, "PERSON_MASKS", output_dir):
                with self.assertRaisesRegex(ValueError, "Existing no-person"):
                    annotate_references.save_empty_person_mask(image_path)
            existing = cv2.imread(str(existing_path), cv2.IMREAD_GRAYSCALE)

        self.assertTrue(np.all(existing == 255))


if __name__ == "__main__":
    unittest.main()
