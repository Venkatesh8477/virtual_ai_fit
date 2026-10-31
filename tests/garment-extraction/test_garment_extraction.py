import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
from routes.tryon import extract_garment_foreground, extract_garment_mask


GARMENT_INPUTS = Path(__file__).parent / "inputs"


class GarmentExtractionTests(unittest.TestCase):
    def test_extracts_all_supplied_garment_examples(self):
        image_paths = sorted(GARMENT_INPUTS.glob("*"))
        image_paths = [
            path for path in image_paths
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        ]
        if not image_paths:
            self.skipTest("Add garment examples to tests/garment-extraction/inputs.")

        for path in image_paths:
            with self.subTest(image=path.name):
                extracted = extract_garment_foreground(path.read_bytes())
                rgba = np.asarray(extracted.convert("RGBA"))
                alpha = rgba[:, :, 3]

                self.assertEqual(rgba.shape[2], 4)
                self.assertGreater(rgba.shape[0], 0)
                self.assertGreater(rgba.shape[1], 0)
                self.assertTrue(np.any(alpha == 0))
                self.assertTrue(np.any(alpha >= 250))

    def test_preserves_rgb_channels_and_rejects_invalid_input(self):
        image = np.full((80, 100, 3), 255, dtype=np.uint8)
        image[15:70, 25:75] = (0, 0, 200)
        encoded, image_bytes = cv2.imencode(".jpg", image)
        self.assertTrue(encoded)

        extracted = np.asarray(
            extract_garment_foreground(image_bytes.tobytes()).convert("RGBA")
        )
        mask = extract_garment_mask(image_bytes.tobytes())
        center = extracted[extracted.shape[0] // 2, extracted.shape[1] // 2]
        self.assertGreater(int(center[0]), int(center[1]) * 2)
        self.assertGreater(int(center[3]), 0)
        self.assertEqual(mask.shape, image.shape[:2])
        self.assertTrue(set(np.unique(mask)).issubset({0, 255}))

        with self.assertRaisesRegex(ValueError, "Failed to decode"):
            extract_garment_foreground(b"not an image")


if __name__ == "__main__":
    unittest.main()
